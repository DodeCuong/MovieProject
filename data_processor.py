"""
data_processor.py - Pipeline phân tích MovieLens cho project PSD301M.

Class MovieDataProcessor gom toàn bộ quy trình:
    load_data() -> clean_data() -> analyze_genres() -> analyze_movies() -> export_results()
"""
import io
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests


def split_genres(genre_string):
    """'Adventure|Comedy' -> ['Adventure', 'Comedy']; '(no genres listed)' -> []."""
    if not isinstance(genre_string, str) or genre_string == "(no genres listed)":
        return []
    return [g.strip() for g in genre_string.split("|") if g.strip()]


def weighted_rating(v, R, m, C):
    """Bayesian weighted rating. Chạy được cho số đơn lẻ lẫn mảng NumPy/Series."""
    return (v / (v + m)) * R + (m / (v + m)) * C


class MovieDataProcessor:
    ZIP_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"

    def __init__(self, data_dir="data", min_genre_ratings=500, quantile=0.90, top_n=20):
        self.raw_dir = Path(data_dir) / "raw"
        self.out_dir = Path(data_dir) / "processed"
        self.min_genre_ratings = min_genre_ratings   # genre phải có >= số rating này
        self.quantile = quantile                     # m = quantile số lượt rating
        self.top_n = top_n
        # dữ liệu sẽ được gán dần qua các bước
        self.movies = self.ratings = self.tags = None
        self.rated = self.rated_genre = None
        self.genre_summary = self.movie_stats = self.top_movies = None
        self.C = self.m = None

    # ------------------------------------------------------------------ load
    def _download(self):
        target = self.raw_dir / "ml-latest-small"
        if (target / "ratings.csv").exists():
            print("[load] Dữ liệu đã có, bỏ qua tải.")
            return
        print("[load] Đang tải", self.ZIP_URL)
        resp = requests.get(self.ZIP_URL, timeout=120)
        resp.raise_for_status()
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            z.extractall(self.raw_dir)

    def load_data(self):
        self._download()
        base = self.raw_dir / "ml-latest-small"
        self.movies = pd.read_csv(base / "movies.csv")
        self.ratings = pd.read_csv(base / "ratings.csv")
        self.tags = pd.read_csv(base / "tags.csv")
        print(f"[load] movies={self.movies.shape}, ratings={self.ratings.shape}, tags={self.tags.shape}")
        return self

    # ----------------------------------------------------------------- clean
    def clean_data(self):
        if self.movies is None:
            raise RuntimeError("Gọi load_data() trước clean_data().")
        mv = self.movies.drop_duplicates("movieId").copy()
        mv["year"] = mv["title"].str.extract(r"\((\d{4})\)\s*$")[0].astype("float")
        mv["clean_title"] = mv["title"].str.replace(r"\s*\(\d{4}\)\s*$", "", regex=True).str.strip()
        mv["genre_list"] = mv["genres"].apply(split_genres)
        self.movies = mv

        rt = self.ratings.drop_duplicates(["userId", "movieId"]).copy()
        rt = rt[rt["rating"].between(0.5, 5.0)]
        rt["datetime"] = pd.to_datetime(rt["timestamp"], unit="s")
        rt["rating_year"] = rt["datetime"].dt.year
        self.ratings = rt

        self.rated = rt.merge(mv[["movieId", "clean_title", "year", "genres"]], on="movieId", how="left")
        movie_genres = (mv[["movieId", "genre_list"]].explode("genre_list")
                        .rename(columns={"genre_list": "genre"}).dropna(subset=["genre"]))
        self.rated_genre = rt.merge(movie_genres, on="movieId", how="inner")
        print(f"[clean] ratings={len(rt)}, rated={len(self.rated)}, rated_genre={len(self.rated_genre)}")
        return self

    # --------------------------------------------------------------- analyze
    def analyze_genres(self):
        gs = (self.rated_genre.groupby("genre")
              .agg(avg_rating=("rating", "mean"),
                   median_rating=("rating", "median"),
                   std_rating=("rating", "std"),
                   n_ratings=("rating", "size"),
                   n_movies=("movieId", "nunique")))
        gs = gs[gs["n_ratings"] >= self.min_genre_ratings]
        self.genre_summary = gs.sort_values("avg_rating", ascending=False).round(3).reset_index()
        print(f"[genre] {len(self.genre_summary)} genre đạt ngưỡng; cao nhất: "
              f"{self.genre_summary.iloc[0]['genre']}")
        return self

    def analyze_movies(self):
        ms = (self.rated.groupby(["movieId", "clean_title", "year", "genres"], dropna=False)
              .agg(n_ratings=("rating", "size"), avg_rating=("rating", "mean"))
              .reset_index())
        self.C = self.ratings["rating"].mean()
        self.m = ms["n_ratings"].quantile(self.quantile)
        ms["weighted_rating"] = weighted_rating(ms["n_ratings"], ms["avg_rating"], self.m, self.C)
        self.movie_stats = ms
        self.top_movies = (ms[ms["n_ratings"] >= self.m]
                           .sort_values("weighted_rating", ascending=False)
                           .head(self.top_n).round(3).reset_index(drop=True))
        r = np.corrcoef(np.log1p(ms["n_ratings"]), ms["avg_rating"])[0, 1]
        print(f"[movies] C={self.C:.3f}, m={self.m:.0f}, corr(log count, avg)={r:.3f}")
        return self

    # ---------------------------------------------------------------- export
    def export_results(self, excel=True):
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.top_movies.to_csv(self.out_dir / "top_movies.csv", index=False, encoding="utf-8-sig")
        self.genre_summary.to_csv(self.out_dir / "genre_summary.csv", index=False, encoding="utf-8-sig")
        if excel:
            with pd.ExcelWriter(self.out_dir / "movie_results.xlsx") as w:
                self.top_movies.to_excel(w, sheet_name="top_movies", index=False)
                self.genre_summary.to_excel(w, sheet_name="genre_summary", index=False)
        print("[export] Đã lưu vào", self.out_dir)
        return self

    def run(self):
        """Chạy toàn bộ pipeline bằng method chaining."""
        return self.load_data().clean_data().analyze_genres().analyze_movies().export_results()
