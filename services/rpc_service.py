
import asyncio
import logging
from typing import List, Any
import aiohttp
import time

logger = logging.getLogger("RPCManager")

class RPCManager:
    def __init__(self):
        self._cache = {}

    async def call_json_rpc(self, urls: List[str], method: str, params: list = None, id: int = 1):
        """
        Attempt JSON-RPC call against a list of URLs with failover and backoff.
        """
        if params is None:
            params = []
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": id
        }

        for i, url in enumerate(urls):
            try:
                # exponential backoff if retrying same URL, but here we rotate
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "result" in data:
                                return data["result"]
                            if "error" in data:
                                logger.warning(f"RPC Error from {url}: {data['error']}")
                        else:
                            logger.warning(f"RPC {url} returned status {resp.status}")
                            
            except Exception as e:
                logger.warning(f"RPC connection failed ({url}): {e}")
            
            # Simple rotation delay
            await asyncio.sleep(0.5)
            
        logger.error(f"All RPCs failed for method {method}")
        return None

rpc_manager = RPCManager()
