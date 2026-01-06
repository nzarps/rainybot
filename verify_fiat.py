import asyncio
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.price_service import get_cached_price, currency_to_fiat

async def main():
    print("Testing Price Service Enhancements...")
    
    # Test USD
    price_usd = await get_cached_price('ltc', 'usd')
    print(f"LTC Price (USD): {price_usd}")
    
    # Test EUR
    price_eur = await get_cached_price('ltc', 'eur')
    print(f"LTC Price (EUR): {price_eur}")
    
    # Test INR
    price_inr = await get_cached_price('ltc', 'inr')
    print(f"LTC Price (INR): {price_inr}")
    
    # Test conversion
    amount = 1.5
    fiat_val = await currency_to_fiat(amount, 'ltc', 'eur')
    print(f"{amount} LTC in EUR: {fiat_val}")
    
    # Test Rate Limit (Force a 429 if possible, or just check logic)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
