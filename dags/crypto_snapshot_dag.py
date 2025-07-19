from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import pickle
import pandas as pd
import kalshi_api.main as kpi
from crypto_book.btc_snap import enriched_position_df  # adjust path if needed
import logging

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


from crypto_book.btc_snap import get_stock_price
from typing import Optional

def save_stock_price(ticker: str, output_path: Optional[str] = None):
    """
    Fetches the latest closing price for a given ticker and saves it to a pickle file.

    Parameters
    ----------
    ticker : str
        The ticker symbol (e.g., 'BTC-USD').
    output_path : str
        The file path where the price will be saved.
    """
    if output_path is None:
        output_path = f"app_data/{ticker}.pkl"
    price = get_stock_price(ticker)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(price, f)
    logger.info(f"Saved {ticker} price ({price}) to {output_path}")


def save_balance(output_path: str = "app_data/balance.pkl"):
    """
    Fetches the account balance and saves it to a pickle file.

    Parameters
    ----------
    output_path : str
        The file path where the balance will be saved.
    """
    try:
        balance = kpi.get_balance()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(balance, f)
        logger.info(f"Saved account balance ({balance}) to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save account balance: {e}", exc_info=True)
        raise



def fetch_and_process_data():
    try:
        logger.info("Fetching account balance...")
        balance = kpi.get_balance()
        logger.info(f"Balance type: {type(balance)}, value: {balance}")
        os.makedirs("app_data", exist_ok=True)
        with open("app_data/balance.pkl", "wb") as f:
            pickle.dump(balance, f)
        logger.info("Balance fetched and saved.")

        logger.info("Fetching positions...")
        positions = kpi.get_positions()
        logger.info(f"Positions shape: {positions.shape if hasattr(positions, 'shape') else 'No shape'}")
        
        logger.info("Fetching BTC markets...")
        miny_markets = kpi.get_event_markets("KXBTCMINY-25")
        maxy_markets = kpi.get_event_markets("KXBTCMAXY-25")
        logger.info(f"MINY markets type: {type(miny_markets)}, shape: {miny_markets.shape if hasattr(miny_markets, 'shape') else 'No shape'}")
        logger.info(f"MAXY markets type: {type(maxy_markets)}, shape: {maxy_markets.shape if hasattr(maxy_markets, 'shape') else 'No shape'}")
        
        # Use pd.concat instead of append
        btc_markets = pd.concat([miny_markets, maxy_markets], ignore_index=True)
        logger.info(f"Combined BTC markets shape: {btc_markets.shape}")
        
        logger.info("Enriching positions...")
        enriched_positions = enriched_position_df(positions, btc_markets)
        enriched_positions.to_pickle("app_data/enriched_positions.pkl")
        logger.info("Enriched positions saved.")

        logger.info("Fetching orders...")
        orders = kpi.get_orders()
        orders.to_pickle("app_data/orders.pkl")
        logger.info("Orders saved.")
        
        logger.info("DAG execution completed successfully!")
        return "SUCCESS"
    except Exception as e:
        logger.error(f"Error in fetch_and_process_data: {e}", exc_info=True)
        raise


if __name__ != "__main__":
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

    enriched_positions_task = PythonOperator(
        task_id="fetch_enriched_positions",
        python_callable=fetch_and_process_data,
        dag=dag,
    )

    get_spot_task >> get_balance_task >> enriched_positions_task

