"""
仮想音楽市場シミュレーションエンジン

Salganik et al. (2006) の MusicLab 実験を再現するためのエージェント・ベース・モデル。

主なポイント:
- 1人ずつエージェントが到着し、曲リストを見る
- 「独立条件 (Independent)」: 他者のダウンロード数を見ない。純粋に品質で選ぶ。
- 「社会的影響条件 (Social influence)」: 他者のダウンロード数を見て影響を受ける。
- 社会的影響条件は 8 つの並列ワールドで独立に進行する。
- 実験1: 曲は 16x3 グリッドのランダム配置 (社会的シグナル = ダウンロード数表示のみ)
- 実験2: 曲は1列でダウンロード数順にソート表示 (社会的シグナルが強い)

各エージェントの行動:
  1) 曲リストから L 曲を「聴く」(listen)
     - 実験1: ランダムに L 曲選ぶ
     - 実験2 (社会的影響): ダウンロード数の多い曲ほど聴かれやすい (人気順表示の効果)
     - 独立条件: ランダムに L 曲選ぶ
  2) 各曲について「ダウンロードするか」を確率的に決定
     - p(download | listen) = sigmoid(α * (quality - q0) + β * log(1 + downloads))
     - 独立条件では β = 0
     - 実験1 と 実験2 で β の値を変える (実験2 の方が大きい = 強い社会的シグナル)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from data.songs import Song


@dataclass
class SimConfig:
    """シミュレーション設定"""
    n_agents: int = 700                  # 1ワールドあたりのエージェント数
    n_worlds: int = 8                    # 社会的影響条件の並列ワールド数
    listens_per_agent_mean: float = 3.5  # 1エージェントが聴く曲数の平均
    quality_weight: float = 1.4          # α: 品質の重み
    quality_center: float = 3.0          # q0: 品質の中央値
    social_weight_exp1: float = 0.45     # 実験1の社会的影響強度 β
    social_weight_exp2: float = 1.10     # 実験2の社会的影響強度 β (より強い)
    listen_bias_exp1: float = 0.35       # 実験1: DL数表示による軽いリスニング偏り
    listen_bias_exp2: float = 1.20       # 実験2: 人気順表示による強いリスニング偏り
    experiment: int = 1                  # 1 or 2
    seed: int = 0                        # 乱数シード


@dataclass
class WorldState:
    """1つのワールドの状態 (独立条件は1ワールド、社会的影響条件は8ワールド)"""
    name: str
    is_social: bool
    downloads: np.ndarray  # shape=(n_songs,), int
    listens: np.ndarray    # shape=(n_songs,), int
    # ダウンロード数の時間推移 (各エージェント後のスナップショット)
    history: List[np.ndarray] = field(default_factory=list)

    def snapshot(self) -> None:
        self.history.append(self.downloads.copy())


def _sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-x))


def _choose_listens(
    rng: np.random.Generator,
    downloads: np.ndarray,
    n_songs: int,
    n_listen: int,
    listen_bias: float,
) -> np.ndarray:
    """
    エージェントが聴く曲を選ぶ。
    listen_bias > 0 だと「ダウンロード数の多い曲ほど聴かれやすい」(=人気順表示の効果)。
    """
    if listen_bias <= 0:
        # 単純なランダム選択
        return rng.choice(n_songs, size=min(n_listen, n_songs), replace=False)

    # 人気順表示の場合: ダウンロード数が多い曲を選びやすい
    weights = np.power(downloads + 1.0, listen_bias)
    weights = weights / weights.sum()
    n_listen = min(n_listen, n_songs)
    return rng.choice(n_songs, size=n_listen, replace=False, p=weights)


def _download_probability(
    quality: np.ndarray,
    downloads: np.ndarray,
    quality_weight: float,
    quality_center: float,
    social_weight: float,
) -> np.ndarray:
    """ダウンロード確率を計算: sigmoid(α*(q - q0) + β*log(1 + d))"""
    logit = quality_weight * (quality - quality_center) + social_weight * np.log1p(downloads)
    return _sigmoid(logit)


def run_world(
    songs: List[Song],
    config: SimConfig,
    is_social: bool,
    world_seed: int,
    snapshot_every: int = 10,
) -> WorldState:
    """単一ワールドのシミュレーションを実行"""
    rng = np.random.default_rng(world_seed)
    n_songs = len(songs)
    qualities = np.array([s.true_quality for s in songs], dtype=float)

    state = WorldState(
        name="social" if is_social else "independent",
        is_social=is_social,
        downloads=np.zeros(n_songs, dtype=int),
        listens=np.zeros(n_songs, dtype=int),
    )

    # 実験条件に応じて社会的影響の強度を決める
    if not is_social:
        social_weight = 0.0
        listen_bias = 0.0
    else:
        if config.experiment == 1:
            social_weight = config.social_weight_exp1
            listen_bias = config.listen_bias_exp1  # 実験1: 軽い偏り
        else:
            social_weight = config.social_weight_exp2
            listen_bias = config.listen_bias_exp2  # 実験2は強い人気順表示

    for agent_idx in range(config.n_agents):
        # 1エージェントが聴く曲数 (ポアソン分布、最低1曲)
        n_listen = max(1, rng.poisson(config.listens_per_agent_mean))
        listen_ids = _choose_listens(
            rng, state.downloads, n_songs, n_listen, listen_bias
        )

        for sid in listen_ids:
            state.listens[sid] += 1
            p_dl = _download_probability(
                qualities[sid],
                state.downloads[sid],
                config.quality_weight,
                config.quality_center,
                social_weight,
            )
            if rng.random() < p_dl:
                state.downloads[sid] += 1

        if (agent_idx + 1) % snapshot_every == 0:
            state.snapshot()

    # 最終スナップショット
    state.snapshot()
    return state


@dataclass
class SimResult:
    """シミュレーション結果一式"""
    songs: List[Song]
    config: SimConfig
    independent: WorldState
    social_worlds: List[WorldState]

    @property
    def n_songs(self) -> int:
        return len(self.songs)

    def market_shares(self, world: WorldState) -> np.ndarray:
        total = world.downloads.sum()
        if total == 0:
            return np.zeros_like(world.downloads, dtype=float)
        return world.downloads / total


def run_experiment(songs: List[Song], config: SimConfig) -> SimResult:
    """
    実験全体を実行する。
    - 1つの独立条件ワールド (subject 2倍 = n_agents * 2)
    - 8つの社会的影響ワールド
    """
    base = config.seed
    # 独立条件は subjects 2倍にする (論文の設計通り)
    indep_config = SimConfig(**{**config.__dict__, "n_agents": config.n_agents * 2})
    independent = run_world(
        songs, indep_config, is_social=False, world_seed=base + 9999
    )

    social_worlds: List[WorldState] = []
    for w in range(config.n_worlds):
        ws = run_world(songs, config, is_social=True, world_seed=base + w + 1)
        ws.name = f"world_{w + 1}"
        social_worlds.append(ws)

    return SimResult(
        songs=songs,
        config=config,
        independent=independent,
        social_worlds=social_worlds,
    )
