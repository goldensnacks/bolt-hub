import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq

class DeltaVolSurfacePoint:
    def __init__(self, spot, tenor, rd, rf, delta_vols):
        """
        spot: spot FX rate
        tenor: time to expiry in years
        rd: domestic interest rate
        rf: foreign interest rate
        delta_vols: dict like {"5P": 0.135, "25P": 0.115, "ATM": 0.10, "25C": 0.108, "5C": 0.127}
        """
        self.S = spot
        self.T = tenor
        self.rd = rd
        self.rf = rf
        self.F = spot * np.exp((rd - rf) * tenor)
        self.delta_vols = delta_vols

    def _delta_bs(self, K, sigma, option_type):
        """Premium-adjusted Black-Scholes delta for FX options."""
        F = self.F
        T = self.T
        d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))
        if option_type == 'call':
            return np.exp(-self.rf * T) * norm.cdf(d1)
        elif option_type == 'put':
            return -np.exp(-self.rf * T) * norm.cdf(-d1)

    def delta_to_strike(self, delta_target, sigma, option_type):
        """Invert delta to get strike using Brent's method."""
        F = self.F
        T = self.T

        def func(K):
            return self._delta_bs(K, sigma, option_type) - delta_target

        # Try progressively wider bounds until we bracket the root
        for factor in [0.4, 0.3, 0.2, 0.1]:
            try:
                return brentq(func, (1 - factor) * F, (1 + factor) * F)
            except ValueError:
                continue  # Try wider interval

        # If we still fail:
        raise ValueError(f"Could not find strike for delta={delta_target}, vol={sigma}, type={option_type}")


    def get_strikes(self):
        """Return a dict of strikes corresponding to each delta label."""
        strikes = {}

        for label, vol in self.delta_vols.items():
            if label == "ATM":
                strikes[label] = self.F  # ATM strike = forward
                continue

            if label.endswith("C"):
                delta = float(label[:-1]) / 100
                option_type = 'call'
            elif label.endswith("P"):
                delta = -float(label[:-1]) / 100
                option_type = 'put'
            else:
                raise ValueError(f"Unknown delta label: {label}")

            try:
                K = self.delta_to_strike(delta, vol, option_type)
                strikes[label] = K
            except ValueError as e:
                print(f"Failed to invert delta {label} with vol {vol}: {e}")
                strikes[label] = None  # or raise, or np.nan

        return strikes


if __name__ == "__main__":
    surface = DeltaVolSurfacePoint(
        spot=1.00,
        tenor=1 / 12,
        rd=0.05,
        rf=0.03,
        delta_vols={
            "5P": 0.135,
            "25P": 0.115,
            "ATM": 0.10,
            "25C": 0.108,
            "5C": 0.127
        }
    )
    print(surface.get_strikes())
