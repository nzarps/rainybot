
import asyncio
from web3 import Web3
import os

# CONFIG FROM config.py
USDT_ABI = [
    {
        "constant": False,
        "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

BSC_RPC_URLS = [
    "https://bsc-dataseed.binance.org",
    "https://bsc-dataseed1.ninicoin.io",
    "https://bsc-dataseed1.defibit.io"
]
USDT_BEP20_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
USDT_BEP20_DECIMALS = 18

POLYGON_RPC_URLS = [
    "https://polygon-rpc.com",
    "https://rpc-mainnet.matic.quiknode.pro"
]
USDT_POLYGON_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
USDT_POLYGON_DECIMALS = 6

TARGET_ADDRESS = "0x036355f850A6Ca00c997AdC779567A38cF251aE4"

async def get_balance(rpc_urls, contract_address, decimals, chain_name):
    async def fetch_balance(rpc):
        try:
            print(f"Checking {chain_name} via {rpc}...")
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if not w3.is_connected():
                print(f"  Failed component connection to {rpc}")
                return None
            
            c_addr = w3.to_checksum_address(contract_address)
            t_addr = w3.to_checksum_address(TARGET_ADDRESS)
            contract = w3.eth.contract(address=c_addr, abi=USDT_ABI)
            
            bal_wei = contract.functions.balanceOf(t_addr).call()
            bal = bal_wei / (10 ** decimals)
            print(f"  Result from {rpc}: {bal} USDT")
            return bal
        except Exception as e:
            print(f"  Error from {rpc}: {e}")
            return None

    tasks = [asyncio.create_task(fetch_balance(url)) for url in rpc_urls]
    done, pending = await asyncio.wait(tasks, timeout=15, return_when=asyncio.FIRST_COMPLETED)
    
    for t in done:
        res = t.result()
        if res is not None:
            return res
            
    print(f"All RPCs failed for {chain_name}")
    return 0.0

async def main():
    print(f"Checking address: {TARGET_ADDRESS}")
    
    print("\n--- BEP20 (BSC) ---")
    bep20_bal = await get_balance(BSC_RPC_URLS, USDT_BEP20_CONTRACT, USDT_BEP20_DECIMALS, "BEP20")
    print(f"Final BEP20 Balance: {bep20_bal}")
    
    print("\n--- POLYGON ---")
    poly_bal = await get_balance(POLYGON_RPC_URLS, USDT_POLYGON_CONTRACT, USDT_POLYGON_DECIMALS, "Polygon")
    print(f"Final Polygon Balance: {poly_bal}")

if __name__ == "__main__":
    asyncio.run(main())
