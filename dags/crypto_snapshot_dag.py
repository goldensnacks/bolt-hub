from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import pickle
import pandas as pd
import kalshi_api.main as kpi
import logging
from crypto_book.btc_snap import save_stock_price, save_balance, fetch_and_process_data, portfolio_greeks_df
from typing import Optional
from constants.constants import BITCOIN_TICKERS, ETH_TICKERS

# Set up logging
logger = logging.getLogger("airflow.task.crypto_snapshot")
logger.setLevel(logging.INFO)

# Optionally, add a handler if running outside Airflow's managed logging
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
}

dag = DAG(
    dag_id="btc_snapshot_dag",
    default_args=default_args,
    # run every 5 minutes
    schedule="*/5 * * * *",  # or None for manual
    catchup=False,
    tags=["btc", "eth", "kalshi"],
)


get_btc_spot_task = PythonOperator(
    task_id="get_and_save_btc_spot",
    python_callable=save_stock_price,
    op_kwargs={"ticker": "BTC-USD"},
    dag=dag,
)

get_eth_spot_task = PythonOperator(
    task_id="get_and_save_eth_spot",
    python_callable=save_stock_price,
    op_kwargs={"ticker": "ETH-USD"},
    dag=dag,
)

get_balance_task = PythonOperator(
    task_id="get_and_save_balance",
    python_callable=save_balance,
    op_kwargs={"output_path": "app_data/balance.pkl"},
    dag=dag,
)
get_positions_task = PythonOperator(
    task_id="get_and_save_positions",
    python_callable=lambda: kpi.get_positions().to_pickle("app_data/positions.pkl"),
    dag=dag,
)
get_btc_maxy_markets_task = PythonOperator(
    task_id="get_and_save_btc_maxy_markets",
    python_callable=lambda: kpi.get_event_markets(BITCOIN_TICKERS["kalshi_maxy"]).to_pickle("app_data/btc_maxy_markets.pkl"),
    dag=dag,
)
get_btc_miny_markets_task = PythonOperator(
    task_id="get_and_save_btc_miny_markets",
    python_callable=lambda: kpi.get_event_markets(BITCOIN_TICKERS["kalshi_miny"]).to_pickle("app_data/btc_miny_markets.pkl"),
    dag=dag,
)
get_eth_maxy_markets_task = PythonOperator(
    task_id="get_and_save_eth_maxy_markets",
    python_callable=lambda: kpi.get_event_markets(ETH_TICKERS["kalshi_maxy"]).to_pickle("app_data/eth_maxy_markets.pkl"),
    dag=dag,
)
get_orders_task = PythonOperator(
    task_id="get_and_save_orders",
    python_callable=lambda: kpi.get_orders().to_pickle("app_data/orders.pkl"),
    dag=dag,
)
enriched_positions_task = PythonOperator(
    task_id="fetch_enriched_positions",
    python_callable=fetch_and_process_data,
    dag=dag,
)
portfolio_greeks_task = PythonOperator(
    task_id="portfolio_greeks",
    python_callable=lambda:portfolio_greeks_df(pd.read_pickle("app_data/enriched_positions.pkl")).to_pickle("app_data/greeks.pkl"),
    dag=dag,
)
get_balance_task >> enriched_positions_task
get_positions_task >> enriched_positions_task
get_btc_spot_task >> enriched_positions_task
get_eth_spot_task >> enriched_positions_task
get_btc_maxy_markets_task >> enriched_positions_task
get_btc_miny_markets_task >> enriched_positions_task
get_orders_task >> enriched_positions_task
enriched_positions_task >> portfolio_greeks_task


