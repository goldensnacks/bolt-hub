#!/usr/bin/env python3
"""
Entry point script to run the multi-underlier trading dashboard.

This script provides a simple way to launch the trading dashboard
from the project root directory with autoreload support.

Usage:
    python run_dashboard.py
    python run_dashboard.py --no-autoreload  # Disable autoreload
    python run_dashboard.py --port 5006      # Use custom port
    python run_dashboard.py --underliers BTC,ETH,SOL  # Specify underliers
    ./run_dashboard.py  # If executable
"""

import sys
import os
import argparse
import logging
import signal
import atexit
import panel as pn
pn.extension("tabulator")


logger = logging.getLogger("run_dashboard")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Default dashboard port (avoiding common conflicts: 8080=Airflow, 5000=Flask, 3000=React)
DEFAULT_PORT = 5006

# Global variable to store the server for cleanup
server = None

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    logger.info(f"\n🛑 Received signal {signum} - shutting down dashboard...")
    cleanup_and_exit()

def cleanup_and_exit():
    """Clean up resources and exit gracefully."""
    global server
    try:
        if server is not None:
            logger.info("🔄 Stopping dashboard server...")
            server.stop()
            server.io_loop.stop()
            logger.info("✅ Dashboard server stopped")
    except Exception as e:
        logger.warning(f"⚠️  Error during cleanup: {e}")
    finally:
        logger.info("👋 Dashboard shutdown complete")
        sys.exit(0)

def create_multi_underlier_dashboard(underliers):
    """
    Create a multi-underlier dashboard with tabs for each underlier.
    
    Parameters
    ----------
    underliers : list
        List of underlier symbols (e.g., ['BTC', 'ETH', 'SOL'])
        
    Returns
    -------
    panel.Column
        Dashboard with tabs for each underlier
    """
    from crypto_book.dashboards.trading_app import TradingDashboard
    
    # Create dashboard instances for each underlier
    dashboard_instances = {}
    dashboard_tabs = []
    
    for underlier in underliers:
        try:
            logger.info(f"📊 Creating dashboard for {underlier}...")
            dashboard_instance = TradingDashboard(underlier=underlier)
            dashboard_tab = dashboard_instance.create_dashboard()
            dashboard_instances[underlier] = dashboard_instance
            dashboard_tabs.append((underlier, dashboard_tab))
            logger.info(f"✅ {underlier} dashboard created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create {underlier} dashboard: {e}")
            # Create a placeholder tab with error message
            error_tab = pn.Column(
                f"# {underlier} Dashboard",
                pn.pane.Alert(f"❌ Error loading {underlier} data: {str(e)}", alert_type="danger"),
                pn.pane.Str("Please check that the required data files exist and are accessible.")
            )
            dashboard_tabs.append((underlier, error_tab))
    
    # Create the main dashboard with tabs
    if len(dashboard_tabs) == 1:
        # Single underlier - return the dashboard directly
        return dashboard_tabs[0][1]
    else:
        # Multiple underliers - create tabbed interface
        main_dashboard = pn.Column(
            "# Multi-Underlier Trading Dashboard",
            pn.pane.Str(f"📈 Monitoring: {', '.join(underliers)}"),
            pn.Tabs(*dashboard_tabs),
            sizing_mode="stretch_width"
        )
        return main_dashboard

def main():
    """Main entry point for the dashboard."""
    global server
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Register cleanup function to run on exit
    atexit.register(cleanup_and_exit)
    
    parser = argparse.ArgumentParser(description='Run the Multi-Underlier Trading Dashboard')
    parser.add_argument('--no-autoreload', action='store_true', 
                       help='Disable autoreload (useful for production)')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                       help=f'Port to run the dashboard on (default: {DEFAULT_PORT})')
    parser.add_argument('--underliers', type=str, default='BTC,ETH',
                       help='Comma-separated list of underliers (default: BTC,ETH)')
    args = parser.parse_args()
    
    # Parse underliers
    underliers = [u.strip().upper() for u in args.underliers.split(',') if u.strip()]
    if not underliers:
        logger.error("❌ No valid underliers specified")
        sys.exit(1)
    
    try:
        # Add the project root to the Python path so we can use absolute imports
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        logger.info("🚀 Starting Multi-Underlier Trading Dashboard...")
        logger.info(f"📍 Dashboard will be available at: http://localhost:{args.port}")
        logger.info(f"📊 Underliers: {', '.join(underliers)}")
        
        if not args.no_autoreload:
            logger.info("🔄 Autoreload enabled - changes will automatically refresh the dashboard")
        else:
            logger.info("⏸️  Autoreload disabled")
            
        logger.info("⏹️  Press Ctrl+C to stop the server")
        logger.info("-" * 50)
        
        if not args.no_autoreload:
            # Enable autoreload for development
            import panel as pn
            pn.config.autoreload = True
            logger.info("✅ Autoreload configured")
        
        # Configure the dashboard to use the specified port
        
        # Allow websocket connections from WSL2 IP addresses
        os.environ['BOKEH_ALLOW_WS_ORIGIN'] = f'localhost:{args.port},172.24.167.61:{args.port},172.17.0.1:{args.port},192.168.49.1:{args.port}'
        
        # Create multi-underlier dashboard
        # dashboard = create_multi_underlier_dashboard(underliers)
        dashboard_loader = lambda: create_multi_underlier_dashboard(underliers)

        
        # Serve the dashboard with proper server reference for cleanup
        server = pn.serve(
            # dashboard,
            dashboard_loader, 
            port=args.port, 
            show=True, 
            allow_websocket_origin=[
                f'localhost:{args.port}', 
                f'172.24.167.61:{args.port}', 
                f'172.17.0.1:{args.port}', 
                f'192.168.49.1:{args.port}'
            ],
            return_server=True  # Return server object for cleanup
        )
        
        # Keep the server running
        try:
            server.start()
            server.io_loop.start()
        except KeyboardInterrupt:
            logger.info("\n🛑 Keyboard interrupt received - shutting down...")
            cleanup_and_exit()
        
    except ImportError as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"❌ Import error: {e}")
        logger.error("💡 Make sure you're running this from the project root directory")
        logger.error("💡 Ensure all dependencies are installed: pip install -r requirements.txt")
        logger.error("🔎 Import failed at:\n" + tb)
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error starting dashboard: {e}")
        import traceback
        logger.error("🔎 Full traceback:\n" + traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 