"""
Wallet Generation Functions
Generates wallets for LTC, EVM (ETH/USDT), and Solana
"""

import asyncio
import base58
from eth_account import Account as EthAccount
from solders.keypair import Keypair
from bitcoinrpc.authproxy import AuthServiceProxy

import config


def rpc_call(method, *params):
    """Single RPC call with a fresh connection (safe for async)."""
    rpc = AuthServiceProxy(config.RPC_URL, timeout=10)
    return getattr(rpc, method)(*params)


async def rpc_async(method, *params):
    """Async wrapper using threads."""
    return await asyncio.to_thread(rpc_call, method, *params)


def generate_evm_wallet():
    """Generate new EVM wallet for ETH/USDT transactions"""
    account = EthAccount.create()
    return {
        "address": account.address,
        "private_key": account.key.hex()
    }


async def generate_ltc_wallet(deal_id):
    """Generate LTC wallet safely using a NEW RPC connection for every call."""
    label = f"deal_{deal_id}"

    try:
        # load wallet ALWAYS with new connection
        await rpc_async("loadwallet", "rainyday")
    except:
        pass  # already loaded

    try:
        # SAFE new address
        address = await rpc_async("getnewaddress", label)

        # SAFE private key dump (optional)
        private_key = await rpc_async("dumpprivkey", address)

        return {
            "address": address,
            "private_key": private_key
        }

    except Exception as e:
        print(f"[LTC-RPC-ERROR] Failed to generate wallet: {e}")
        return None


def generate_solana_wallet():
    """Generate Solana wallet"""
    kp = Keypair()

    # Secret key = 64 bytes (32 private + 32 public)
    secret_key_bytes = bytes(kp)  # THIS RETURNS ALL 64 BYTES
    secret_key_b58 = base58.b58encode(secret_key_bytes).decode()

    return {
        "address": str(kp.pubkey()),
        "private_key": secret_key_b58
    }


async def generate_wallet_for_currency(deal_id, currency):
    """Generate wallet based on selected currency"""
    if currency == 'ltc':
        return await generate_ltc_wallet(deal_id)
    elif currency in ['usdt_bep20', 'usdt_polygon', 'ethereum']:
        return generate_evm_wallet()
    elif currency == 'solana':
        return generate_solana_wallet()
    else:
        raise ValueError(f"Unsupported currency: {currency}")
