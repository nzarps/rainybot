import asyncio
from web3 import Web3

POLYGON_RPC_URLS = ["https://polygon-rpc.com", "https://rpc-mainnet.matic.quiknode.pro"]

async def get_dynamic_gas_price():
    """Fetch current gas price in Wei from RPCs."""
    from web3 import Web3
    for rpc in POLYGON_RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            if w3.is_connected():
                return w3.eth.gas_price
        except:
            continue
    return 0

async def test_gas_estimation():
    print("Testing dynamic gas estimation for Polygon USDT...")
    
    gas_price = await get_dynamic_gas_price()
    print(f"Current gas price: {gas_price} Wei ({gas_price / 10**9:.2f} Gwei)")
    
    # Test with 2 transactions (fee + main)
    tx_count = 2
    gas_limit = 65000
    total_gas_needed = gas_limit * tx_count
    
    needed_wei = total_gas_needed * gas_price
    needed_with_buffer = int(needed_wei * 1.3)
    needed_native = needed_with_buffer / 10**18
    
    print(f"Gas limit per tx: {gas_limit}")
    print(f"Transaction count: {tx_count}")
    print(f"Needed MATIC (with 30% buffer): {needed_native:.6f}")

if __name__ == "__main__":
    asyncio.run(test_gas_estimation())
