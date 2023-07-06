import pickle


class Tradable:
    def serialize(self):
        return pickle.dumps(self, pickle.HIGHEST_PROTOCOL)

    def fromSerial(self, pickleDump):
        self = pickle.loads(pickleDump)
        return self

    def spot(self):
        return self.underlier


class VanillaOption(Tradable):
    def fromSerial(self, pickleDump):
        self = pickle.loads(pickleDump)
        return self

    def d_one(self, spot, strike, time, sigma, rate):
        val = (np.log(spot / strike) + (rate + 0.5 * sigma ** 2) * time / 365) / (sigma * np.sqrt(time))
        return val

    def d_two(self, spot, strike, time, sigma, rate):
        dOne = self.d_one(spot, strike, time / 252, sigma, rate)
        adj = sigma * sqrt(time / 252)
        return dOne - adj


class Portfolio:
    def __init__(self, legs: [], weights: []):
        self.legs = dict(zip(legs, weights))

    def time(self, clock=False):
        return max([leg.time(clock) for leg in self.legs])

    def sigma(self):
        return sum([leg.sigma() / len(self.legs) for leg in self.legs])

    def spot(self):
        return sum([leg.spot() / len(self.legs) for leg in self.legs])

    def price(self):
        return sum([x.price() * weight for x, weight in zip(self.legs.keys(), self.legs.values())])

    def delta(self):
        return sum([x.delta() * weight for x, weight in zip(self.legs.keys(), self.legs.values())])

    def vega(self):
        return sum([x.vega() * weight for x, weight in zip(self.legs.keys(), self.legs.values())])

    def theta(self):
        return sum([x.theta() * weight for x, weight in zip(self.legs.keys(), self.legs.values())])


class Range(Portfolio):
    def __init__(self, lowerBound, upperBound):
        self.lowerBound = lowerBound
        self.upperBound = upperBound
        super().__init__([lowerBound, upperBound], [1, -1])

    def floor_sigma(self):
        return self.lowerBound.sigma()

    def cap_sigma(self):
        return self.upperBound.sigma()

    def cap(self):
        return self.lowerBound.strike

    def floor(self):
        return self.upperBound.strike

    def spot(self):
        return self.spot


class BinaryOption(Tradable):
    def __init__(self, underlier, strike: float, expiry, isCall: bool, pair):
        if strike == 'NA':
            self.isValid = False
        else:
            self.isValid = True
        self.strike = strike
        self.isCall = isCall
        self.expiry = expiry

    def price(self):
        callPrice = float(norm.cdf(self.d_two(self.spot(), float(self.strike), self.time(), self.sigma(), self.rate())))
        if self.isCall:
            return callPrice
        else:
            return 1 - callPrice

    def delta(self):
        up_market = copy.deepcopy(self.pair)
        up_market.diddle.spot = .01
        up_price = BinaryOption(underlier=self.underlier, strike=self.strike, expiry=self.expiry, isCall=self.isCall,
                                pair=up_market).price()
        downMarket = copy.deepcopy(self.pair)
        downMarket.diddle.spot = -.01
        down_price = BinaryOption(underlier=self.underlier, strike=self.strike, expiry=self.expiry, isCall=self.isCall,
                                  pair=downMarket).price()
        return (up_price - down_price) / .02

    def vega(self):
        up_market = copy.deepcopy(self.pair)
        up_market.diddle.vol = .01
        up_price = BinaryOption(underlier=self.underlier, strike=self.strike, expiry=self.expiry, isCall=self.isCall,
                                pair=up_market).price()
        downMarket = copy.deepcopy(self.pair)
        downMarket.diddle.vol = -.01
        down_price = BinaryOption(underlier=self.underlier, strike=self.strike, expiry=self.expiry, isCall=self.isCall,
                                  pair=downMarket).price()
        return (up_price - down_price) / .02

    def theta(self):
        up_price = BinaryOption(underlier=self.underlier, strike=self.strike, expiry=self.expiry + timedelta(minutes=1),
                                isCall=self.isCall, pair=self.pair).price()
        down_price = BinaryOption(underlier=self.underlier, strike=self.strike,
                                  expiry=self.expiry - timedelta(minutes=1), isCall=self.isCall, pair=self.pair).price()
        return (up_price - down_price) / 1440

    def sigma(self):
        return self.pair.vol(self.strike)

    def rate(self):
        return .02

    def implied_volatility(self, price, vol_min=0, vol_max=1, tol=.02):
        """find implied vol given price"""
        within_tol = False
        while not within_tol:
            px = self.price

    def clock_time(self):
        return (self.expiry - datetime.now()) / timedelta(days=1)

    def vol_time(self):
        decay = self.pair.two_four_decay()
        decay = decay['pct']
        part_hour = decay[datetime.now().hour] * (datetime.now().minute / 60)
        if self.expiry.hour < datetime.now().hour:
            r1 = decay[datetime.now().hour:-1].sum()
            r2 = decay[0:datetime.now().hour].sum()
            remainder = r1 + r2
        else:
            remainder = decay[datetime.now().hour:self.expiry.hour].sum()
        return part_hour + remainder

    def financial_time(self):
        return self.vol_time() * self.sigma()

    def time(self, clock=False):
        if clock:
            return self.clock_time()
        else:
            return self.vol_time()


