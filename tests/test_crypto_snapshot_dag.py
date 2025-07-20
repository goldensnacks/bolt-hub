"""
Pytest tests for crypto_snapshot_dag
"""
import pytest
import sys
import os
import pandas as pd
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dags.crypto_snapshot_dag import fetch_and_process_data
import kalshi_api.main as kpi

# Set up logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture
def setup_logging():
    """Setup logging for tests"""
    logger = logging.getLogger("test_crypto_dag")
    logger.setLevel(logging.INFO)
    return logger

class TestCryptoSnapshotDAG:
    """Test class for crypto snapshot DAG functionality"""
    
    def test_balance_fetching(self, setup_logging):
        """Test balance fetching functionality"""
        logger = setup_logging
        logger.info("Testing balance fetching...")
        
        try:
            balance = kpi.get_balance()
            logger.info(f"Balance type: {type(balance)}, value: {balance}")
            
            assert balance is not None, "Balance should not be None"
            assert isinstance(balance, (int, float)), "Balance should be numeric"
            
            logger.info("✅ Balance fetching test passed")
        except Exception as e:
            logger.error(f"❌ Balance fetching failed: {e}")
            pytest.fail(f"Balance fetching failed: {e}")
    
    def test_positions_fetching(self, setup_logging):
        """Test positions fetching functionality"""
        logger = setup_logging
        logger.info("Testing positions fetching...")
        
        try:
            positions = kpi.get_positions()
            logger.info(f"Positions type: {type(positions)}")
            
            if hasattr(positions, 'shape'):
                logger.info(f"Positions shape: {positions.shape}")
            if hasattr(positions, 'columns'):
                logger.info(f"Positions columns: {list(positions.columns)}")
            
            assert positions is not None, "Positions should not be None"
            assert hasattr(positions, 'shape'), "Positions should have shape attribute"
            
            logger.info("✅ Positions fetching test passed")
        except Exception as e:
            logger.error(f"❌ Positions fetching failed: {e}")
            pytest.fail(f"Positions fetching failed: {e}")
    
    def test_markets_fetching(self, setup_logging):
        """Test markets fetching and concatenation"""
        logger = setup_logging
        logger.info("Testing markets fetching...")
        
        try:
            miny_markets = kpi.get_event_markets("KXBTCMINY-25")
            maxy_markets = kpi.get_event_markets("KXBTCMAXY-25")
            
            logger.info(f"MINY markets type: {type(miny_markets)}")
            if hasattr(miny_markets, 'shape'):
                logger.info(f"MINY markets shape: {miny_markets.shape}")
            
            logger.info(f"MAXY markets type: {type(maxy_markets)}")
            if hasattr(maxy_markets, 'shape'):
                logger.info(f"MAXY markets shape: {maxy_markets.shape}")
            
            # Test concatenation
            combined = pd.concat([miny_markets, maxy_markets], ignore_index=True)
            logger.info(f"Combined markets shape: {combined.shape}")
            
            assert miny_markets is not None, "MINY markets should not be None"
            assert maxy_markets is not None, "MAXY markets should not be None"
            assert combined.shape[0] > 0, "Combined markets should have rows"
            
            logger.info("✅ Markets fetching test passed")
        except Exception as e:
            logger.error(f"❌ Markets fetching failed: {e}")
            pytest.fail(f"Markets fetching failed: {e}")
    
    def test_enriched_position_df_function(self, setup_logging):
        """Test the enriched_position_df function specifically"""
        logger = setup_logging
        logger.info("Testing enriched_position_df function...")
        
        try:
            from crypto_book.btc_snap import enriched_position_df
            
            # Get the data first
            positions = kpi.get_positions()
            miny_markets = kpi.get_event_markets("KXBTCMINY-25")
            maxy_markets = kpi.get_event_markets("KXBTCMAXY-25")
            btc_markets = pd.concat([miny_markets, maxy_markets], ignore_index=True)
            
            logger.info(f"Positions shape: {positions.shape}")
            logger.info(f"BTC markets shape: {btc_markets.shape}")
            
            # Test the function
            enriched_positions = enriched_position_df(positions, btc_markets)
            logger.info(f"Enriched positions shape: {enriched_positions.shape}")
            
            # Check that required columns exist
            required_columns = ['mid', 'strike', 'vol_mark', 'implied_vol_mid', 'delta_by_mid', 'position_delta']
            missing_columns = [col for col in required_columns if col not in enriched_positions.columns]
            
            if missing_columns:
                logger.warning(f"Missing columns: {missing_columns}")
                logger.info(f"Available columns: {list(enriched_positions.columns)}")
            
            assert enriched_positions is not None, "Enriched positions should not be None"
            assert hasattr(enriched_positions, 'shape'), "Enriched positions should have shape attribute"
            assert 'mid' in enriched_positions.columns, "Enriched positions should have 'mid' column"
            
            logger.info("✅ enriched_position_df test passed")
        except Exception as e:
            logger.error(f"❌ enriched_position_df failed: {e}")
            pytest.fail(f"enriched_position_df failed: {e}")
    
    def test_orders_fetching(self, setup_logging):
        """Test orders fetching functionality"""
        logger = setup_logging
        logger.info("Testing orders fetching...")
        
        try:
            orders = kpi.get_orders()
            logger.info(f"Orders type: {type(orders)}")
            
            if hasattr(orders, 'shape'):
                logger.info(f"Orders shape: {orders.shape}")
            
            assert orders is not None, "Orders should not be None"
            
            logger.info("✅ Orders fetching test passed")
        except Exception as e:
            logger.error(f"❌ Orders fetching failed: {e}")
            pytest.fail(f"Orders fetching failed: {e}")
    
    def test_full_dag_execution(self, setup_logging):
        """Test the complete DAG function"""
        logger = setup_logging
        logger.info("Testing complete DAG function...")
        
        try:
            result = fetch_and_process_data()
            logger.info(f"DAG execution result: {result}")
            
            assert result == "SUCCESS", f"Expected 'SUCCESS', got {result}"
            
            logger.info("✅ Complete DAG test passed")
        except Exception as e:
            logger.error(f"❌ Complete DAG test failed: {e}")
            pytest.fail(f"Complete DAG test failed: {e}")

# Individual test functions for running specific tests
def test_balance():
    """Individual test for balance fetching"""
    test_instance = TestCryptoSnapshotDAG()
    test_instance.test_balance_fetching(logging.getLogger("test_balance"))

def test_positions():
    """Individual test for positions fetching"""
    test_instance = TestCryptoSnapshotDAG()
    test_instance.test_positions_fetching(logging.getLogger("test_positions"))

def test_markets():
    """Individual test for markets fetching"""
    test_instance = TestCryptoSnapshotDAG()
    test_instance.test_markets_fetching(logging.getLogger("test_markets"))

def test_enriched_position_df():
    """Individual test for enriched_position_df function"""
    test_instance = TestCryptoSnapshotDAG()
    test_instance.test_enriched_position_df_function(logging.getLogger("test_enriched_position_df"))

def test_orders():
    """Individual test for orders fetching"""
    test_instance = TestCryptoSnapshotDAG()
    test_instance.test_orders_fetching(logging.getLogger("test_orders"))

def test_full_dag():
    """Individual test for full DAG execution"""
    test_instance = TestCryptoSnapshotDAG()
    test_instance.test_full_dag_execution(logging.getLogger("test_full_dag")) 