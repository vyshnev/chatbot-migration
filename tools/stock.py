"""
tools/stock.py
--------------
Stock price tool using Alpha Vantage with Redis caching.
"""

import requests
from langchain_core.tools import tool
from core.config import ALPHA_VANTAGE_KEY
from cache.service import cached


@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
    using Alpha Vantage.
    """
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
    )

    def fetch_stock():
        r = requests.get(url)
        return r.json()

    return cached("get_stock_price", fetch_stock, 300)
