from .graph import Security, save_security, get_security


UNDERLIERS_TO_INIT = ["EURUSD"]
INFRA_TO_INIT = ["tradables"]
for ticker in UNDERLIERS_TO_INIT:
    sec = Security(ticker, "Underlier()")
    sec.save()
for infra in INFRA_TO_INIT:
    sec = Security(infra, "MarketTable()")
    sec.save()
print("Done")


