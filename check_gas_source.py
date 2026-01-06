import asyncio
import config
from web3 import Web3

async def check_gas_source():
    """Check if the gas source wallet has funds"""
    if not config.GAS_SOURCE_PRIVATE_KEY:
        print("❌ GAS_SOURCE_PRIVATE_KEY is not configured!")
        return
    
    print(f"✅ GAS_SOURCE_PRIVATE_KEY is configured: {config.GAS_SOURCE_PRIVATE_KEY[:10]}...")
    
    # Get the address from private key
    from eth_account import Account
    acc = Account.from_key(config.GAS_SOURCE_PRIVATE_KEY)
    address = acc.address
    print(f"📍 Gas Source Address: {address}")
    
    # Check Polygon balance
    for rpc in config.POLYGON_RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            if not w3.is_connected():
                print(f"  ❌ RPC offline: {rpc}")
                continue
            
            balance_wei = w3.eth.get_balance(address)
            balance_matic = balance_wei / (10**18)
            print(f"  ✅ Polygon (MATIC) Balance: {balance_matic:.6f} MATIC (via {rpc})")
            break
        except Exception as e:
            print(f"  ❌ RPC error ({rpc}): {e}")

if __name__ == "__main__":
    asyncio.run(check_gas_source())
