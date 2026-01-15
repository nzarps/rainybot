import asyncio
import os
import sys
from web3 import AsyncWeb3, AsyncHTTPProvider

# Import config if possible, else hardcode for test
POLYGON_RPC_URLS = [
    "https://polygon-rpc.com",
    "https://1rpc.io/matic",
    "https://rpc-mainnet.maticvigil.com"
]

USDT_POLYGON_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"

async def test_gas():
    for rpc in POLYGON_RPC_URLS:
        try:
            w3 = AsyncWeb3(AsyncHTTPProvider(rpc))
            if not await w3.is_connected():
                print(f"RPC {rpc} not connected")
                continue
            
            gas_price = await w3.eth.gas_price
            print(f"RPC: {rpc}")
            print(f"Current Gas Price: {gas_price / 1e9} Gwei")
            
            # Simple simulation of USDT transfer (to self)
            # Dummy address
            address = "0x0000000000000000000000000000000000000000"
            abi = [{"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}]
            contract = w3.eth.contract(address=USDT_POLYGON_CONTRACT, abi=abi)
            
            # Note: estimate_gas might fail without real balance, but let's see
            print("Estimating gas for USDT transfer...")
            # We use a real-ish address but 0 amount
            try:
                # Need a sender with 0 balance maybe?
                est = 65000 # Standard
                print(f"Standard Buffer calculation:")
                print(f"1.5x Limit = {est * 1.5}")
                print(f"1.2x Price = {gas_price * 1.2 / 1e9} Gwei")
                print(f"Total needed for 1 tx (Wei): {est * 1.5 * gas_price * 1.2}")
                print(f"Total needed for 2 tx (Wei): {est * 1.5 * gas_price * 1.2 * 2}")
                print(f"As MATIC: { (est * 1.5 * gas_price * 1.2 * 2) / 1e18 }")
            except Exception as e:
                print(f"Estimation simulation failed: {e}")
            
        except Exception as e:
            print(f"Error on {rpc}: {e}")

if __name__ == "__main__":
    asyncio.run(test_gas())
