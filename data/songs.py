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
    ("52metro", "Lockdown"),
    ("A Blinding Silence", "Miseries and Miracles"),
    ("Art of Kanly", "Seductive Intro, Melodic Breakdown"),
    ("Beerbong", "Father to Son"),
    ("Benefit of a Doubt", "Run Away"),
    ("By November", "If I Could Take You"),
    ("Cape Renewal", "Baseball Warlock v1"),
    ("Dante", "Life's Mystery"),
    ("Deep Enough to Die", "For the Sky"),
    ("Drawn in the Sky", "Tap the Ride"),
    ("Ember Sky", "This Upcoming Winter"),
    ("Evan Gold", "Robert Downey Jr."),
    ("Fading Through", "Wish me Luck"),
    ("Far from Known", "Route 9"),
    ("Forthfading", "Fear"),
    ("Go Mordecai", "It Does What Its Told"),
    ("Hall of Fame", "Best Mistakes"),
    ("Hartsfield", "Enough is Enough"),
    ("Hydraulic Sandwich", "Separation Anxiety"),
    ("Miss October", "Pink Aggression"),
    ("Moral Hazard", "Waste of my Life"),
    ("Nooner at Nine", "Walk Away"),
    ("Not for Scholars", "As Seasons Change"),
    ("Parker Theory", "She Said"),
    ("Post Break Tragedy", "Florence"),
    ("Ryan Essmaker", "Detour (Be Still)"),
    ("Salute the Dawn", "I am Error"),
    ("Secretary", "Keep Your Eyes on the Ballistics"),
    ("Selsius", "Stars of the City"),
    ("Shipwreck Union", "Out of the Woods"),
    ("Sibrian", "Eye Patch"),
    ("Silent Film", "All I have to Say"),
    ("Silverfox", "Gnaw"),
    ("Simply Waiting", "Went with the Count"),
    ("Star Climber", "Tell Me"),
    ("Stranger", "One Drop"),
    ("Stunt Monkey", "Inside Out"),
    ("Sum Rana", "The Bolshevik Boogie"),
    ("Summerswasted", "A Plan Behind Destruction"),
    ("The Broken Promise", "The End in Friend"),
    ("The Calefaction", "Trapped in an Orange Peel"),
    ("The Fastlane", "Til Death do us Part (I don't)"),
    ("The Thrift Syndicate", "2003 a Tragedy"),
    ("This New Dawn", "The Belief Above the Answer"),
    ("Undo", "While the World Passes"),
    ("Unknown Citizens", "Falling Over"),
    ("Up Falls Down", "A Brighter Burning Star"),
    ("Up for Nothing", "In Sight Of"),
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
