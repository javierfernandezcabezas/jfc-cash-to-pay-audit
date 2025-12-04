"""
Cloud Run Service: jfc-cash-to-pay-audit
Ejecuta queries de BigQuery y exporta resultados a Google Sheets
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from flask import Request
from google.cloud import bigquery
from google.auth import default

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de BigQuery
PROJECT_ID = os.environ.get('PROJECT_ID', 'workflows-and-automations-1')
DATASET_ID = 'amn_op_automatic_invoicing'

# Configuración de Google Sheets
GOOGLE_SHEETS_ID = os.environ.get('GOOGLE_SHEETS_ID', '14zyGkUGjj3HP4klvwmUKHukHc_1eN6FRLAazcwoNQZ8')

# Tablas
HIST = f'{PROJECT_ID}.{DATASET_ID}.historic_order_item_sales'
T_CC = f'{PROJECT_ID}.{DATASET_ID}.Commercial_Condition__c'
T_CONTRACT = f'{PROJECT_ID}.{DATASET_ID}.Contract'
T_TAXES = f'{PROJECT_ID}.{DATASET_ID}.historic_taxes_applied'
T_FEES = f'{PROJECT_ID}.{DATASET_ID}.historic_fixed_fees'
T_ACCOUNT = f'{PROJECT_ID}.{DATASET_ID}.Account'

# Inicializar cliente de BigQuery
def get_bigquery_client():
    """
    Obtiene cliente de BigQuery usando Application Default Credentials.
    Esto usará la cuenta de servicio del servicio Cloud Run si está configurada,
    o las credenciales del entorno si están disponibles.
    """
    try:
        # Intentar usar Application Default Credentials
        client = bigquery.Client(project=PROJECT_ID)
        return client
    except Exception as e:
        logger.error(f"Error inicializando cliente BigQuery: {e}")
        # Fallback: crear cliente sin especificar proyecto
        return bigquery.Client()


def execute_query(query: str, params: Optional[Dict] = None) -> list:
    """Ejecuta una query en BigQuery y retorna los resultados"""
    client = get_bigquery_client()
    
    job_config = bigquery.QueryJobConfig()
    if params:
        job_config.query_parameters = [
            bigquery.ScalarQueryParameter(key, value_type, value)
            for key, (value, value_type) in params.items()
        ]
    
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()
    
    return [dict(row) for row in results]


def get_partner_id_by_contract(cd_contract: str) -> Optional[str]:
    """Obtiene partner_id según cd_contract"""
    query = f"""
        SELECT id_partner
        FROM `{HIST}`
        WHERE cd_contract = @cd_contract
        ORDER BY DT_INVOICE_TO DESC
        LIMIT 1
    """
    params = {'cd_contract': (cd_contract, 'STRING')}
    results = execute_query(query, params)
    return results[0]['id_partner'] if results else None


def get_contract_by_partner(id_partner: int) -> Optional[str]:
    """Obtiene cd_contract según partner_id"""
    query = f"""
        SELECT cd_contract
        FROM `{HIST}`
        WHERE CAST(REPLACE(id_partner, ',', '') AS INT64) = @id_partner
          AND cd_contract IS NOT NULL
        ORDER BY DT_INVOICE_TO DESC
        LIMIT 1
    """
    params = {'id_partner': (id_partner, 'INT64')}
    results = execute_query(query, params)
    return results[0]['cd_contract'] if results else None


def get_contracts_by_partner(id_partner: int) -> list:
    """Obtiene distintos cd_contracts bajo un mismo partner_id"""
    query = f"""
        SELECT DISTINCT cd_contract
        FROM `{HIST}`
        WHERE CAST(REPLACE(id_partner, ',', '') AS INT64) = @id_partner
          AND cd_contract IS NOT NULL
        ORDER BY cd_contract
        LIMIT 5000
    """
    params = {'id_partner': (id_partner, 'INT64')}
    return execute_query(query, params)


def get_account_name(id_partner: int) -> Optional[str]:
    """Obtiene account name según partner_id"""
    query = f"""
        SELECT Name
        FROM `{T_ACCOUNT}`
        WHERE CAST(Partner_ID__c AS INT64) = @id_partner_num
        LIMIT 1
    """
    params = {'id_partner_num': (id_partner, 'INT64')}
    results = execute_query(query, params)
    return results[0]['Name'] if results else None


def get_invoice_summary(where_clause: str = '') -> list:
    """Query RESUMEN INVOICES - Completa con CTEs"""
    query = f"""
    WITH base AS (
      SELECT * FROM `{HIST}`{where_clause}
    ),
    sessions AS (SELECT DISTINCT session_id FROM base),
    taxes_tab AS (
      SELECT session_id, ds_tax_apply_to, SUM(nm_tax_rate)/100 AS tax
      FROM `{T_TAXES}`
      WHERE session_id IN (SELECT session_id FROM sessions)
      GROUP BY session_id, ds_tax_apply_to
    ),
    fixed_fees_tab_1 AS (
      SELECT
        f.session_id, 
        f.cd_contract, 
        f.ds_fixed_description, 
        f.fixed_fee_invoice,
        COALESCE(ts.tax, td.tax, 0) AS tax_rate_to_apply,
        CASE
          WHEN CAST(f.apply_tax AS STRING) = 'No' OR f.apply_tax = FALSE THEN 0
          ELSE f.fixed_fee_invoice * COALESCE(ts.tax, td.tax, 0)
        END AS fixed_fee_invoice_tax,
        CASE 
          WHEN ts.tax IS NOT NULL THEN 'specific'
          WHEN td.tax IS NOT NULL THEN 'default' 
          ELSE 'none' 
        END AS tax_source
      FROM `{T_FEES}` AS f
      JOIN sessions s USING (session_id)
      LEFT JOIN taxes_tab AS ts
        ON ts.session_id = f.session_id AND ts.ds_tax_apply_to = f.ds_fixed_description
      LEFT JOIN taxes_tab AS td
        ON td.session_id = f.session_id AND td.ds_tax_apply_to = 'default'
    ),
    fixed_fees_tab AS (
      SELECT session_id,
             SUM(fixed_fee_invoice) AS fixed_fee_invoice,
             SUM(fixed_fee_invoice_tax) AS fixed_fee_invoice_tax
      FROM fixed_fees_tab_1
      GROUP BY 1
    ),
    commission_tab AS (
      SELECT
        h.session_id, CAST(h.invoice_id AS STRING) AS invoice_id,
        h.dt_invoice_from, h.dt_invoice_to, h.dt_input, h.invoice_link,
        SUM(CASE WHEN h.item_status = 'validated/expired' THEN h.variable_cc_for_fever
                 WHEN h.item_status = 'canceled'           THEN h.AMOUNT_TO_COLLECT_FEVER ELSE 0 END) AS commission,
        SUM(CASE WHEN h.item_status = 'validated/expired' THEN h.variable_cc_for_fever * COALESCE(ts.tax, td.tax, 0)
                 WHEN h.item_status = 'canceled'           THEN h.AMOUNT_TO_COLLECT_FEVER * COALESCE(ts.tax, td.tax, 0)
                 ELSE 0 END) AS tax_commission
      FROM base h
      LEFT JOIN taxes_tab AS ts
        ON ts.session_id = h.session_id AND ts.ds_tax_apply_to = CAST(h.id_plan AS STRING)
      LEFT JOIN taxes_tab AS td
        ON td.session_id = h.session_id AND td.ds_tax_apply_to = 'default'
      WHERE h.item_status IN ('validated/expired','canceled')
      GROUP BY 1,2,3,4,5,6
    ),
    fin AS (
      SELECT
        dt_input, invoice_id, dt_invoice_from, dt_invoice_to, invoice_link,
        commission,
        COALESCE(ff.fixed_fee_invoice, 0) AS fixed_fees,
        commission + COALESCE(ff.fixed_fee_invoice, 0) AS total_fever_share,
        tax_commission + COALESCE(ff.fixed_fee_invoice_tax, 0) AS taxes
      FROM commission_tab c
      LEFT JOIN fixed_fees_tab ff USING (session_id)
    )
    SELECT
      'TOTAL' AS invoice_id,
      NULL AS dt_input, NULL AS dt_invoice_from, NULL AS dt_invoice_to, NULL AS invoice_link,
      SUM(commission) AS commission, SUM(fixed_fees) AS fixed_fees,
      SUM(total_fever_share) AS total_fever_share, SUM(taxes) AS taxes
    FROM fin
    UNION ALL
    SELECT invoice_id, dt_input, dt_invoice_from, dt_invoice_to, invoice_link,
           commission, fixed_fees, total_fever_share, taxes
    FROM fin
    ORDER BY dt_input DESC NULLS FIRST
    """
    return execute_query(query)


def get_partner_summary(where_clause: str = '') -> list:
    """
    Query RESUMEN POR PARTNER - Una línea por partner_id con métricas acumuladas
    """
    query = f"""
    WITH base AS (
      SELECT * FROM `{HIST}`{where_clause}
    ),
    sessions AS (
      SELECT DISTINCT session_id, id_partner
      FROM base
    ),
    taxes_tab AS (
      SELECT
        session_id,
        ds_tax_apply_to,
        SUM(nm_tax_rate) / 100 AS tax
      FROM `{T_TAXES}`
      WHERE session_id IN (SELECT session_id FROM sessions)
      GROUP BY session_id, ds_tax_apply_to
    ),
    -- [2] Commission tab de invoice
    commission_invoice_partner AS (
      SELECT
        CAST(REPLACE(CAST(h.id_partner AS STRING), ',', '') AS INT64) AS id_partner,
        SUM(
          CASE
            WHEN h.item_status = 'validated/expired' THEN h.variable_cc_for_fever
            WHEN h.item_status = 'canceled'           THEN h.AMOUNT_TO_COLLECT_FEVER
            ELSE 0
          END
        ) AS ticketing_commission,
        SUM(
          CASE
            WHEN h.item_status = 'validated/expired' THEN h.variable_cc_for_fever * COALESCE(ts.tax, td.tax, 0)
            WHEN h.item_status = 'canceled'           THEN h.AMOUNT_TO_COLLECT_FEVER * COALESCE(ts.tax, td.tax, 0)
            ELSE 0
          END
        ) AS tax_commission
      FROM base h
      LEFT JOIN taxes_tab AS ts
        ON ts.session_id = h.session_id
       AND ts.ds_tax_apply_to = CAST(h.id_plan AS STRING)
      LEFT JOIN taxes_tab AS td
        ON td.session_id = h.session_id
       AND td.ds_tax_apply_to = 'default'
      WHERE h.item_status IN ('validated/expired','canceled')
      GROUP BY h.id_partner
    ),
    -- [3] Marketing fee de invoice
    fixed_fees_invoice AS (
      SELECT
        f.session_id,
        COALESCE(
          SUM(CASE WHEN f.ds_fixed_type = 'Marketing'
                   THEN f.fixed_fee_invoice END), 0
        ) AS mkt_fixed_fees
      FROM `{T_FEES}` AS f
      JOIN sessions s USING (session_id)
      GROUP BY f.session_id
    ),
    fixed_fees_invoice_partner AS (
      SELECT
        CAST(REPLACE(CAST(s.id_partner AS STRING), ',', '') AS INT64) AS id_partner,
        SUM(fi.mkt_fixed_fees) AS invoice_mkt_fixed_fee
      FROM fixed_fees_invoice fi
      JOIN sessions s USING (session_id)
      GROUP BY s.id_partner
    ),
    -- Fixed fees settlement desglosado por tipo
    fixed_fees_settlement AS (
      SELECT
        f.session_id,
        -- MARKETING
        SUM(
          CASE WHEN f.ds_fixed_type = 'Marketing'
               THEN f.fixed_fee_settlement ELSE 0 END
        ) AS marketing_fixed_fees_total,
        SUM(
          CASE 
            WHEN f.ds_fixed_type = 'Marketing' AND f.apply_tax = TRUE
              THEN f.fixed_fee_settlement * COALESCE(ts.tax, td.tax, 0)
            ELSE 0
          END
        ) AS marketing_fixed_fees_tax_total,
        -- CASH ADVANCE (nunca lleva tax)
        SUM(
          CASE WHEN f.ds_fixed_type = 'Cash advance'
               THEN f.fixed_fee_settlement ELSE 0 END
        ) AS cash_advance_fixed_fees_total,
        0 AS cash_advance_fixed_fees_tax_total,
        -- SPONSORSHIP
        SUM(
          CASE WHEN f.ds_fixed_type = 'Sponsorship'
               THEN f.fixed_fee_settlement ELSE 0 END
        ) AS sponsorship_fixed_fees_total,
        SUM(
          CASE 
            WHEN f.ds_fixed_type = 'Sponsorship' AND f.apply_tax = TRUE
              THEN f.fixed_fee_settlement * COALESCE(ts.tax, td.tax, 0)
            ELSE 0
          END
        ) AS sponsorship_fixed_fees_tax_total,
        -- RECONCILIATION
        SUM(
          CASE WHEN f.ds_fixed_type = 'Reconciliation'
               THEN f.fixed_fee_settlement ELSE 0 END
        ) AS reconciliation_fixed_fees_total,
        SUM(
          CASE 
            WHEN f.ds_fixed_type = 'Reconciliation' AND f.apply_tax = TRUE
              THEN f.fixed_fee_settlement * COALESCE(ts.tax, td.tax, 0)
            ELSE 0
          END
        ) AS reconciliation_fixed_fees_tax_total,
        -- OTHER
        SUM(
          CASE WHEN f.ds_fixed_type = 'Other'
               THEN f.fixed_fee_settlement ELSE 0 END
        ) AS other_fixed_fees_total,
        SUM(
          CASE 
            WHEN f.ds_fixed_type = 'Other' AND f.apply_tax = TRUE
              THEN f.fixed_fee_settlement * COALESCE(ts.tax, td.tax, 0)
            ELSE 0
          END
        ) AS other_fixed_fees_tax_total
      FROM `{T_FEES}` AS f
      JOIN sessions s USING (session_id)
      LEFT JOIN taxes_tab AS ts
        ON ts.session_id = f.session_id
       AND ts.ds_tax_apply_to = f.ds_fixed_description
      LEFT JOIN taxes_tab AS td
        ON td.session_id = f.session_id
       AND td.ds_tax_apply_to = 'default'
      GROUP BY f.session_id
    ),
    fixed_fees_settlement_partner AS (
      SELECT
        CAST(REPLACE(CAST(s.id_partner AS STRING), ',', '') AS INT64) AS id_partner,
        SUM(fs.marketing_fixed_fees_total) AS marketing_fixed_fees_total,
        SUM(fs.marketing_fixed_fees_tax_total) AS marketing_fixed_fees_tax_total,
        SUM(fs.cash_advance_fixed_fees_total) AS cash_advance_fixed_fees_total,
        SUM(fs.cash_advance_fixed_fees_tax_total) AS cash_advance_fixed_fees_tax_total,
        SUM(fs.sponsorship_fixed_fees_total) AS sponsorship_fixed_fees_total,
        SUM(fs.sponsorship_fixed_fees_tax_total) AS sponsorship_fixed_fees_tax_total,
        SUM(fs.reconciliation_fixed_fees_total) AS reconciliation_fixed_fees_total,
        SUM(fs.reconciliation_fixed_fees_tax_total) AS reconciliation_fixed_fees_tax_total,
        SUM(fs.other_fixed_fees_total) AS other_fixed_fees_total,
        SUM(fs.other_fixed_fees_tax_total) AS other_fixed_fees_tax_total
      FROM fixed_fees_settlement fs
      JOIN sessions s USING (session_id)
      GROUP BY s.id_partner
    ),
    commission_invoice_partner AS (
      SELECT
        CAST(REPLACE(CAST(h.id_partner AS STRING), ',', '') AS INT64) AS id_partner,
        SUM(
          CASE
            WHEN h.item_status = 'validated/expired' THEN h.variable_cc_for_fever
            WHEN h.item_status = 'canceled'           THEN h.AMOUNT_TO_COLLECT_FEVER
            ELSE 0
          END
        ) AS ticketing_commission,
        SUM(
          CASE
            WHEN h.item_status = 'validated/expired' THEN h.variable_cc_for_fever * COALESCE(ts.tax, td.tax, 0)
            WHEN h.item_status = 'canceled'           THEN h.AMOUNT_TO_COLLECT_FEVER * COALESCE(ts.tax, td.tax, 0)
            ELSE 0
          END
        ) AS tax_commission
      FROM base h
      LEFT JOIN taxes_tab AS ts
        ON ts.session_id = h.session_id
       AND ts.ds_tax_apply_to = CAST(h.id_plan AS STRING)
      LEFT JOIN taxes_tab AS td
        ON td.session_id = h.session_id
       AND td.ds_tax_apply_to = 'default'
      WHERE h.item_status IN ('validated/expired','canceled')
      GROUP BY h.id_partner
    ),
    cancelled_info_tab AS (
      SELECT
        id_order_item,
        IFNULL(-MAX(TOTAL_TRANSACTION_VALUE), 0) AS hist_gross_revenue,
        IFNULL(-MAX(FT_COLLECTED_BY_FEVER), 0)   AS hist_collected_by_fever
      FROM base
      GROUP BY 1
    ),
    consolidated_info_tab AS (
      SELECT
        h.id_order_item,
        h.id_partner,
        h.item_status,
        CASE
          WHEN h.item_status = 'canceled'
            THEN c.hist_gross_revenue
          ELSE h.total_transaction_value
        END AS gross_transaction,
        CASE
          WHEN h.item_status = 'canceled'
            THEN c.hist_collected_by_fever
          ELSE h.ft_collected_by_fever
        END AS collected_by_fever
      FROM base h
      LEFT JOIN cancelled_info_tab c USING (id_order_item)
    ),
    revenue_by_partner AS (
      SELECT
        CAST(REPLACE(CAST(id_partner AS STRING), ',', '') AS INT64) AS id_partner,
        SUM(
          CASE
            WHEN item_status <> 'purchased'
              THEN collected_by_fever
            ELSE 0
          END
        ) AS revenue_collected_by_fever_no_purchased
      FROM consolidated_info_tab
      GROUP BY id_partner
    )
    SELECT
      CAST(REPLACE(CAST(p.id_partner AS STRING), ',', '') AS INT64) AS id_partner,
      -- [1] revenue_collected_by_fever (sin purchased)
      COALESCE(r.revenue_collected_by_fever_no_purchased, 0) AS gross_collected,
      -- [2] commission de ticketing
      COALESCE(ci.ticketing_commission, 0) AS commission,
      -- [3] marketing fee de invoice
      COALESCE(fi.invoice_mkt_fixed_fee, 0) AS marketing_fees,
      -- [4] total taxes = tax_commission + suma de taxes de fixed fees settlement
      (
        COALESCE(ci.tax_commission, 0)
        + COALESCE(fs.marketing_fixed_fees_tax_total, 0)
        + COALESCE(fs.cash_advance_fixed_fees_tax_total, 0)
        + COALESCE(fs.sponsorship_fixed_fees_tax_total, 0)
        + COALESCE(fs.reconciliation_fixed_fees_tax_total, 0)
        + COALESCE(fs.other_fixed_fees_tax_total, 0)
      ) AS total_taxes,
      -- [5] partner payment = [1] - [2] - fixed_fees_total (sin taxes) - [4]
      (
        COALESCE(r.revenue_collected_by_fever_no_purchased, 0)
        - COALESCE(ci.ticketing_commission, 0)
        - (
            COALESCE(fs.marketing_fixed_fees_total, 0)
            + COALESCE(fs.cash_advance_fixed_fees_total, 0)
            + COALESCE(fs.sponsorship_fixed_fees_total, 0)
            + COALESCE(fs.reconciliation_fixed_fees_total, 0)
            + COALESCE(fs.other_fixed_fees_total, 0)
          )
        - (
            COALESCE(ci.tax_commission, 0)
            + COALESCE(fs.marketing_fixed_fees_tax_total, 0)
            + COALESCE(fs.cash_advance_fixed_fees_tax_total, 0)
            + COALESCE(fs.sponsorship_fixed_fees_tax_total, 0)
            + COALESCE(fs.reconciliation_fixed_fees_tax_total, 0)
            + COALESCE(fs.other_fixed_fees_tax_total, 0)
          )
      ) AS pago_al_partner
    FROM (
      SELECT DISTINCT CAST(REPLACE(CAST(id_partner AS STRING), ',', '') AS INT64) AS id_partner
      FROM base
    ) p
    LEFT JOIN revenue_by_partner          r  ON p.id_partner = r.id_partner
    LEFT JOIN commission_invoice_partner  ci ON p.id_partner = ci.id_partner
    LEFT JOIN fixed_fees_invoice_partner  fi ON p.id_partner = fi.id_partner
    LEFT JOIN fixed_fees_settlement_partner fs ON p.id_partner = fs.id_partner
    ORDER BY p.id_partner
    """
    return execute_query(query)


def get_settlement_summary(where_clause: str = '') -> list:
    """Query RESUMEN SETTLEMENT - Completa con CTEs"""
    query = f"""
    WITH base AS (SELECT * FROM `{HIST}`{where_clause}),
    sessions AS (SELECT DISTINCT session_id FROM base),
    taxes_tab AS (
      SELECT session_id, ds_tax_apply_to, SUM(nm_tax_rate)/100 AS tax
      FROM `{T_TAXES}`
      WHERE session_id IN (SELECT session_id FROM sessions)
      GROUP BY session_id, ds_tax_apply_to
    ),
    fixed_fees_tab_1 AS (
      SELECT f.session_id, f.cd_contract, f.ds_fixed_description, f.fixed_fee_settlement,
             f.apply_tax,
             COALESCE(ts.tax, td.tax, 0) AS tax_rate_to_apply,
             f.fixed_fee_settlement * COALESCE(ts.tax, td.tax, 0) AS fixed_fee_settlement_tax,
             CASE WHEN ts.tax IS NOT NULL THEN 'specific'
                  WHEN td.tax IS NOT NULL THEN 'default' ELSE 'none' END AS tax_source
      FROM `{T_FEES}` AS f
      JOIN sessions s USING (session_id)
      LEFT JOIN taxes_tab AS ts ON ts.session_id = f.session_id AND ts.ds_tax_apply_to = f.ds_fixed_description
      LEFT JOIN taxes_tab AS td ON td.session_id = f.session_id AND td.ds_tax_apply_to = 'default'
    ),
    fixed_fees_tab AS (
      SELECT session_id,
             COALESCE(SUM(CASE WHEN ds_fixed_description = 'Marketing' THEN fixed_fee_settlement + fixed_fee_settlement_tax END),0) AS mkt_fixed_fees_w_tax,
             COALESCE(SUM(CASE WHEN ds_fixed_description = 'Cash advance' THEN fixed_fee_settlement END),0) AS cash_advance_w_tax,
             COALESCE(SUM(CASE WHEN ds_fixed_description NOT IN ('Marketing','Cash advance') THEN CASE WHEN CAST(apply_tax AS STRING) = 'No' OR apply_tax = FALSE THEN fixed_fee_settlement
             ELSE fixed_fee_settlement + fixed_fee_settlement_tax END END),0) AS other_fixed_fees_w_tax
      FROM fixed_fees_tab_1
      GROUP BY 1
    ),
    cancelled_info_tab AS (
      SELECT id_order_item, IFNULL(-MAX(TOTAL_TRANSACTION_VALUE),0) AS hist_gross_revenue,
                             IFNULL(-MAX(FT_COLLECTED_BY_FEVER),0) AS hist_collected_by_fever
      FROM base
      GROUP BY 1
    ),
    consolidated_info_tab AS (
      SELECT h.id_order_item, h.item_status,
             CASE WHEN h.item_status = 'canceled' THEN c.hist_gross_revenue  ELSE h.total_transaction_value END AS gross_transaction,
             CASE WHEN h.item_status = 'canceled' THEN c.hist_collected_by_fever ELSE h.ft_collected_by_fever END AS collected_by_fever
      FROM base h
      LEFT JOIN cancelled_info_tab c USING (id_order_item)
    ),
    commission_tab AS (
      SELECT
        h.session_id, h.invoice_id, h.dt_invoice_from, h.dt_invoice_to, h.dt_input, h.settlement_link,
        SUM(ci.gross_transaction) AS gross_revenue,
        SUM(ci.collected_by_fever) AS revenue_collected_by_fever,
        SUM(CASE WHEN h.item_status = 'validated/expired' THEN h.variable_cc_for_fever_w_taxes ELSE 0 END) AS executed_commission_w_tax,
        SUM(CASE WHEN h.item_status = 'canceled'           THEN h.variable_cc_for_fever_w_taxes ELSE 0 END) AS cancelled_commission_w_tax,
        SUM(CASE WHEN h.item_status = 'purchased'          THEN h.variable_cc_for_fever_w_taxes ELSE 0 END) AS ticketing_advance_commission_w_tax,
        SUM(h.variable_cc_for_partner_w_taxes) AS partner_settlement_ticketing
      FROM base h
      LEFT JOIN taxes_tab AS ts ON ts.session_id = h.session_id AND ts.ds_tax_apply_to = CAST(h.id_plan AS STRING)
      LEFT JOIN taxes_tab AS td ON td.session_id = h.session_id AND td.ds_tax_apply_to = 'default'
      LEFT JOIN consolidated_info_tab ci USING (id_order_item, item_status)
      GROUP BY 1,2,3,4,5,6
    ),
    fin AS (
      SELECT 
        dt_input,
        dt_invoice_from AS dt_settlement_from,
        dt_invoice_to   AS dt_settlement_to,
        settlement_link, 
        gross_revenue,
        revenue_collected_by_fever,
        executed_commission_w_tax, 
        cancelled_commission_w_tax,
        ticketing_advance_commission_w_tax,
        COALESCE(ff.mkt_fixed_fees_w_tax,0)   AS mkt_fixed_fee_w_tax,
        COALESCE(ff.cash_advance_w_tax,0)     AS cash_advance_w_tax, 
        COALESCE(ff.other_fixed_fees_w_tax,0) AS other_fixed_fee_w_tax, 
        revenue_collected_by_fever - (
          executed_commission_w_tax + cancelled_commission_w_tax + ticketing_advance_commission_w_tax +
          COALESCE(ff.mkt_fixed_fees_w_tax,0) + COALESCE(ff.cash_advance_w_tax,0) + COALESCE(ff.other_fixed_fees_w_tax,0)
        ) AS partner_settlement
      FROM commission_tab c
      LEFT JOIN fixed_fees_tab ff USING (session_id)
    )
    SELECT
      'TOTAL' AS settlement_link,
      NULL AS dt_input, NULL AS dt_settlement_from, NULL AS dt_settlement_to,
      SUM(gross_revenue) AS gross_revenue,
      SUM(revenue_collected_by_fever) AS revenue_collected_by_fever,
      SUM(executed_commission_w_tax) AS executed_commission_w_tax,
      SUM(cancelled_commission_w_tax) AS cancelled_commission_w_tax,
      SUM(ticketing_advance_commission_w_tax) AS ticketing_advance_commission_w_tax,
      SUM(mkt_fixed_fee_w_tax) AS mkt_fixed_fee_w_tax,
      SUM(cash_advance_w_tax) AS cash_advance_w_tax,
      SUM(other_fixed_fee_w_tax) AS other_fixed_fee_w_tax,
      SUM(partner_settlement) AS partner_settlement
    FROM fin
    UNION ALL
    SELECT
      settlement_link, dt_input, dt_settlement_from, dt_settlement_to,
      gross_revenue, revenue_collected_by_fever,
      executed_commission_w_tax, cancelled_commission_w_tax, ticketing_advance_commission_w_tax,
      mkt_fixed_fee_w_tax, cash_advance_w_tax, other_fixed_fee_w_tax, partner_settlement
    FROM fin
    ORDER BY dt_input DESC NULLS FIRST
    """
    return execute_query(query)


def save_results_to_bigquery(results: list, table_name: str, dataset_id: str = DATASET_ID):
    """Guarda resultados en una tabla de BigQuery"""
    if not results:
        logger.warning(f"No hay resultados para guardar en {table_name}")
        return
    
    client = get_bigquery_client()
    table_ref = client.dataset(dataset_id).table(table_name)
    
    # Crear tabla si no existe
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True
    )
    
    # Convertir resultados a JSON
    json_rows = [json.dumps(row, default=str) for row in results]
    
    job = client.load_table_from_json(
        [json.loads(row) for row in json_rows],
        table_ref,
        job_config=job_config
    )
    job.result()
    
    logger.info(f"Resultados guardados en {table_name}: {len(results)} filas")


def export_to_sheets_if_configured(results: list, sheet_id: str = None, sheet_name: str = None):
    """Exporta resultados a Google Sheets si está configurado"""
    sheet_id = sheet_id or GOOGLE_SHEETS_ID
    sheet_name = sheet_name or os.environ.get('GOOGLE_SHEETS_NAME', 'Results')
    
    if not sheet_id:
        logger.info("Google Sheets ID no configurado, omitiendo exportación")
        return
    
    try:
        from export_to_sheets import export_to_sheets
        export_to_sheets(sheet_id, sheet_name, results)
        logger.info(f"Resultados exportados a Google Sheets: {sheet_id}/{sheet_name}")
    except ImportError:
        logger.warning("Módulo export_to_sheets no disponible")
    except Exception as e:
        logger.error(f"Error exportando a Google Sheets: {e}")


def jfc_cash_to_pay_audit(request: Request) -> Dict[str, Any]:
    """
    Función HTTP que ejecuta queries de BigQuery y guarda resultados
    """
    # Manejar CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    try:
        # Obtener parámetros
        if request.method == 'GET':
            data = request.args.to_dict()
        else:
            data = request.get_json(silent=True) or {}
        
        query_type = data.get('query_type', 'partner_summary')
        id_partner = data.get('id_partner')
        cd_contract = data.get('cd_contract')
        
        logger.info(f"Ejecutando query tipo: {query_type}")
        
        # Construir WHERE clause si hay filtros
        where_clause = ''
        if id_partner:
            where_clause = f" WHERE CAST(REPLACE(id_partner, ',', '') AS INT64) = {id_partner}"
        elif cd_contract:
            where_clause = f" WHERE cd_contract = '{cd_contract}'"
        
        # Ejecutar query según tipo
        if query_type == 'partner_summary':
            results = get_partner_summary(where_clause)
            table_name = f'partner_summary_{datetime.now().strftime("%Y%m%d")}'
            sheet_name = 'Partner Summary'
        elif query_type == 'invoice_summary':
            results = get_invoice_summary(where_clause)
            table_name = f'invoice_summary_{datetime.now().strftime("%Y%m%d")}'
            sheet_name = 'Invoice Summary'
        elif query_type == 'settlement_summary':
            results = get_settlement_summary(where_clause)
            table_name = f'settlement_summary_{datetime.now().strftime("%Y%m%d")}'
            sheet_name = 'Settlement Summary'
        else:
            return (json.dumps({"error": "Tipo de query no válido"}), 400, headers)
        
        # Guardar resultados en BigQuery
        save_results_to_bigquery(results, table_name)
        
        # Exportar a Google Sheets (siempre, usando el spreadsheet configurado)
        export_to_sheets_if_configured(results, sheet_name=sheet_name)
        
        result = {
            "status": "success",
            "query_type": query_type,
            "rows_returned": len(results),
            "table_name": table_name,
            "dataset": DATASET_ID,
            "project": PROJECT_ID,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Query ejecutada exitosamente: {len(results)} filas")
        
        return (json.dumps(result), 200, headers)
        
    except Exception as e:
        logger.error(f"Error ejecutando query: {str(e)}", exc_info=True)
        error_response = {
            "status": "error",
            "message": str(e)
        }
        return (json.dumps(error_response), 500, headers)
