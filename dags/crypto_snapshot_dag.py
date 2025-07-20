from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import pickle
import pandas as pd
import kalshi_api.main as kpi
import logging
from crypto_book.btc_snap import save_stock_price, save_balance, fetch_and_process_data
from typing import Optional

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
    schedule="@daily",  # or None for manual
    catchup=False,
    tags=["btc", "kalshi"],
)




get_spot_task = PythonOperator(
    task_id="get_and_save_spot",
    python_callable=save_stock_price,
    op_kwargs={"ticker": "BTC-USD"},
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
get_maxy_markets_task = PythonOperator(
    task_id="get_and_save_maxy_markets",
    python_callable=lambda: kpi.get_event_markets("KXBTCMAXY-25").to_pickle("app_data/maxy_markets.pkl"),
    dag=dag,
)
get_miny_markets_task = PythonOperator(
    task_id="get_and_save_miny_markets",
    python_callable=lambda: kpi.get_event_markets("KXBTCMINY-25").to_pickle("app_data/miny_markets.pkl"),
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
get_balance_task >> enriched_positions_task
get_positions_task >> enriched_positions_task
get_spot_task >> enriched_positions_task
get_maxy_markets_task >> enriched_positions_task
get_miny_markets_task >> enriched_positions_task
get_orders_task >> enriched_positions_task

