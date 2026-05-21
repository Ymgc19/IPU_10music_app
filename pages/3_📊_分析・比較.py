"""
分析・比較ページ

シミュレーション結果から、Gini 係数 / Unpredictability U / リアルタイムランキング
を可視化する。論文の Fig. 1, Fig. 2 に相当する図を生成する。
"""

from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data import generate_songs
from sim import SimConfig, run_experiment
from sim.metrics import (
    gini_coefficient,
    gini_per_world,
    market_share,
    unpredictability,
    unpredictability_independent,
)

st.set_page_config(page_title="分析・比較", page_icon="📊", layout="wide")
st.title("📊 分析・比較")
st.caption(
    "論文 Fig. 1 (Gini 係数) / Fig. 2 (Unpredictability) / "
    "ランキング推移を可視化します"
)


# ---------- 比較設定 ----------
with st.sidebar:
    st.header("⚙️ 比較設定")
    n_agents = st.slider("1ワールドあたりエージェント数", 100, 1500, 700, step=100)
    n_worlds = st.slider("並列ワールド数", 2, 8, 8, step=1)
    seed_base = st.number_input("乱数シード (基準)", 0, 9999, 42, step=1)

    st.divider()
    st.subheader("社会的影響強度の設定")
    beta_exp1 = st.slider(
        "実験1 の社会的影響強度 β₁",
        0.0, 2.0, 0.55, step=0.05,
        help="ランダム配置・DL数表示のみ"
    )
    beta_exp2 = st.slider(
        "実験2 の社会的影響強度 β₂",
        0.0, 2.0, 1.10, step=0.05,
        help="人気順表示・DL数表示"
    )

    run = st.button("🔬 両実験を実行して比較", type="primary", use_container_width=True)


# ---------- 実行 ----------
if "compare_result" not in st.session_state:
    st.session_state.compare_result = None

if run:
    songs = generate_songs(seed=int(seed_base))

    with st.spinner("実験1 を実行中..."):
        cfg1 = SimConfig(
            n_agents=int(n_agents), n_worlds=int(n_worlds),
            experiment=1,
            social_weight_exp1=float(beta_exp1),
            social_weight_exp2=float(beta_exp2),
            seed=int(seed_base),
        )
        res1 = run_experiment(songs, cfg1)

    with st.spinner("実験2 を実行中..."):
        cfg2 = SimConfig(
            n_agents=int(n_agents), n_worlds=int(n_worlds),
            experiment=2,
            social_weight_exp1=float(beta_exp1),
            social_weight_exp2=float(beta_exp2),
            seed=int(seed_base) + 100,
        )
        res2 = run_experiment(songs, cfg2)

    st.session_state.compare_result = {"exp1": res1, "exp2": res2}
    st.success("✅ 比較完了")


result = st.session_state.compare_result
if result is None:
    st.info("👈 サイドバーで「両実験を実行して比較」を押してください。")
    st.stop()

res1 = result["exp1"]
res2 = result["exp2"]


# =====================================================
# Fig. 1: Gini 係数の比較
# =====================================================
st.subheader("📈 不平等 (Gini 係数) — 論文 Fig. 1 相当")

gini1 = gini_per_world(res1)
gini2 = gini_per_world(res2)

rows = []
for i, g in enumerate(gini1["social_worlds"]):
    rows.append({"実験": "実験1", "条件": f"Social W{i+1}", "Gini": g})
rows.append({"実験": "実験1", "条件": "Indep.", "Gini": gini1["independent_mean"]})
for i, g in enumerate(gini2["social_worlds"]):
    rows.append({"実験": "実験2", "条件": f"Social W{i+1}", "Gini": g})
rows.append({"実験": "実験2", "条件": "Indep.", "Gini": gini2["independent_mean"]})

gini_df = pd.DataFrame(rows)

c1, c2 = st.columns(2)

with c1:
    chart1 = alt.Chart(gini_df[gini_df["実験"] == "実験1"]).mark_bar().encode(
        x=alt.X("条件:N", sort=None, title="条件"),
        y=alt.Y("Gini:Q", title="Gini 係数 G", scale=alt.Scale(domain=[0, 1])),
        color=alt.condition(
            alt.datum["条件"] == "Indep.",
            alt.value("#9bd"),
            alt.value("#345"),
        ),
        tooltip=["条件", "Gini"],
    ).properties(title="実験1: ランダム配置 (弱い社会的シグナル)", height=320)
    st.altair_chart(chart1, use_container_width=True)

