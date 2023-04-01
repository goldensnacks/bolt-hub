import yfinance as yf

class YFinanceSource:
    def __init__(self, symbol):
        self.ticker = yf.Ticker(symbol)
        self.create_time = time.time()

    def vol_surface(self):
        ticker = self.ticker
        supported_dates = ticker.options

        surface_calls = pd.concat(list(
            map(lambda date: (ticker.option_chain(date).calls[["strike", "impliedVolatility"]]).set_index('strike'),
                supported_dates)), axis=1).T
        surface_puts = pd.concat(list(
            map(lambda date: (ticker.option_chain(date).puts[["strike", "impliedVolatility"]]).set_index('strike'),
                supported_dates)), axis=1).T

        def combine(A, B):
            if A is numpy.NaN:
                if B is numpy.NaN:
                    return None
                else:
                    return B
            if B is numpy.NaN:
                return A
            return (A + B) / 2

        surface = surface_calls.combine(surface_puts, combine)
        surface['dates'] = list(map(lambda date: ((datetime.strptime(date,
                                                                     "%Y-%m-%d").timestamp() - datetime.today().timestamp()) / 86400) + 16 / 24,
                                    supported_dates))
        surface = (surface.reset_index(drop=True)).set_index('dates').sort_index(axis=1)
        surface = surface.loc[[y for y in surface.index.values.tolist()],
                              [x for x in surface.columns.values.tolist()]]

        tenors = surface.index.values
        x, y = np.mgrid[0:len(surface), 0:len(surface.columns)]
        ix_notna = surface.notna().values
        z_interpolated = interpolate.griddata(
            (x[ix_notna], y[ix_notna]),
            surface.values[ix_notna],
            (x, y),
            method='linear')
        strikes = surface.columns.values
        surface = (pd.DataFrame(z_interpolated).reset_index(drop=True)).set_index(tenors)
        surface.columns = strikes
        return surface