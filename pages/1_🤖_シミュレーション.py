"""
シミュレーションページ

設定したパラメータでエージェント・ベース・シミュレーションを実行し、
独立条件と 8 並列ワールドのダウンロード結果を表示する。
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# 親ディレクトリ (リポジトリルート) を import パスに追加
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data import generate_songs, songs_to_dataframe
from sim import SimConfig, run_experiment
from sim.metrics import (
    gini_coefficient,
    gini_per_world,
    market_share,
    unpredictability_summary,
)

st.set_page_config(page_title="シミュレーション", page_icon="🤖", layout="wide")
st.title("🤖 シミュレーション")
st.caption("仮想エージェントが大量に行動し、Salganik et al. (2006) の実験を再現します")

# ---------- サイドバー: パラメータ設定 ----------
with st.sidebar:
    st.header("⚙️ シミュレーション設定")

    experiment = st.radio(
        "実験デザイン",
        options=[1, 2],
        format_func=lambda x: f"実験 {x}: " + (
            "ランダム配置 (弱い社会的シグナル)" if x == 1
            else "人気順表示 (強い社会的シグナル)"
        ),
        index=0,
        help="実験1: 曲はランダム配置・ダウンロード数のみ表示。"
        "実験2: 曲はダウンロード数順に並べ替えて表示 (人気順)。",
    )

    n_agents = st.slider("1ワールドあたりのエージェント数", 100, 2000, 700, step=100)
    n_worlds = st.slider("社会的影響条件の並列ワールド数", 2, 8, 8, step=1)
    listens = st.slider("1エージェントの平均リスニング数", 1.0, 8.0, 3.5, step=0.5)

    st.divider()
    st.subheader("行動モデル")
    quality_weight = st.slider(
        "品質の重み α", 0.1, 3.0, 1.4, step=0.1,
        help="曲の品質がダウンロード確率に影響する強さ"
    )
    social_weight = st.slider(
        "社会的影響の強さ β", 0.0, 2.0,
        0.55 if experiment == 1 else 1.10, step=0.05,
        help="他人のダウンロード数がダウンロード確率に影響する強さ"
    )
    seed = st.number_input("乱数シード", min_value=0, max_value=9999, value=42, step=1)

    run = st.button("🚀 シミュレーション実行", type="primary", use_container_width=True)


# ---------- セッション状態 ----------
if "sim_result" not in st.session_state:
    st.session_state.sim_result = None

# ---------- 実行 ----------
if run:
    songs = generate_songs(seed=int(seed))
    config = SimConfig(
        n_agents=int(n_agents),
        n_worlds=int(n_worlds),
        listens_per_agent_mean=float(listens),
        quality_weight=float(quality_weight),
        social_weight_exp1=float(social_weight) if experiment == 1 else 0.35,
        social_weight_exp2=float(social_weight) if experiment == 2 else 0.90,
        experiment=int(experiment),
        seed=int(seed),
    )

    with st.spinner(f"エージェント {n_agents * (n_worlds + 2)} 人ぶんを処理中..."):
        result = run_experiment(songs, config)

    st.session_state.sim_result = result
    st.success("✅ シミュレーション完了！")


# ---------- 結果表示 ----------
result = st.session_state.sim_result

if result is None:
    st.info("👈 左のサイドバーで設定して、「シミュレーション実行」を押してください。")
    st.subheader("曲リスト (ダミーデータ・48曲)")
    st.dataframe(
        songs_to_dataframe(generate_songs(seed=42)),
        use_container_width=True, hide_index=True,
    )
    st.stop()


# ---------- メトリクス概要 ----------
st.subheader("📊 結果サマリー")

gini_info = gini_per_world(result)
u_info = unpredictability_summary(result)

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Gini (独立条件)",
    f"{gini_info['independent_mean']:.3f}",
    help="完全平等=0, 完全不平等=1"
)
col2.metric(
    "Gini (社会的影響, 平均)",
    f"{np.mean(gini_info['social_worlds']):.3f}",
    delta=f"{np.mean(gini_info['social_worlds']) - gini_info['independent_mean']:+.3f}",
)
col3.metric("Unpredictability U (独立)", f"{u_info['independent']:.4f}")
col4.metric(
    "Unpredictability U (社会的影響)",
    f"{u_info['social']:.4f}",
    delta=f"{u_info['social'] - u_info['independent']:+.4f}",
)

st.divider()


# ---------- ワールド別ダウンロード結果 ----------
tab_table, tab_top, tab_rank = st.tabs(
    ["🌍 全ワールドの結果", "🏆 各ワールドの TOP10", "🎯 品質 vs 成功"]
)

with tab_table:
    rows = []
    for s in result.songs:
        row = {
            "song_id": s.song_id,
            "曲名": f"{s.band} - {s.title}",
            "品質": round(s.true_quality, 2),
            "独立条件 DL": int(result.independent.downloads[s.song_id]),
        }
        for i, ws in enumerate(result.social_worlds):
            row[f"W{i + 1}"] = int(ws.downloads[s.song_id])
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("独立条件 DL", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True, height=480)

with tab_top:
    n_worlds_real = len(result.social_worlds)
    cols = st.columns(min(4, n_worlds_real + 1))
    # 独立条件
    with cols[0]:
        st.markdown("**🟢 独立条件 (Independent)**")
        order = np.argsort(-result.independent.downloads)[:10]
        for rank, sid in enumerate(order, start=1):
            song = result.songs[sid]
            st.write(
                f"{rank}. **{song.band}** — {song.title}  "
                f"`{int(result.independent.downloads[sid])} DL`"
            )

    # 各社会的影響ワールド (横並び。多すぎる場合はexpander)
    if n_worlds_real <= 3:
        for i, ws in enumerate(result.social_worlds):
            with cols[i + 1]:
                st.markdown(f"**🟣 World {i + 1} (Social)**")
                order = np.argsort(-ws.downloads)[:10]
                for rank, sid in enumerate(order, start=1):
                    song = result.songs[sid]
                    st.write(
                        f"{rank}. **{song.band}** — {song.title}  "
                        f"`{int(ws.downloads[sid])} DL`"
                    )
    else:
        st.markdown("---")
        st.markdown("**🟣 社会的影響条件の8ワールド TOP10**")
        wcols = st.columns(4)
        for i, ws in enumerate(result.social_worlds):
            with wcols[i % 4]:
                with st.expander(f"World {i + 1}", expanded=(i < 4)):
                    order = np.argsort(-ws.downloads)[:10]
                    for rank, sid in enumerate(order, start=1):
                        song = result.songs[sid]
                        st.write(
                            f"{rank}. {song.band[:18]}"
                            f" `{int(ws.downloads[sid])}DL`"
                        )

with tab_rank:
    st.markdown(
        "横軸=独立条件での市場シェア (= 品質)、縦軸=各ワールドでの市場シェア。"
        "**点線**は y=x (完全に品質どおり)。"
    )
    indep_share = market_share(result.independent.downloads)
    import altair as alt

    chart_rows = []
    for sid in range(result.n_songs):
        for i, ws in enumerate(result.social_worlds):
            chart_rows.append({
                "song_id": sid,
                "曲": f"{result.songs[sid].band} - {result.songs[sid].title}",
                "m_indep": indep_share[sid],
                "m_world": market_share(ws.downloads)[sid],
                "world": f"W{i + 1}",
            })
    chart_df = pd.DataFrame(chart_rows)

    base = alt.Chart(chart_df).mark_circle(size=60, opacity=0.55).encode(
        x=alt.X("m_indep:Q", title="独立条件の市場シェア (≒ 品質)"),
        y=alt.Y("m_world:Q", title="社会的影響条件 各ワールドの市場シェア"),
        color=alt.Color("world:N", legend=alt.Legend(title="ワールド")),
        tooltip=["曲", "world", "m_indep", "m_world"],
    )

    max_val = float(max(chart_df["m_indep"].max(), chart_df["m_world"].max()) * 1.05)
    line = alt.Chart(pd.DataFrame({"x": [0, max_val], "y": [0, max_val]})).mark_line(
        strokeDash=[4, 4], color="gray"
    ).encode(x="x:Q", y="y:Q")

    st.altair_chart((base + line).properties(height=480), use_container_width=True)