with c2:
    chart2 = alt.Chart(gini_df[gini_df["実験"] == "実験2"]).mark_bar().encode(
        x=alt.X("条件:N", sort=None, title="条件"),
        y=alt.Y("Gini:Q", title="Gini 係数 G", scale=alt.Scale(domain=[0, 1])),
        color=alt.condition(
            alt.datum["条件"] == "Indep.",
            alt.value("#9bd"),
            alt.value("#345"),
        ),
        tooltip=["条件", "Gini"],
    ).properties(title="実験2: 人気順表示 (強い社会的シグナル)", height=320)
    st.altair_chart(chart2, use_container_width=True)

st.info(
    "🔎 観察ポイント: 社会的影響条件 (濃色) の Gini が独立条件 (淡色) より大きい "
    "= 人気の格差が広がる。さらに実験2 (人気順表示) では実験1 よりも Gini が大きい。"
)


# =====================================================
# Fig. 2: Unpredictability の比較
# =====================================================
st.divider()
st.subheader("🌪️ 不予測性 (Unpredictability U) — 論文 Fig. 2 相当")

u1_social = unpredictability([market_share(w.downloads) for w in res1.social_worlds])
u1_indep = unpredictability_independent(res1.independent)
u2_social = unpredictability([market_share(w.downloads) for w in res2.social_worlds])
u2_indep = unpredictability_independent(res2.independent)

u_df = pd.DataFrame([
    {"実験": "実験1", "条件": "Social Influence", "U": u1_social},
    {"実験": "実験1", "条件": "Independent",      "U": u1_indep},
    {"実験": "実験2", "条件": "Social Influence", "U": u2_social},
    {"実験": "実験2", "条件": "Independent",      "U": u2_indep},
])

cu1, cu2 = st.columns(2)

with cu1:
    chart_u1 = alt.Chart(u_df[u_df["実験"] == "実験1"]).mark_bar().encode(
        x=alt.X("条件:N", title="条件"),
        y=alt.Y("U:Q", title="Unpredictability U"),
        color=alt.Color("条件:N", legend=None),
        tooltip=["条件", "U"],
    ).properties(title="実験1", height=320)
    st.altair_chart(chart_u1, use_container_width=True)

with cu2:
    chart_u2 = alt.Chart(u_df[u_df["実験"] == "実験2"]).mark_bar().encode(
        x=alt.X("条件:N", title="条件"),
        y=alt.Y("U:Q", title="Unpredictability U"),
        color=alt.Color("条件:N", legend=None),
        tooltip=["条件", "U"],
    ).properties(title="実験2", height=320)
    st.altair_chart(chart_u2, use_container_width=True)

st.info(
    "🔎 観察ポイント: 社会的影響条件は独立条件より U が大きい "
    "= 同じ曲・同じルールでも世界が違えばヒット曲が変わる。"
    "強い社会的シグナル (実験2) ではさらに大きくなる。"
)


# =====================================================
# リアルタイムランキング推移
# =====================================================
st.divider()
st.subheader("⏱️ ランキング推移 (ダウンロード数の時系列)")

target_exp = st.radio(
    "推移を見る実験",
    [1, 2],
    format_func=lambda x: f"実験 {x}",
    horizontal=True,
)
target_world = st.selectbox(
    "ワールド",
    options=[("indep", "独立条件")] + [
        (f"w{i}", f"Social World {i + 1}") for i in range(len(res1.social_worlds))
    ],
    format_func=lambda x: x[1],
)

res = res1 if target_exp == 1 else res2
if target_world[0] == "indep":
    state = res.independent
else:
    state = res.social_worlds[int(target_world[0][1:])]

# history は (n_snapshots, n_songs) の配列
history = np.stack(state.history, axis=0)
snapshots = history.shape[0]
# 全部表示すると煩雑なので TOP K 曲だけ追跡
top_k = st.slider("追跡する曲数 (最終ダウンロード数の上位)", 3, 15, 8)
final = state.downloads
top_ids = np.argsort(-final)[:top_k]

rows = []
for snap_idx in range(snapshots):
    for sid in top_ids:
        rows.append({
            "snapshot": snap_idx,
            "subjects": (snap_idx + 1) * 10,  # snapshot_every=10
            "song": f"{res.songs[sid].band} - {res.songs[sid].title}",
            "downloads": int(history[snap_idx, sid]),
        })
hist_df = pd.DataFrame(rows)

chart_hist = alt.Chart(hist_df).mark_line(point=False).encode(
    x=alt.X("subjects:Q", title="参加エージェント数"),
    y=alt.Y("downloads:Q", title="ダウンロード数"),
    color=alt.Color("song:N", title="曲", legend=alt.Legend(columns=2, symbolLimit=0)),
    tooltip=["song", "subjects", "downloads"],
).properties(height=420)
st.altair_chart(chart_hist, use_container_width=True)

st.caption(
    "💡 社会的影響条件 (Social World) では、序盤の偶然のリードが累積して "
    "後続の参加者の選択に影響するため、ランキングが急激に開いていく様子が見られます。"
)
