import numpy as np
import pandas as pd
from scipy.interpolate import interp1d, interp2d

import securities
from .pricing_helper_fns import solve_vanilla_bs_for_strike, interpret_tenor


class Underlier:
    def __init__(self):
        pass

    """spot & forward curve"""
    def mark_spot(self, spot):
        """spot represents current price, also remarking spot will reset forward curve"""
        self.spot = spot

    def get_spot(self):
        return self.spot if hasattr(self, 'spot') else None

    def forward_curve_as_fn(self):
        if isinstance(self.forward_curve, dict):
            curve = pd.DataFrame(self.forward_curve)
        base_spot = curve.values[0][0]
        live_spot = self.spot
        x = [interpret_tenor(x) for x in curve.index]
        y = [y[0]/base_spot * live_spot for y in curve.values]
        return interp1d(x, y, kind='linear')


    def load_forward_curve(self, forward_curve):
        self.forward_curve = forward_curve

    def load_vol_surface(self, vol_surface, by_strike =False):
        """vol surface is a dataframe with strike as index and tenor as columns"""
        vol_surface = pd.DataFrame(vol_surface)
        index = vol_surface.index
        index = [interpret_tenor(tenor) for tenor in index]
        vol_surface.index = index
        if by_strike:
            self.vol_surface_by_strike = vol_surface
        else:
            self.vol_surface = vol_surface
    def mark_vol(self, strike, tenor, vol):
        """mark vol at a given strike and tenor - for fx, strike is usually RR or BF and a delta"""
        self.vol_surface.loc[strike, tenor] = vol

    def get_smile_points(self, smile, tenor):
        """mark smile points for a given tenor"""
        twenty_five_call_sigma = smile['ATM']+smile['BF25']+smile['RR25']/2
        twenty_five_put_sigma = smile['ATM']-smile['BF25']-smile['RR25']/2
        ten_call_sigma = smile['ATM']+smile['BF10']+smile['RR10']/2
        ten_put_sigma = smile['ATM']-smile['BF10']-smile['RR10']/2
        delta_sigma = {delta:sigma for delta, sigma in zip(
                        ['25c', '10c', '25p', '10p'],
                        [twenty_five_call_sigma, ten_call_sigma, twenty_five_put_sigma, ten_put_sigma])
                       }
        strike_sigma = {solve_vanilla_bs_for_strike(delta, self.get_spot(), .04, tenor, sigma):sigma
                        for delta, sigma in delta_sigma.items()}
        return strike_sigma

    def complete_surface_from_marks(self):
        smiles = self.vol_surface_by_strike.transpose().to_dict()
        new_surface = {tenor: self.get_smile_points(smile, tenor) for tenor, smile in smiles.items()}
        self.vol_surface = pd.DataFrame(new_surface).transpose()
        self.vol_surface = self.vol_surface.reindex(sorted(self.vol_surface.columns), axis=1)
        self.vol_surface.interpolate(inplace=True)

    def vol_surface_as_fn(self):
        vol_surface = self.vol_surface.to_dict()
        Xs, Ys, Zs = [], [], []
        for x in vol_surface.keys():
            for y in vol_surface[x].keys():
                Xs.append(x)
                Ys.append(interpret_tenor(y))
                Zs.append(vol_surface[x][y] if not np.isnan(vol_surface[x][y]) else 0)
        return interp2d(Xs, Ys, Zs)

    def get_vol_surface(self):
        return self.vol_surface

    def get_vol(self, tenor, strike = None, delta = None):
        if strike is not None:
            return self.vol_surface_as_fn()(strike, tenor.total_seconds()/86400)
        elif delta is not None:
            return self.vol_surface_as_fn()(delta, tenor.total_seconds()/86400)
        else:
            raise Exception('Must provide either strike or delta')

    def load_intraday_weights(self, weights):
        self.intraday_weights = weights


    def get_intraday_weight(self, start, end):
        weights = self.intraday_weights
        if isinstance(weights, dict):
            weights = pd.DataFrame(weights)
        weights = weights['Cumulative']
        if start < end:
            return weights.loc[start:end].mean() / weights.mean()
        else:
            left_today = weights.loc[start:23].mean() * (24 - start)
            right_today = weights.loc[0:end].mean() * end
            weighted_mean = (left_today + right_today) / (24 - start + end)
            return weighted_mean / weights.mean()

class Cross(Underlier):
    def __init__(self, funding_asset: str, asset):
        self.funding_asset = securities.get_security(funding_asset)
        self.asset = securities.get_security(asset)
class Asset:
    pass

class Currency(Asset):
    def __init__(self, name):
        self.name = name

    def yield_curve(self):
        pass

