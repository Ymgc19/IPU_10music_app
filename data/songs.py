"""
仮想音楽市場 - 楽曲ダミーデータ
Salganik, Dodds & Watts (2006) "Experimental Study of Inequality and
Unpredictability in an Artificial Cultural Market" Science 311, 854 を参照。

論文と同じく 48 曲を用意する。
各曲には「真の品質 (true_quality)」を 1〜5 のスコアで割り当てる。
これは「独立条件 (Independent condition) で観察される平均ダウンロード率」に
相当するもので、エージェント・シミュレーションのベースとなる。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass(frozen=True)
class Song:
    song_id: int
    band: str
    title: str
    true_quality: float  # 1.0〜5.0 (5に近いほど高品質)


# Salganik et al. (2006) 論文の Table S3 から取った 48 曲。
# 実音源は使わずダミーとして使用する。
_SONGS_RAW: List[tuple[str, str]] = [
    ("RED LINE", "アンジュルム"),
    ("46億年LOVE", "アンジュルム"),
    ("アンドロイドは夢を見るか", "アンジュルム"),
    ("マナーモード", "アンジュルム"),
    ("愛されルート A or B?", "アンジュルム"),
    ("赤いイヤホン", "アンジュルム"),
    ("大器晩成", "アンジュルム"),
    ("アイノケダモノ", "アンジュルム"),
    ("光のうた", "アンジュルム"),
    ("Celebtate! Celeblate!", "アンジュルム"),
    ("美々たる一撃", "アンジュルム"),
    ("プリズンブレイカー", "アンジュルム"),
    ("悔しいわ", "アンジュルム"),
    ("次々続々", "アンジュルム"),
    ("愛・魔性", "アンジュルム"),
    ("泳げないMermaid", "アンジュルム"),
    ("トラブルメーカー", "アンジュルム"),
    ("人生、すなわち、パンタレイ", "アンジュルム"),
    ("初恋、花冷え", "アンジュルム"),
    ("臥薪嘗胆", "アンジュルム"),
    ("限りあるMoment", "アンジュルム"),
    ("私を創るのは私", "アンジュルム"),
    ("七転び八起き", "アンジュルム"),
    ("はっきりしようぜ", "アンジュルム"),
    ("ドンデンガエシ", "アンジュルム"),
    ("タデ食う虫もLike it!", "アンジュルム"),
    ("恋はアッチャアッチャ", "アンジュルム"),
    ("愛すべきべき Human Life", "アンジュルム"),
    ("愛のため今日まで進化してきた人間 愛のためすべて退化してきた人間", "アンジュルム"),
    ("カクゴして !", "アンジュルム"),
    ("ハデにやっちゃいな !", "アンジュルム"),
    ("うわさのナルシー", "アンジュルム"),
    ("泣けないぜ・・・共感詐欺", "アンジュルム"),
    ("夏将軍", "アンジュルム"),
    ("明晩、ギャラクシー劇場で", "アンジュルム"),
    ("出すぎた杭は打たれない", "アンジュルム"),
    ("もう一歩", "アンジュルム"),
    ("悠々閑々 gonna be alright!!", "アンジュルム"),
    ("23時のペルソナ", "アンジュルム"),
    ("忘れてあげる", "アンジュルム"),
    ("FAST PASS", "アンジュルム"),
    ("いとし いとしと Say My Heart", "アンジュルム"),
    ("友よ", "アンジュルム"),
    ("THANK YOU，HELLO GOOD BYE", "アンジュルム"),
    ("キソクタダシクウツクシク", "アンジュルム"),
    ("乙女の逆襲", "アンジュルム"),
    ("Survive～生きてく為に夢を見んだ", "アンジュルム"),
    ("全然起き上がれないSUNDAY", "アンジュルム"),
]


def generate_songs(seed: int = 42) -> List[Song]:
    """
    48曲の Song リストを生成する。

    真の品質 (true_quality) は再現性確保のため固定シードで生成する。
    分布は 1.0〜5.0 のベータ分布ライクな形で、ほどよくばらつきを持たせる。
    """
    rng = np.random.default_rng(seed)
    n = len(_SONGS_RAW)

    # ベータ分布で品質に偏りを持たせる (中程度の品質の曲が多い)
    raw = rng.beta(a=2.5, b=2.5, size=n)
    # 1.0〜5.0 にスケーリング
    qualities = 1.0 + raw * 4.0

    songs = [
        Song(song_id=i, band=band, title=title, true_quality=float(q))
        for i, ((band, title), q) in enumerate(zip(_SONGS_RAW, qualities))
    ]
    return songs


def songs_to_dataframe(songs: List[Song]):
    import pandas as pd
    return pd.DataFrame(
        [
            {
                "song_id": s.song_id,
                "band": s.band,
                "title": s.title,
                "true_quality": round(s.true_quality, 3),
            }
            for s in songs
        ]
    )
