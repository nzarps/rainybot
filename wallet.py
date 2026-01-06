import eth_account
from solders.keypair import Keypair
import base58
import crypto_utils

def generate_evm_wallet():
    """Generate new EVM wallet for ETH/USDT transactions"""
    account = eth_account.Account.create()
    return {
        "address": account.address,
        "private_key": account.key.hex()
    }

async def generate_ltc_wallet(deal_id):
    """Generate LTC wallet safely using a NEW RPC connection for every call."""
    label = f"deal_{deal_id}"

    try:
        # load wallet ALWAYS with new connection
        # 'rainyday' wallet name from original code
        await crypto_utils.rpc_async("loadwallet", "rainyday")
    except:
        pass  # already loaded

    try:
        # SAFE new address
        address = await crypto_utils.rpc_async("getnewaddress", label)

        # SAFE private key dump
        private_key = await crypto_utils.rpc_async("dumpprivkey", address)

        return {
            "address": address,
            "private_key": private_key
        }

    except Exception as e:
        print(f"[LTC-RPC-ERROR] Failed to generate wallet: {e}")
        return None

def generate_solana_wallet():
    kp = Keypair()

    # Secret key = 64 bytes (32 private + 32 public)
    secret_key_bytes = bytes(kp) 
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
        # Maintain compatibility with original code which might raise error or handle it elsewhere
        raise ValueError(f"Unsupported currency: {currency}")
