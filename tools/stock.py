"""
tools/stock.py
--------------
Stock price tool using Alpha Vantage with Redis caching.
"""

import requests
from langchain_core.tools import tool
from core.config import ALPHA_VANTAGE_KEY
from cache.service import cached

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
REQUEST_TIMEOUT_SECONDS = 10


@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
    using Alpha Vantage.
    """
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        return {"error": "Stock symbol is required"}

    if not ALPHA_VANTAGE_KEY:
        return {"error": "Alpha Vantage API key is not configured"}

    def fetch_stock(stock_symbol: str):
        try:
            response = requests.get(
                ALPHA_VANTAGE_URL,
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": stock_symbol,
                    "apikey": ALPHA_VANTAGE_KEY,
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            if not response.ok:
                return {
                    "error": (
                        f"Stock provider returned HTTP {response.status_code} "
                        f"for {stock_symbol}"
                    )
                }
            return response.json()
        except requests.Timeout:
            return {"error": f"Timed out fetching stock price for {stock_symbol}"}
        except requests.RequestException:
            return {"error": f"Failed to fetch stock price for {stock_symbol}"}
        except ValueError:
            return {"error": f"Received invalid stock response for {stock_symbol}"}

    return cached("get_stock_price", fetch_stock, 300, normalized_symbol)
