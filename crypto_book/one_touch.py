from datetime import datetime, date
from datetime import timedelta

from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.models.black_scholes import BlackScholes
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.utils import TouchOptionTypes
from financepy.utils.date import Date



class OneTouch(EquityOneTouchOption ):
    def __init__(self, expiry, option_type, barrier, payment):
        super().__init__(expiry, option_type, barrier, payment)

    # define string representation
    def __repr__(self):
        return f"OneTouch(expiry={self.expiry}, option_type={self.option_type}, barrier={self.barrier}, payment={self.payment})"