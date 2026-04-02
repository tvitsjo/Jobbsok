from app.fetchers.base import BaseJobFetcher
from app.fetchers.finn_fetcher import FinnFetcher
from app.fetchers.nav_fetcher import NAVFetcher


def get_fetchers() -> dict[str, BaseJobFetcher]:
    return {
        "nav_arbeidsplassen": NAVFetcher(),
        "finn": FinnFetcher(),
    }
