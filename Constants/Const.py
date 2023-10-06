from datetime import timedelta
import pandas as pd
import os

DATE_OFFSETS = {
    '1D': timedelta(days=1),
    '1W': timedelta(weeks=1),
    '2W': timedelta(weeks=2),
    '3W': timedelta(weeks=3),
    '1M': timedelta(days=30),
    '2M': timedelta(days=60),
    '3M': timedelta(days=90),
    '6M': timedelta(days=180),
    '9M': timedelta(days=270),
    '1Y': timedelta(days=365),
    'Overnight': timedelta(days=1),
    'Tomorrow Next': timedelta(days=1),
    'Spot Next': timedelta(days=2),
    'One Week': timedelta(weeks=1),
    'Two Weeks': timedelta(weeks=2),
    'Three Weeks': timedelta(weeks=3),
    'One Month': timedelta(days=30),
    'Two Months': timedelta(days=60),
    'Three Months': timedelta(days=90),
    'Four Months': timedelta(days=120),
    'Five Months': timedelta(days=150),
    'Six Months': timedelta(days=180),
    'Seven Months': timedelta(days=210),
    'Eight Months': timedelta(days=240),
    'Nine Months': timedelta(days=270),
    'Ten Months': timedelta(days=300),
    'Eleven Months': timedelta(days=330),
    'One Year': timedelta(days=365),
    'Two Years': timedelta(days=730),
    'Three Years': timedelta(days=1095),
    'Four Years': timedelta(days=1460),
    'Five Years': timedelta(days=1825),
    'Six Years': timedelta(days=2190),
    'Seven Years': timedelta(days=2555),
    'Ten Years': timedelta(days=3650),
}
