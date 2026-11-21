"""
main.py - Chạy toàn bộ project bằng một lệnh:
    python main.py
    python main.py --min-genre-ratings 1000 --top-n 30 --no-scrape
"""
import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                     # vẽ không cần cửa sổ (chạy được trên server)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from bs4 import BeautifulSoup

from src.data_processor import MovieDataProcessor

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_highest-grossing_films"
HEADERS = {"User-Agent": "PSD301M-StudentProject/1.0 (student project)"}
FIG_DIR = Path("figures")


def scrape_grossing_films():
    """Scrape bảng highest-grossing films đầu tiên trên Wikipedia."""
    html = requests.get(WIKI_URL, headers=HEADERS, timeout=30).text
    table = BeautifulSoup(html, "lxml").find("table", class_="wikitable")
    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if len(cells) < 5:
            continue
        rank, _peak, title, gross, year = cells[:5]
        years = re.findall(r"\d{4}", year)
        if not years:
            continue
        rows.append({
            "rank": rank,
            "title": re.sub(r"\[.*?\]", "", title).strip(),
            "worldwide_gross": int(re.sub(r"[^0-9]", "", gross.split("$")[-1]) or 0),
            "year": int(years[0]),
        })
    return pd.DataFrame(rows)


def normalize_title(title):
    """'Dark Knight, The' -> 'the dark knight'."""
    title = re.sub(r"\s*\(\d{4}\)\s*$", "", str(title))
    m = re.match(r"^(.*), (The|A|An)$", title)
    if m:
        title = f"{m.group(2)} {m.group(1)}"
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def make_figures(p):
    FIG_DIR.mkdir(exist_ok=True)
    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=p.genre_summary, y="genre", x="avg_rating", color="steelblue", ax=ax)
    ax.axvline(p.C, ls="--", color="red", label=f"Trung bình chung = {p.C:.2f}")
    ax.set(title=f"Average rating theo thể loại (≥ {p.min_genre_ratings} rating)",
           xlabel="Điểm trung bình", ylabel="")
    ax.set_xlim(3, p.genre_summary["avg_rating"].max() + 0.1)
    ax.legend()
    fig.tight_layout(); fig.savefig(FIG_DIR / "01_genre_bar.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(p.ratings["rating"], bins=np.arange(0.25, 5.5, 0.5), edgecolor="white")
    ax.set_xticks(np.arange(0.5, 5.5, 0.5))
    ax.set(title="Phân bố điểm rating", xlabel="Rating", ylabel="Số lượt")
    fig.tight_layout(); fig.savefig(FIG_DIR / "02_rating_hist.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=p.movie_stats, x="n_ratings", y="avg_rating", alpha=0.3, s=15, ax=ax)
    ax.set_xscale("log")
    ax.set(title="Số lượt rating vs điểm trung bình",
           xlabel="Số lượt rating (thang log)", ylabel="Điểm trung bình")
    fig.tight_layout(); fig.savefig(FIG_DIR / "03_count_vs_rating.png", dpi=150); plt.close(fig)
    print("[figures] Đã lưu 3 biểu đồ vào", FIG_DIR)


def compare_with_wikipedia(p):
    wiki = scrape_grossing_films()
    wiki.to_csv(p.raw_dir / "grossing_films.csv", index=False, encoding="utf-8-sig")
    wiki["key"] = wiki["title"].map(normalize_title)
    ms = p.movie_stats.copy()
    ms["key"] = ms["clean_title"].map(normalize_title)
    matched = wiki.merge(ms, left_on=["key", "year"], right_on=["key", "year"], how="left")
    found = matched["movieId"].notna().sum()
    print(f"[wiki] Khớp {found}/{len(wiki)} phim doanh thu cao với MovieLens")
    out = matched[["rank", "title", "year", "worldwide_gross", "n_ratings", "avg_rating", "weighted_rating"]]
    out.to_csv(p.out_dir / "grossing_vs_movielens.csv", index=False, encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser(description="PSD301M MovieLens pipeline")
    parser.add_argument("--min-genre-ratings", type=int, default=500)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--no-scrape", action="store_true", help="Bỏ qua scraping Wikipedia")
    args = parser.parse_args()

    p = MovieDataProcessor(min_genre_ratings=args.min_genre_ratings, top_n=args.top_n).run()
    make_figures(p)
    if not args.no_scrape:
        try:
            compare_with_wikipedia(p)
        except Exception as e:                # mạng lỗi không làm hỏng cả pipeline
            print("[wiki] Bỏ qua do lỗi:", e)
    print(p.top_movies.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
