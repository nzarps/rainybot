"""
Price Service
Crypto price fetching with caching and multiple API fallbacks.
Optimized for high-performance with global session management and parallel fetching.
"""

import time
import asyncio
import aiohttp

# Price cache (shared across calls)
price_cache = {}
CACHE_DURATION = 60  # seconds
GLOBAL_SESSION = None

async def get_session():
    """Get or create a persistent aiohttp session"""
    global GLOBAL_SESSION
    if GLOBAL_SESSION is None or GLOBAL_SESSION.closed:
        GLOBAL_SESSION = aiohttp.ClientSession()
    return GLOBAL_SESSION

async def get_coingecko_price(currency_key, vs_currency="usd"):
    """Get price from CoinGecko using internal currency key mapping"""
    mapping = {
        'ltc': 'litecoin',
        'solana': 'solana',
        'ethereum': 'ethereum',
        'usdt_bep20': 'tether',
        'usdt_polygon': 'tether',
        'usdt': 'tether',
        'bnb': 'binancecoin',
        'matic': 'matic-network',
        'btc': 'bitcoin',
    }
    # Resolve the ID or use the key directly
    cg_id = mapping.get(currency_key.lower(), currency_key.lower())
    
    # Standardize tether aliases for GC
    if any(x in currency_key.lower() for x in ['usdt', 'tether']):
        cg_id = 'tether'

    vs_curr = vs_currency.lower()
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies={vs_curr}"
    
    session = await get_session()
    try:
        async with session.get(url, timeout=5) as r:
            if r.status == 200:
                data = await r.json()
                if cg_id in data:
                    return float(data[cg_id][vs_curr])
            elif r.status == 429:
                return "RATE_LIMIT"
    except: pass
    return None

async def get_ltc_price(vs_currency="usd"):
    """Get LTC price using the fastest responding API in parallel"""
    vs_curr = vs_currency.lower()
    if vs_curr != "usd":
        return await get_coingecko_price('ltc', vs_curr)

    apis = [
        "https://api.binance.com/api/v3/ticker/price?symbol=LTCUSDT",
        "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd",
        "https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD",
    ]
    session = await get_session()
    
    async def fetch(url):
        try:
            async with session.get(url, timeout=3) as r:
                if r.status == 200:
                    d = await r.json()
                    if "price" in d: return float(d["price"])
                    if "litecoin" in d: return float(d["litecoin"]["usd"])
                    if "USD" in d: return float(d["USD"])
                elif r.status == 429:
                    return "RATE_LIMIT"
        except: pass
        return None

    tasks = [asyncio.create_task(fetch(u)) for u in apis]
    for task in asyncio.as_completed(tasks):
        res = await task
        if res:
            if res == "RATE_LIMIT": continue
            for t in tasks: t.cancel()
            return res
    return 0.0

async def get_solana_price(vs_currency="usd"):
    """Get SOL price using the fastest responding API in parallel"""
    vs_curr = vs_currency.lower()
    if vs_curr != "usd":
        return await get_coingecko_price('solana', vs_curr)

    apis = [
        "https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT",
        "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd",
        "https://min-api.cryptocompare.com/data/price?fsym=SOL&tsyms=USD",
    ]
    session = await get_session()
    
    async def fetch(url):
        try:
            async with session.get(url, timeout=3) as r:
                if r.status == 200:
                    d = await r.json()
                    if "price" in d: return float(d["price"])
                    if "solana" in d: return float(d["solana"]["usd"])
                    if "USD" in d: return float(d["USD"])
                elif r.status == 429:
                    return "RATE_LIMIT"
        except: pass
        return None

    tasks = [asyncio.create_task(fetch(u)) for u in apis]
    for task in asyncio.as_completed(tasks):
        res = await task
        if res:
            if res == "RATE_LIMIT": continue
            for t in tasks: t.cancel()
            return res
    return 0.0

