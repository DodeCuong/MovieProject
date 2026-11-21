def split_genres(genre_string):
    """'Adventure|Comedy' -> ['Adventure', 'Comedy']. Trả list rỗng nếu không có genre."""
    if not genre_string or genre_string == "(no genres listed)":
        return []
    genres = []
    for g in genre_string.split("|"):
        g = g.strip()
        if g:                      # bỏ chuỗi rỗng
            genres.append(g)
    return genres
from datetime import datetime, timezone

def convert_timestamp(ts, fmt="%Y-%m-%d"):
    """964982703 -> '2000-07-30'."""
    if ts is None or ts < 0:
        return None
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime(fmt)
def weighted_rating(v, R, m, C):
    """Bayesian weighted rating."""
    if v + m == 0:
        return C
    return (v / (v + m)) * R + (m / (v + m)) * C
def filter_movies_by_count(movie_stats, thresholds=(50, 3.5)):
    """movie_stats: list các dict {'title', 'count', 'mean'}.
    thresholds: tuple (min_count, min_rating)."""
    min_count, min_rating = thresholds   # tuple unpacking
    result = []
    for m in movie_stats:
        if m["count"] >= min_count and m["mean"] >= min_rating:
            result.append(m)
    return result
def split_title_year(title):
    """'Toy Story (1995)' -> ('Toy Story', 1995)"""
    title = title.strip()
    if title.endswith(")") and title[-5:-1].isdigit():
        return (title[:-7].strip(), int(title[-5:-1]))
    return (title, None)