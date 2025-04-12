from datetime import datetime, date
from datetime import timedelta
from logging import getLogger

import pandas as pd
from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.models.black_scholes import BlackScholes
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.utils import TouchOptionTypes
from financepy.utils.date import Date

from logging import getLogger

from datetime import datetime, date
from datetime import timedelta
from logging import getLogger

from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.models.black_scholes import BlackScholes
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.utils import TouchOptionTypes
from financepy.utils.date import Date
import yfinance as yf
from crypto_book import *
from logging import getLogger

logger = getLogger('backtester_fns.pyxll_functions')

from marking_cycles.kalshi_api import KalshiSession, snap_markets

if __name__ == '__main__':
    logger.info(
    snap_markets(KalshiSession())
    )
