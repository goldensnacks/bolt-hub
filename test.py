from securities.graph import get_security, Security
from tradables.underliers import Cross, Currency

usd, jpy = Security("usd",Currency()), Security("jpy", Currency())

usd.value_in_usd = 1.0
jpy.value_in_usd = 0.009

usdjpy = Security("usdjpy", Cross("usd", "jpy"))

print(usdjpy.spot)
