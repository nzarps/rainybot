import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider

async def test_eth_rpcs():
    rpcs = [
        "https://ethereum-rpc.publicnode.com",
        "https://eth.llamarpc.com",
        "https://1rpc.io/eth",
        "https://rpc.ankr.com/eth"
    ]
    
    for rpc in rpcs:
        print(f"Testing {rpc}...")
        try:
            w3 = AsyncWeb3(AsyncHTTPProvider(rpc, request_kwargs={"timeout": 5}))
            connected = await w3.is_connected()
            if connected:
                bn = await w3.eth.block_number
                gp = await w3.eth.gas_price
                print(f"  [SUCCESS] Block: {bn}, Gas Price: {w3.from_wei(gp, 'gwei')} gwei")
            else:
                print(f"  [FAILED] Connection failed")
        except Exception as e:
            print(f"  [ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(test_eth_rpcs())
