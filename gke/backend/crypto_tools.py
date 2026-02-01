# crypto_tools.py
import requests
from langchain_core.tools import tool

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

@tool
def get_crypto_price(coin_id: str) -> str:
    """Get the current price and market data for a cryptocurrency.
    
    Args:
        coin_id: The cryptocurrency ID (e.g., 'bitcoin', 'ethereum', 'solana')
    
    Returns:
        Current price, market cap, volume, and 24h change
    """
    try:
        response = requests.get(
            f"{COINGECKO_BASE_URL}/coins/{coin_id.lower()}",
            params={"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        market = data["market_data"]
        return (
            f"💰 {data['name']} ({data['symbol'].upper()})\n"
            f"Price: ${market['current_price']['usd']:,.2f}\n"
            f"Market Cap: ${market['market_cap']['usd']:,.0f}\n"
            f"24h Volume: ${market['total_volume']['usd']:,.0f}\n"
            f"24h Change: {market['price_change_percentage_24h']:.2f}%\n"
            f"Rank: #{data['market_cap_rank']}"
        )
    except Exception as e:
        return f"Error fetching {coin_id}: {str(e)}"


@tool
def get_top_cryptos(limit: int = 10) -> str:
    """Get the top cryptocurrencies by market cap.
    
    Args:
        limit: Number of cryptocurrencies to return (default 10, max 100)
    
    Returns:
        List of top cryptocurrencies with price and market cap
    """
    try:
        response = requests.get(
            f"{COINGECKO_BASE_URL}/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": min(limit, 100),
                "page": 1,
                "sparkline": "false"
            },
            timeout=10
        )
        response.raise_for_status()
        coins = response.json()
        
        result = "📊 Top Cryptocurrencies by Market Cap:\n\n"
        for coin in coins:
            price = coin['current_price'] or 0
            change = coin['price_change_percentage_24h'] or 0
            emoji = "🟢" if change >= 0 else "🔴"
            result += f"#{coin['market_cap_rank']} {coin['name']} ({coin['symbol'].upper()}): ${price:,.2f} {emoji} {change:.2f}%\n"
        
        return result
    except Exception as e:
        return f"Error fetching top cryptos: {str(e)}"


@tool
def search_crypto(query: str) -> str:
    """Search for a cryptocurrency by name or symbol.
    
    Args:
        query: Search term (e.g., 'btc', 'ethereum', 'doge')
    
    Returns:
        List of matching cryptocurrencies with their IDs
    """
    try:
        response = requests.get(
            f"{COINGECKO_BASE_URL}/search",
            params={"query": query},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        coins = data.get("coins", [])[:5]
        if not coins:
            return f"No cryptocurrencies found for '{query}'"
        
        result = f"🔍 Search results for '{query}':\n\n"
        for coin in coins:
            result += f"• {coin['name']} ({coin['symbol'].upper()}) - ID: {coin['id']}\n"
        
        return result
    except Exception as e:
        return f"Error searching: {str(e)}"