import asyncio
import aiohttp
import random

async def get_ltc_confirmations(tx_hash):
    if not tx_hash: return None
    
    # 1. Skip local node for this external test
    print(f"Testing TX: {tx_hash}")

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
        # Define API Callers
        async def check_blockcypher():
            try:
                url = f"https://api.blockcypher.com/v1/ltc/main/txs/{tx_hash}"
                async with session.get(url, timeout=5) as r:
                    if r.status == 200:
                        data = await r.json()
                        if "confirmations" in data: 
                            c = int(data["confirmations"])
                            print(f"BlockCypher: {c}")
                            return c
                    else:
                        print(f"[LTC-CONF] BlockCypher failed: {r.status}")
            except Exception as e:
                print(f"[LTC-CONF] BlockCypher error: {e}")
            return None

        async def check_blockchair():
            try:
                url = f"https://api.blockchair.com/litecoin/dashboards/transaction/{tx_hash}"
                async with session.get(url, timeout=5) as r:
                    if r.status == 200:
                        data = await r.json()
                        val = data.get("data", {}).get(tx_hash, {}).get("transaction")
                        if val and "block_id" in val:
                            block_height = val["block_id"]
                            if block_height != -1:
                                context = data.get("context", {})
                                state_layer = context.get("state_layer")
                                if state_layer: 
                                    c = max(0, state_layer - block_height + 1)
                                    print(f"Blockchair: {c}")
                                    return c
                    else:
                        print(f"[LTC-CONF] Blockchair failed: {r.status}")
            except Exception as e:
                print(f"[LTC-CONF] Blockchair error: {e}")
            return None

        async def check_litecoinspace():
            try:
                url_tx = f"https://litecoinspace.org/api/tx/{tx_hash}"
                async with session.get(url_tx, timeout=5) as r:
                     if r.status == 200:
                        data = await r.json()
                        status = data.get("status", {})
                        if status.get("confirmed"):
                             block_height = status.get("block_height")
                             async with session.get("https://litecoinspace.org/api/blocks/tip/height", timeout=2) as r2:
                                 if r2.status == 200:
                                     tip = int(await r2.text())
                                     c = max(1, tip - block_height + 1)
                                     print(f"LitecoinSpace: {c}")
                                     return c
            except Exception as e:
                print(f"[LTC-CONF] LitecoinSpace error: {e}")
            return None

        async def check_sochain_v3():
             # Code in main.py uses v2, let's try v2 here too
            try:
                url = f"https://chain.so/api/v2/get_tx/LTC/{tx_hash}"
                async with session.get(url, timeout=5) as r:
                    if r.status == 200:
                        d = await r.json()
                        if d.get("status") == "success":
                            c = int(d["data"]["confirmations"])
                            print(f"SoChain: {c}")
                            return c
            except: pass
            return None

        apis = [check_litecoinspace, check_blockcypher, check_blockchair, check_sochain_v3]
        for api in apis:
            res = await api()
            if res is not None:
                print(f"FINAL RESULT from {api.__name__}: {res}")
                # continue to see all results in test
    return None

if __name__ == "__main__":
    tx = "b8ac269ebdbbc65650244678c053876756c0c16e07ceb"
    asyncio.run(get_ltc_confirmations(tx))
