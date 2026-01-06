
import asyncio
import sys
import os

# Add project root
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from services.price_service import get_cached_price

async def verify_calc():
    print("--- Testing Price Service & Calc Logic ---")
    
    currencies = ['ltc', 'eth', 'sol', 'usdt_bep20']
    
    for curr in currencies:
        price = await get_cached_price(curr)
        print(f"Price for {curr}: ${price}")
        
        # Test Calc Logic (USD to Crypto)
        amount_usd = 100
        if price > 0:
            crypto_amt = amount_usd / price
            print(f"  $100 USD = {crypto_amt:.6f} {curr}")
            
        # Test Calc Logic (Crypto to USD)
        amount_crypto = 1
        if price > 0:
            usd_amt = amount_crypto * price
            print(f"  1 {curr} = ${usd_amt:.2f} USD")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(verify_calc())
