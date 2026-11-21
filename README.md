# MovieProject – MovieLens Rating & Genre Analysis

Exploratory data analysis of the [MovieLens](https://grouplens.org/datasets/movielens/) "latest-small" dataset: which genres and films do users rate highest, and does popularity predict quality?

**Dataset:** 100,836 ratings by 610 users on 9,742 movies (1996–2018), plus Wikipedia's list of highest-grossing films (scraped).

## Key findings

| | |
|---|---|
| Highest-rated genre (≥ 500 ratings) | **Film-Noir – 3.92** (then War 3.81, Documentary 3.80) |
| Lowest-rated genre | **Horror – 3.26** |
| Global mean rating | 3.50 |
| Movies with only one rating | 3,446 (≈ 35%) → raw averages are unreliable |
| Popularity vs. score | weak correlation (r = 0.11 between log #ratings and mean rating) |

Because so many films have very few ratings, the top-movie ranking uses a **Bayesian weighted rating** (IMDb-style): `WR = v/(v+m)·R + m/(v+m)·C`, with `m` = 90th percentile of rating counts (27) and `C` = global mean.
Top 3: *The Shawshank Redemption* (4.36), *The Godfather* (4.19), *Fight Club* (4.19).

## Charts

| Average rating by genre | Rating distribution | #Ratings vs. average |
|---|---|---|
| ![](figures/01_genre_bar.png) | ![](figures/02_rating_hist.png) | ![](figures/03_count_vs_rating.png) |

## Pipeline

`src/data_processor.py` – `MovieDataProcessor` chains the steps:

1. **Load** – downloads and extracts the MovieLens zip (skipped if already present).
2. **Clean** – drops duplicate / out-of-range ratings, extracts release year from titles, splits multi-genre fields, converts Unix timestamps.
3. **Analyze** – genre summary (mean, median, std, counts) and per-movie weighted rating.
4. **Export** – `data/processed/*.csv` and `movie_results.xlsx`.

`main.py` also draws the charts and scrapes Wikipedia (BeautifulSoup) to match the highest-grossing films with their MovieLens ratings.

## Run

```bash
pip install -r requirements.txt
python main.py                      # full pipeline
python main.py --min-genre-ratings 1000 --top-n 30 --no-scrape
```

The notebook `notebooks/movie_analysis.ipynb` walks through the same analysis step by step.

**Stack:** Python, Pandas, NumPy, Matplotlib, Seaborn, Requests, BeautifulSoup, Jupyter, Excel (openpyxl).

*Data: F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets. ACM TiiS 5(4). Raw data is not committed; it is downloaded on first run.*
