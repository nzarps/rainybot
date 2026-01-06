import asyncio
from web3 import AsyncWeb3
import config

class NonceManager:
    """
    Manages nonces for accounts to safe-guard against replacement transaction underpriced errors
    and "nonce too low" errors in high-concurrency environments.
    """
    def __init__(self):
        self._locks = {}
        self._nonces = {}

    def _get_lock(self, address):
        """Get or create an async lock for a specific address"""
        if address not in self._locks:
            self._locks[address] = asyncio.Lock()
        return self._locks[address]

    async def get_next_nonce(self, w3, address):
        """
        Thread-safe method to get the next valid nonce.
        If local nonce is behind chain (app restart), it syncs up.
        If local nonce is ahead (unconfirmed txs), it uses local.
        """
        lock = self._get_lock(address)
        async with lock:
            # Always get the on-chain nonce first to be sure where we stand
            chain_nonce = await w3.eth.get_transaction_count(address)
            
            # Sync local if needed
            # If we don't have a local record, OR chain has moved ahead of us (e.g. from another source/restart)
            if address not in self._nonces or self._nonces[address] < chain_nonce:
                self._nonces[address] = chain_nonce
            
            # Use the local nonce which might be ahead of chain due to pending txs in this memory space
            nonce_to_use = self._nonces[address]
            
            # Increment so the next caller gets the next one
            self._nonces[address] += 1
            
            return nonce_to_use

# Global instance
nonce_manager = NonceManager()
