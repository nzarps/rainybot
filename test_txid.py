#!/usr/bin/env python3
"""Test TXID retrieval for Polygon USDT"""
import asyncio
import aiohttp
import sys

POLYGON_TATUM_RPC = "https://polygon-mainnet.gateway.tatum.io/"
TATUM_KEY = "t-66af694f0692f9f4d1"
USDT_POLYGON_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

async def polygon_tatum_rpc(method, params):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            POLYGON_TATUM_RPC,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            headers={"Content-Type": "application/json", "x-api-key": TATUM_KEY}
        ) as resp:
            return await resp.json()

async def get_txid(address):
    try:
        address = address.lower().replace("0x", "")
        padded_address = "0x" + address.zfill(64)
        
        print(f"[INFO] Padded address: {padded_address}")
        
        data = await polygon_tatum_rpc("eth_blockNumber", [])
        print(f"[INFO] Block number response: {data}")
        
        if "result" not in data:
            print("[ERROR] No result in block number response")
            return None
        
        latest = int(data["result"], 16)
        scan_range = 6000
        start_block = latest - scan_range
        
        print(f"[INFO] Scanning from block {start_block} to {latest}")
        
        params = [{
            "fromBlock": hex(start_block),
            "toBlock": hex(latest),
            "address": USDT_POLYGON_CONTRACT,
            "topics": [TRANSFER_TOPIC, None, padded_address]
        }]
        
        print(f"[INFO] Calling eth_getLogs with params: {params}")
        res = await polygon_tatum_rpc("eth_getLogs", params)
        print(f"[INFO] getLogs response: {res}")
        
        if "result" in res and res["result"]:
            logs = res["result"]
            print(f"[INFO] Found {len(logs)} logs")
            return logs[-1]["transactionHash"]
        else:
            print("[INFO] No logs found")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

if __name__ == "__main__":
    address = sys.argv[1] if len(sys.argv) > 1 else "0x827AFBfCA94f97765076E6511f798249016bC145"
    print(f"\n=== Testing TXID retrieval for: {address} ===\n")
    txid = asyncio.run(get_txid(address))
    print(f"\n[RESULT] TXID: {txid}")