async def get_ethereum_price(vs_currency="usd"):
    """Get ETH price using the fastest responding API in parallel"""
    vs_curr = vs_currency.lower()
    if vs_curr != "usd":
        return await get_coingecko_price('ethereum', vs_curr)

    apis = [
        "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT",
        "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd",
        "https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD",
    ]
    session = await get_session()
    
    async def fetch(url):
        try:
            async with session.get(url, timeout=3) as r:
                if r.status == 200:
                    d = await r.json()
                    if "price" in d: return float(d["price"])
                    if "ethereum" in d: return float(d["ethereum"]["usd"])
                    if "USD" in d: return float(d["USD"])
                elif r.status == 429:
                    return "RATE_LIMIT"
        except: pass
        return None

    tasks = [asyncio.create_task(fetch(u)) for u in apis]
    for task in asyncio.as_completed(tasks):
        res = await task
        if res:
            if res == "RATE_LIMIT": continue
            for t in tasks: t.cancel()
            return res
    return 0.0

async def get_usdt_price(vs_currency="usd"):
    """Get USDT price using the fastest responding API in parallel"""
    vs_curr = vs_currency.lower()
    if vs_curr != "usd":
        return await get_coingecko_price('usdt', vs_curr)

    apis = [
        "https://api.binance.com/api/v3/ticker/price?symbol=USDTUSDC",
        "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=usd",
        "https://min-api.cryptocompare.com/data/price?fsym=USDT&tsyms=USD",
    ]
    session = await get_session()
    
    async def fetch(url):
        try:
            async with session.get(url, timeout=3) as r:
                if r.status == 200:
                    d = await r.json()
                    if "price" in d: return float(d["price"])
                    if "tether" in d: return float(d["tether"]["usd"])
                    if "USD" in d: return float(d["USD"])
                elif r.status == 429:
                    return "RATE_LIMIT"
        except: pass
        return None

    tasks = [asyncio.create_task(fetch(u)) for u in apis]
    for task in asyncio.as_completed(tasks):
        res = await task
        if res:
            if res == "RATE_LIMIT": continue
            for t in tasks: t.cancel()
            return res
    return 1.0

async def get_cached_price(currency, vs_currency="usd"):
    """Get cached price or fetch new one using universal CoinGecko fetcher with parallel fallbacks"""
    current_time = time.time()
    curr = currency.lower()
    vs_curr = vs_currency.lower()
    
    cache_key = f"{curr}_{vs_curr}_price"
    
    if cache_key in price_cache:
        price, timestamp = price_cache[cache_key]
        if current_time - timestamp < CACHE_DURATION:
            return price
            
    # Try CoinGecko first
    new_price = await get_coingecko_price(curr, vs_curr)
    
    # Fallback if CG fails
    if (new_price is None or new_price <= 0) and new_price != "RATE_LIMIT":
        if curr == 'ltc':
            new_price = await get_ltc_price(vs_curr)
        elif curr == 'solana':
            new_price = await get_solana_price(vs_curr)
        elif curr == 'ethereum':
            new_price = await get_ethereum_price(vs_curr)
        elif curr in ['usdt_bep20', 'usdt_polygon', 'usdt', 'usdtbep', 'usdtpol']:
            new_price = await get_usdt_price(vs_curr)
        else:
            # Last resort
            new_price = await get_coingecko_price(curr, vs_curr)
            if not new_price: new_price = 0.0

    if new_price and new_price != "RATE_LIMIT" and new_price > 0:
        price_cache[cache_key] = (new_price, current_time)
        return new_price
    
    if new_price == "RATE_LIMIT":
        return "RATE_LIMIT"
        
    return 0.0

async def usd_to_currency_amount(amount_usd, currency):
    """Convert USD to crypto amount using cached prices"""
    rate = await get_cached_price(currency, "usd")
    if rate == "RATE_LIMIT": return "RATE_LIMIT"
    if rate and rate > 0:
        result = amount_usd / rate
        return round(result, 8)
    return 0.0

async def currency_to_fiat(amount, currency, vs_currency="usd"):
    """Convert crypto amount to fiat using cached prices"""
    rate = await get_cached_price(currency, vs_currency)
    if rate == "RATE_LIMIT": return "RATE_LIMIT"
    if rate and rate > 0:
        result = amount * rate
        return round(result, 2)
    return 0.0

async def currency_to_usd(amount, currency):
    """Convert crypto amount to USD (backward compatibility)"""
    return await currency_to_fiat(amount, currency, "usd")
