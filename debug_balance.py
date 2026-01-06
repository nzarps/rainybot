import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider
import json

USDT_POLYGON_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
POLYGON_RPC_URLS = ["https://polygon.llamarpc.com", "https://1rpc.io/matic", "https://rpc.ankr.com/polygon", "https://polygon-rpc.com"]
WALLET = "0x6A893a51f34f04E5c5228388A754C1888E55f6d4"

USDT_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

async def check_balance():
    for rpc in POLYGON_RPC_URLS:
        try:
            w3 = AsyncWeb3(AsyncHTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if not await w3.is_connected():
                print(f"RPC {rpc}: Not connected")
                continue
            
            contract = w3.eth.contract(address=AsyncWeb3.to_checksum_address(USDT_POLYGON_CONTRACT), abi=USDT_ABI)
            balance = await contract.functions.balanceOf(AsyncWeb3.to_checksum_address(WALLET)).call()
            print(f"RPC {rpc}: Balance = {balance} (USDT units)")
        except Exception as e:
            print(f"RPC {rpc}: Error = {e}")

if __name__ == "__main__":
    asyncio.run(check_balance())
