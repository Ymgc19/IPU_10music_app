"""データモジュール (ダミー楽曲データ)"""
from .songs import Song, generate_songs, songs_to_dataframe

__all__ = ["Song", "generate_songs", "songs_to_dataframe"]
