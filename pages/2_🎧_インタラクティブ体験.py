"""
インタラクティブ体験ページ

ユーザー自身が音楽市場に「参加」して、曲を選びダウンロードする体験版。

体験モード:
- 独立条件: ダウンロード数を見ずに曲を選ぶ
- 社会的影響条件: ダウンロード数 (= 過去にプレイした自分+仮想エージェントの合計) を見て選ぶ
  - 実験1スタイル: 3列グリッド・ランダム順
  - 実験2スタイル: 1列・人気順
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data import generate_songs


st.set_page_config(page_title="インタラクティブ体験", page_icon="🎧", layout="wide")
st.title("🎧 インタラクティブ体験")
st.caption(
    "あなた自身が仮想音楽市場の参加者になります。"
    "曲を聴き、☆評価をつけ、ダウンロードするかを決めてください。"
)


# ---------- セッション初期化 ----------
def _init_session() -> None:
    if "interactive_inited" in st.session_state:
        return
    songs = generate_songs(seed=42)
    rng = np.random.default_rng(0)
    n = len(songs)

    # 「過去のエージェント」が既に200人分くらい行動した状態から始める
    initial_downloads = np.zeros(n, dtype=int)
    qualities = np.array([s.true_quality for s in songs])
    # 品質に応じてある程度ダウンロード数を分布させる + ノイズ
    base = np.exp(qualities - 3.0) * 8.0
    initial_downloads = rng.poisson(np.clip(base, 0.5, None)).astype(int)

    st.session_state.interactive_inited = True
    st.session_state.songs = songs
    st.session_state.downloads_independent = initial_downloads.copy()
    st.session_state.downloads_social = initial_downloads.copy()
    st.session_state.my_downloads_indep: list[int] = []
    st.session_state.my_downloads_social: list[int] = []
    st.session_state.my_ratings: dict[int, int] = {}
    st.session_state.playing_song_id: int | None = None
    # ランダム順 (実験1の3列グリッド再現用) を保持
    perm = rng.permutation(n)
    st.session_state.random_order = perm.tolist()


_init_session()
songs = st.session_state.songs

# ---------- 表示モード切り替え ----------
mode = st.radio(
    "あなたが置かれる「条件」",
    options=["independent", "social_exp1", "social_exp2"],
    format_func=lambda m: {
        "independent": "🟢 独立条件 (ダウンロード数を見ない)",
        "social_exp1": "🟣 社会的影響: 実験1 (ランダム配置・DL数表示)",
        "social_exp2": "🔴 社会的影響: 実験2 (人気順・DL数表示)",
    }[m],
    horizontal=True,
)

if mode == "independent":
    downloads = st.session_state.downloads_independent
    show_counts = False
    sort_by_popularity = False
    grid_random = True
elif mode == "social_exp1":
    downloads = st.session_state.downloads_social
    show_counts = True
    sort_by_popularity = False
    grid_random = True
else:
    downloads = st.session_state.downloads_social
    show_counts = True
    sort_by_popularity = True
    grid_random = False


col_left, col_right = st.columns([3, 1])

with col_right:
    st.subheader("📈 あなたの参加状況")
    indep_count = len(st.session_state.my_downloads_indep)
    social_count = len(st.session_state.my_downloads_social)
    st.metric("独立条件でDLした曲数", indep_count)
    st.metric("社会的影響条件でDLした曲数", social_count)
    rated = len(st.session_state.my_ratings)
    st.metric("評価した曲数", rated)

    if st.button("🔄 リセット", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k.startswith("interactive_") or k in {
                "songs", "downloads_independent", "downloads_social",
                "my_downloads_indep", "my_downloads_social",
                "my_ratings", "playing_song_id", "random_order"
            }:
                del st.session_state[k]
        st.rerun()


# ---------- 表示順の決定 ----------
if sort_by_popularity:
    order = np.argsort(-downloads).tolist()
elif grid_random:
    order = st.session_state.random_order
else:
    order = list(range(len(songs)))

with col_left:
    st.subheader("🎵 曲リスト")
    st.caption(
        "曲名をクリックして「聴く」と、☆評価とダウンロード判断ができます。"
    )

    if mode == "social_exp1":
        # 3列グリッド
        cols = st.columns(3)
        for idx, sid in enumerate(order):
            with cols[idx % 3]:
                song = songs[sid]
                label = f"**{song.band}**\n*「{song.title}」*"
                if show_counts:
                    label += f"  \n🎧 DL数: `{int(downloads[sid])}`"
                if st.button(label, key=f"play_{sid}", use_container_width=True):
                    st.session_state.playing_song_id = sid
    else:
        # 1列表示 (独立条件・実験2スタイル)
        for sid in order:
            song = songs[sid]
            c1, c2, c3 = st.columns([5, 2, 1.2])
            with c1:
                st.write(f"**{song.band}** — *{song.title}*")
            with c2:
                if show_counts:
                    st.write(f"🎧 `{int(downloads[sid])}` DL")
                else:
                    st.write("　")
            with c3:
                if st.button("▶ 聴く", key=f"play_{sid}"):
                    st.session_state.playing_song_id = sid


# ---------- 再生・ダウンロードダイアログ ----------
playing = st.session_state.playing_song_id
if playing is not None:
    song = songs[playing]
    st.divider()
    st.subheader(f"🎶 再生中: {song.band} — {song.title}")
    st.caption(
        "※ ダミーデータなので実際の音声はありません。"
        " 1〜5 の☆で評価して、ダウンロードするか決めてください。"
    )

    current_rating = st.session_state.my_ratings.get(playing, 3)
    rating = st.slider(
        "☆ あなたの評価",
        min_value=1, max_value=5, value=current_rating,
        help="1=I hate it, 5=I love it (論文の星評価と同じスケール)"
    )
    st.session_state.my_ratings[playing] = int(rating)

    # 「真の品質」をネタバラシ的にうっすら表示しない (ユーザーが知らないように)
    cdl, cclose = st.columns([1, 1])
    if cdl.button("⬇️ ダウンロードする", type="primary", use_container_width=True):
        if mode == "independent":
            st.session_state.downloads_independent[playing] += 1
            st.session_state.my_downloads_indep.append(playing)
        else:
            st.session_state.downloads_social[playing] += 1
            st.session_state.my_downloads_social.append(playing)
        st.session_state.playing_song_id = None
        st.success(f"✅ 「{song.title}」をダウンロードしました")
        st.rerun()
    if cclose.button("✖️ ダウンロードしない", use_container_width=True):
        st.session_state.playing_song_id = None
        st.rerun()


# ---------- あなたが評価した曲のサマリー ----------
st.divider()
with st.expander("📝 あなたが評価した曲一覧", expanded=False):
    if st.session_state.my_ratings:
        rows = []
        for sid, r in st.session_state.my_ratings.items():
            s = songs[sid]
            rows.append({
                "曲": f"{s.band} - {s.title}",
                "評価 (☆)": r,
                "真の品質": round(s.true_quality, 2),
                "現在の DL数 (独立)":
                    int(st.session_state.downloads_independent[sid]),
                "現在の DL数 (社会的影響)":
                    int(st.session_state.downloads_social[sid]),
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("まだ曲を評価していません。")
