"""
分析指標の計算

Salganik et al. (2006) で使われた指標:
- Gini coefficient G : 市場シェアの不平等度 (0=完全平等, 1=完全不平等)
- Unpredictability U : 並列ワールド間の市場シェアの差の平均
- ランキング推移         : ダウンロード数の時系列推移
"""

from __future__ import annotations

from itertools import combinations
from typing import List

import numpy as np

from .engine import SimResult, WorldState


def market_share(downloads: np.ndarray) -> np.ndarray:
    """ダウンロード数ベクトルから市場シェア (mi) を計算"""
    total = downloads.sum()
    if total == 0:
        return np.zeros_like(downloads, dtype=float)
    return downloads.astype(float) / total


def gini_coefficient(values: np.ndarray) -> float:
    """
    Gini 係数を計算する。
    G = (1/S^2 * ΣΣ|mi - mj|) / (2 * Σmk / S)
       = ΣΣ|mi - mj| / (2 * S * Σmk)
    値域: 0 (完全平等) ～ 1 (完全不平等)
    """
    values = np.asarray(values, dtype=float)
    s = values.size
    total = values.sum()
    if s == 0 or total == 0:
        return 0.0
    diffs = np.abs(values[:, None] - values[None, :])
    return float(diffs.sum() / (2.0 * s * total))


def unpredictability(world_shares: List[np.ndarray]) -> float:
    """
    Unpredictability U を計算する。
    U = (1/S) * Σi  ui
    ui = (1 / C(W,2)) * Σ_{j<k} |mi,j - mi,k|

    world_shares: 各ワールドの市場シェアベクトル (list of np.ndarray)
    """
    w = len(world_shares)
    if w < 2:
        return 0.0
    shares = np.stack(world_shares, axis=0)  # shape=(W, S)
    s = shares.shape[1]

    pair_diffs = []
    for j, k in combinations(range(w), 2):
        pair_diffs.append(np.abs(shares[j] - shares[k]))
    pair_diffs = np.stack(pair_diffs, axis=0)  # shape=(C(W,2), S)
    u_i = pair_diffs.mean(axis=0)  # shape=(S,)
    return float(u_i.mean())


def unpredictability_independent(
    independent: WorldState, n_splits: int = 200, seed: int = 0
) -> float:
    """
    独立条件の Unpredictability を測る。
    独立条件は1ワールドしかないため、エージェントをランダムに2分割して
    その2つの「サブワールド」間の市場シェア差を計算し、何度も繰り返した平均を取る。
    """
    # 簡易版: ダウンロード数を二項分布で2分割 (各ダウンロードを 1/2 確率で振り分け)
    rng = np.random.default_rng(seed)
    n_songs = independent.downloads.size
    results = []
    for _ in range(n_splits):
        a = rng.binomial(independent.downloads, 0.5)
        b = independent.downloads - a
        sa = market_share(a)
        sb = market_share(b)
        results.append(np.abs(sa - sb).mean())
    return float(np.mean(results))


def gini_independent_replicates(
    independent: WorldState, n_splits: int = 200, seed: int = 0
) -> List[float]:
    """
    独立条件の Gini を 2分割 → 片方の Gini で複数回計算する。
    社会的影響条件の各ワールド (約半数のサブジェクト数) と比較するための処理。
    """
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_splits):
        a = rng.binomial(independent.downloads, 0.5)
        out.append(gini_coefficient(market_share(a)))
    return out


def gini_per_world(result: SimResult) -> dict:
    """各ワールドの Gini 係数を計算して dict で返す"""
    indep_replicates = gini_independent_replicates(result.independent)
    return {
        "independent_mean": float(np.mean(indep_replicates)),
        "independent_replicates": indep_replicates,
        "social_worlds": [
            gini_coefficient(market_share(w.downloads)) for w in result.social_worlds
        ],
    }


def unpredictability_summary(result: SimResult) -> dict:
    """Unpredictability U を計算してまとめる"""
    social_shares = [market_share(w.downloads) for w in result.social_worlds]
    u_social = unpredictability(social_shares)
    u_indep = unpredictability_independent(result.independent)
    return {
        "social": u_social,
        "independent": u_indep,
    }


def rankings(downloads: np.ndarray) -> np.ndarray:
    """ダウンロード数 → 順位 (1位=最多ダウンロード)"""
    order = np.argsort(-downloads, kind="stable")
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(downloads) + 1)
    return ranks
