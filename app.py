"""
仮想音楽市場 (MusicLab Replica) - Streamlit メインアプリ

Salganik, Dodds & Watts (2006)
"Experimental Study of Inequality and Unpredictability in an Artificial Cultural Market"
Science 311, 854 を Streamlit で再現/体験するアプリ。

ページ構成 (左サイドバーで切り替え):
- ホーム            : 論文の概要と使い方
- シミュレーション   : エージェントを大量に走らせて結果を観察
- インタラクティブ体験: ユーザー自身が「曲を聴いてダウンロードする」体験
- 分析・比較         : 独立条件 vs 社会的影響条件、Gini/Unpredictability

実行方法:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="仮想音楽市場 (MusicLab Replica)",
    page_icon="🎵",
    layout="wide",
)

st.title("🎵 仮想音楽市場 (MusicLab Replica)")
st.caption(
    "Salganik, Dodds & Watts (2006) "
    "*Experimental Study of Inequality and Unpredictability in an Artificial Cultural Market* "
    "を Streamlit 上で再現するシミュレーション/体験アプリ"
)

st.markdown(
    """
### この実験で何を確かめるのか

Salganik たちの問い:
**「ヒット曲はなぜ生まれるのか? 本当に "良い曲" が売れているのか?」**

論文は仮想の音楽マーケット (musiclab.columbia.edu) に 14,341 人を集め、
2 つの条件に分けて 48 曲のダウンロード数を比較しました。

- **独立条件 (Independent)**: 他人のダウンロード数は見えない。純粋に自分の好みで決める。
- **社会的影響条件 (Social influence)**: 他人のダウンロード数が見える。8 つの「並行世界」で別々に進む。

結果:
1. **不平等 (Gini)** : 社会的影響があると人気曲はより人気に、不人気曲はより不人気になる。
2. **不予測性 (Unpredictability)** : 同じ条件・同じ曲でも、世界が違えばヒットする曲が変わる。
3. **品質と成功の関係** : "ベスト" は最悪にならず "ワースト" は最高にならないが、それ以外は何でも起こりうる。

---

### このアプリでできること

左サイドバーから 4 つのページに移動できます。

1. **🏠 ホーム** : このページ。論文の概要と使い方。
2. **🤖 シミュレーション** : 仮想エージェントが大量に行動し、独立条件と8つの並列ワールドを再現。
3. **🎧 インタラクティブ体験** : あなた自身が曲を選んで「ダウンロード」する体験版。
4. **📊 分析・比較** : Gini 係数 / Unpredictability U / リアルタイムランキングを可視化。

それぞれのページで、論文の **Fig. 1, 2** に相当する図が確認できます。
    """
)

with st.sidebar:
    st.header("📚 参考")
    st.markdown(
        """
**論文**
Salganik, M. J., Dodds, P. S., & Watts, D. J. (2006).
*Science*, 311(5762), 854-856.

**MusicLab (実験サイト)**
http://musiclab.columbia.edu
        """
    )
    st.info("👈 上のメニューからページを移動してください")
