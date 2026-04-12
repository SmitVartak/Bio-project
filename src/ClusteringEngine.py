# src/ClusteringEngine.py
# Implements the Lumer & Faieta (1994) pickup / drop probability formulas.
# This is the mathematical heart of the ant colony sorting algorithm.

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


class ClusteringEngine:
    """
    Stateless utility class — all methods are static / class methods.
    The Environment is passed in at each call so this class owns no mutable state.

    Core formulas
    -------------
    f(i)  =  max(0,  (1/|N|) * sum_{j in N}  [1 - d(oi, oj) / alpha])
    Pp(i) =  (K1 / (K1 + f(i)))^2
    Pd(i) =  2*f(i)   if f(i) < K2
             1         otherwise
    """

    @staticmethod
    def euclidean(v1: np.ndarray, v2: np.ndarray) -> float:
        """Fast Euclidean distance between two feature vectors."""
        return float(np.linalg.norm(v1 - v2))

    @classmethod
    def similarity(cls, item_id: int, gx: int, gy: int, env) -> float:
        """
        Compute f(i) — the local similarity density of item_id
        relative to its neighbours at grid position (gx, gy).

        Parameters
        ----------
        item_id : int   The item whose similarity is being evaluated.
        gx, gy  : int   The grid position to evaluate around
                         (may differ from the item's actual position when
                         an ant is scouting a drop location).
        env     : Environment

        Returns
        -------
        f_val : float in [0, 1]
        """
        neighbours = env.get_neighbourhood_items(gx, gy, r=config.NEIGHBORHOOD_R)

        if len(neighbours) == 0:
            return 0.0

        vi = env.features[item_id]
        total = 0.0
        for j in neighbours:
            vj = env.features[j]
            dist = cls.euclidean(vi, vj)
            contribution = 1.0 - dist / config.ALPHA
            total += contribution

        f_val = total / len(neighbours)
        return max(0.0, f_val)

    @staticmethod
    def pickup_prob(f_val: float) -> float:
        """
        P_p = (K1 / (K1 + f))^2
        High f → low pickup probability (ant leaves well-grouped items alone).
        Low  f → high pickup probability (ant picks up isolated vagabonds).
        """
        return (config.K1 / (config.K1 + f_val)) ** 2

    @staticmethod
    def drop_prob(f_val: float) -> float:
        """
        P_d = 2*f  if f < K2
              1     otherwise
        High f → ant is likely to drop (it found a matching neighbourhood).
        Low  f → ant keeps wandering (bad neighbourhood).
        """
        if f_val < config.K2:
            return 2.0 * f_val
        return 1.0

    @classmethod
    def should_pickup(cls, item_id: int, gx: int, gy: int, env) -> bool:
        """Roll the dice for a pickup event. Returns True if the ant picks up."""
        f_val = cls.similarity(item_id, gx, gy, env)
        prob  = cls.pickup_prob(f_val)
        return np.random.random() < prob

    @classmethod
    def should_drop(cls, item_id: int, gx: int, gy: int, env) -> bool:
        """Roll the dice for a drop event. Returns True if the ant drops."""
        f_val = cls.similarity(item_id, gx, gy, env)
        prob  = cls.drop_prob(f_val)
        return np.random.random() < prob
