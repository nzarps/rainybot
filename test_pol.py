
import asyncio
from web3 import Web3
import os

POLYGON_RPC_URLS = ["https://polygon.llamarpc.com", "https://1rpc.io/matic", "https://rpc.ankr.com/polygon", "https://polygon-rpc.com"]

async def get_evm_confirmations(tx_hash, currency):
    try:
        rpc_urls = {
            "ethereum": [],
            "usdt_polygon": POLYGON_RPC_URLS,
            "usdt_bep20": []
        }.get(currency, [])
        
        if not rpc_urls: return 0
        
        for url in rpc_urls:
            try:
                print(f"Checking RPC: {url}")
                w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 5}))
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                if receipt and receipt.blockNumber:
                    current_block = w3.eth.block_number
                    conf = max(0, current_block - receipt.blockNumber + 1)
                    print(f"Success! Confirmations: {conf}")
                    return conf
            except Exception as e:
                print(f"Error on {url}: {e}")
                continue
    except Exception as e:
        print(f"Global error: {e}")
    return 0

tx = "0x2984aaec720c5dece11f0abc981cf04a2825e9fd6a5aecd72a8ec9598af9aa3b"
async def main():
    confs = await get_evm_confirmations(tx, "usdt_polygon")
    print(f"Final Count: {confs}")

asyncio.run(main())
