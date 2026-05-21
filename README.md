# 仮想音楽市場 (MusicLab Replica) on Streamlit

Salganik, Dodds & Watts (2006)
*"Experimental Study of Inequality and Unpredictability in an Artificial Cultural Market"*
(Science 311, 854-856) を Streamlit 上で再現するシミュレーション/体験アプリです。

岩手県立大学 非常勤講義「仮想 SNS」教材として作成。

## できること

- **シミュレーション**: 仮想エージェントが大量に行動し、独立条件と8並列ワールドを再現
- **インタラクティブ体験**: あなた自身が曲を選んで「ダウンロード」する体験版
- **分析・比較**: Gini 係数・Unpredictability U・ランキング推移を可視化 (論文 Fig. 1, 2 相当)

## セットアップ

```bash
# 仮想環境 (推奨)
python3 -m venv .venv
source .venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開きます。
左サイドバーのメニューから 3 つのページ
(🤖 シミュレーション / 🎧 インタラクティブ体験 / 📊 分析・比較) に移動できます。

## ディレクトリ構成

```
仮想SNS/
├── app.py                       # メインページ (ホーム)
├── requirements.txt
├── README.md
├── data/
│   ├── __init__.py
│   └── songs.py                 # 48 曲ダミーデータ (Table S3 の曲名)
├── sim/
│   ├── __init__.py
│   ├── engine.py                # エージェント・ベース・シミュレーション
│   └── metrics.py               # Gini / Unpredictability / ランキング計算
└── pages/
    ├── 1_🤖_シミュレーション.py
    ├── 2_🎧_インタラクティブ体験.py
    └── 3_📊_分析・比較.py
```

## モデル概要

各エージェントは曲リストから L 曲を「聴き」、各曲について以下の確率でダウンロードします:

```
p(download | listen) = sigmoid(α * (quality - q0) + β * log(1 + downloads))
```

- `α`: 品質の重み
- `β`: 社会的影響の強さ (独立条件では 0)
- 実験1 と 2 は `β` および「聴かれやすさのバイアス」が異なる

## 参考文献

- Salganik, M. J., Dodds, P. S., & Watts, D. J. (2006).
  Experimental Study of Inequality and Unpredictability in an Artificial Cultural Market.
  *Science*, 311(5762), 854-856. DOI: 10.1126/science.1121066
- MusicLab (実験サイト): http://musiclab.columbia.edu
