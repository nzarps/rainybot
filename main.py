import discord
from discord.ext import commands, tasks
import asyncio
import os
import requests
import datetime
from config import CHANNEL_ID, TOKEN, OWNER, CATEGORY_ID_1, CATEGORY_ID_2, LOG_CHANNEL, HISTORY_CHANNEL, EXECUTIVE_ROLE_ID
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button, Select
import pytz
import json
import uuid
from PIL import Image
import qrcode
import aiohttp
import time
import chat_exporter
import io
import aiofiles
import base64
from bitcoinrpc.authproxy import AuthServiceProxy
import random
import string
import secrets
import base58
from web3 import Web3
import eth_account
from web3 import Web3
from eth_account import Account
import asyncio
import random
import time
# =====================================================
# CONFIGURATIONS
# =====================================================

# RPC URLs
# CONSTANT GAS AMOUNTS (SAFE VALUES)
POLYGON_GAS_REQUIRED = 0.027   # MATIC required for USDT Polygon transfer
BEP20_GAS_REQUIRED = 0.00003      # BNB required for USDT BEP20 transfer
POLYGON_RPC = "https://polygon-rpc.com"
BSC_RPC = "https://bsc-dataseed.binance.org/"

# ETHEREUM RPC Configuration
ETH_RPC_URLS = [
    "https://ethereum-rpc.publicnode.com",
    "https://rpc.ankr.com/eth"
]
ETH_DECIMALS = 18

# Chain settings
CHAINS = {
    "usdt_bep20": {
        "rpc": BSC_RPC,
        "chain_id": 56,
        "symbol": "BNB",
        "usdt": "0x55d398326f99059fF775485246999027B3197955",
        "decimals": 18
    },
    "usdt_polygon": {
        "rpc": POLYGON_RPC,
        "chain_id": 137,
        "symbol": "MATIC",
        "usdt": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "decimals": 6
    }
}
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

# LTC RPC Configuration
RPC_USER = "rainyday"
RPC_PASSWORD = ""
RPC_HOST = ""
RPC_PORT = 9332
rpc = AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}")
RPC_URL = "http://rainyday:9332/"

# USDT Configuration
# USDT BEP20 (BNB SMART CHAIN)
USDT_BEP20_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
BEP20_RPC_URLS = [
    "https://bsc-dataseed.binance.org",
    "https://bsc-dataseed1.ninicoin.io",
    "https://bsc-dataseed1.defibit.io"
]
USDT_BEP20_DECIMALS = 18

# USDT POLYGON (POS/MAINNET)
USDT_POLYGON_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
POLYGON_RPC_URLS = [
    "https://polygon-rpc.com",
    "https://rpc-mainnet.matic.quiknode.pro"
]
USDT_POLYGON_DECIMALS = 6

SOLANA_RPC_URLS = [
    "https://solana-rpc.publicnode.com"
]
# =====================================================
# GLOBAL VARIABLES
# =====================================================

pending_force_actions = {}
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
price_cache = {}
CACHE_DURATION = 60

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def create_deal_id(length: int = 64, prefix: str = ""):
    """Generate secure deal ID"""
    charset = string.ascii_lowercase + string.digits
    deal_id = ''.join(secrets.choice(charset) for _ in range(length))
    return f"{prefix}{deal_id}" if prefix else deal_id

def load_all_data():
    if not os.path.exists("data.json"):
        return {}
    with open("data.json", "r") as f:
        return json.load(f)

def save_all_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

def load_counter():
    if not os.path.exists("counter.json"):
        return 0
    with open("counter.json", "r") as f:
        return json.load(f)

def save_counter(counter):
    with open("counter.json", "w") as f:
        json.dump(counter, f)

def get_deal_by_dealid(deal_id):
    data = load_all_data()
    return data.get(deal_id)

def get_deal_by_channel(channel_id):
    data = load_all_data()
    for did, info in data.items():
        if str(info.get("channel_id")) == str(channel_id):
            return did, info
    return None, None

def get_deal_by_address(address):
    data = load_all_data()
    for did, info in data.items():
        if info.get("address") == address:
            return did, info
    return None, None

def update_deal(channel_id, deal_data):
    deal_id, deal = get_deal_by_channel(channel_id)
    if deal_id:
        data = load_all_data()
        data[deal_id] = deal_data
        save_all_data(data)
    else:
        data = load_all_data()
        data[str(channel_id)] = deal_data
        save_all_data(data)

def safe_rpc_call(func, *args, retries=5, delay=1):
    for i in range(retries):
        try:
            return func(*args)
        except Exception as e:
            print(f"RPC error: {e}, retry {i+1}/{retries}")
            time.sleep(delay)
    raise Exception("RPC failed after retries")

import time

def dbg(msg):
    print(f"[LTC-DEBUG] {msg}")

async def get_gas_balance(address, currency):
    """Return BNB (for BEP20) or MATIC (for Polygon) balance"""
    try:
        if currency == "usdt_bep20":
            # Check BNB balance
            for rpc in BEP20_RPC_URLS:
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc))
                    bal = w3.eth.get_balance(address)
                    return float(w3.from_wei(bal, 'ether'))
                except:
                    continue

        elif currency == "usdt_polygon":
            # Check MATIC balance
            for rpc in POLYGON_RPC_URLS:
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc))
                    bal = w3.eth.get_balance(address)
                    return float(w3.from_wei(bal, 'ether'))
                except:
                    continue

    except Exception as e:
        print("Gas balance error:", e)

    return 0.0

async def safe_respond(interaction, *, content=None, embed=None, view=None, ephemeral=False, defer=False, edit_original=False, send_modal=None):
    try:
        if send_modal:
            if not interaction.response.is_done():
                await interaction.response.send_modal(send_modal)
                return True
            return False
        elif defer:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=ephemeral)
            return True
        elif edit_original and interaction.message:
            await interaction.message.edit(content=content, embed=embed, view=view)
            return True
        elif not interaction.response.is_done():
            kwargs = {}
            if content is not None:
                kwargs['content'] = content
            if embed is not None:
                kwargs['embed'] = embed
            if view is not None:
                kwargs['view'] = view
            kwargs['ephemeral'] = ephemeral
            await interaction.response.send_message(**kwargs)
            return True
        else:
            await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
            return True
    except (discord.InteractionResponded, discord.NotFound, discord.HTTPException) as e:
        try:
            if interaction.message and not edit_original:
                await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
                return True
        except:
            pass
        return False
# =====================================================
# WALLET GENERATION
# =====================================================

def generate_evm_wallet():
    """Generate new EVM wallet for ETH/USDT transactions"""
    account = eth_account.Account.create()
    return {
        "address": account.address,
        "private_key": account.key.hex()
    }

from bitcoinrpc.authproxy import AuthServiceProxy
import asyncio

def rpc_call(method, *params):
    """Single RPC call with a fresh connection (safe for async)."""
    rpc = AuthServiceProxy(RPC_URL, timeout=10)
    return getattr(rpc, method)(*params)


async def rpc_async(method, *params):
    """Async wrapper using threads."""
    return await asyncio.to_thread(rpc_call, method, *params)


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
from solders.keypair import Keypair
import base58

def generate_solana_wallet():
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

# =====================================================
# ETHEREUM FUNCTIONS
# =====================================================

async def get_eth_balance_parallel(address):
    """Get ETH balance from multiple RPCs in parallel"""
    async def fetch_balance(rpc_url):
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 5}))
            if not w3.is_connected():
                return None
            balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
            balance_eth = balance_wei / (10 ** 18)
            return float(balance_eth)
        except Exception as e:
            print(f"ETH RPC error ({rpc_url}): {e}")
            return None
    
    tasks = [fetch_balance(url) for url in ETH_RPC_URLS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, (int, float)) and result >= 0:
            return result
    
    return 0.0

async def get_last_eth_txhash(address):
    """Get last incoming ETH transaction hash"""
    address = Web3.to_checksum_address(address)
    
    async def fetch_last_tx(rpc_url):
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 5}))
            if not w3.is_connected():
                return None
            
            # Get latest block
            latest_block = w3.eth.block_number
            
            # Check last 20 blocks for transactions to this address
            for block_num in range(latest_block, latest_block - 20, -1):
                if block_num <= 0:
                    break
                    
                try:
                    block = w3.eth.get_block(block_num, full_transactions=True)
                    for tx in block.transactions:
                        if tx.to and tx.to.lower() == address.lower():
                            return tx.hash.hex()
                except:
                    continue
                    
        except Exception as e:
            print(f"ETH tx detection error ({rpc_url}): {e}")
        return None
    
    tasks = [fetch_last_tx(url) for url in ETH_RPC_URLS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if result and isinstance(result, str):
            return result
    
    return None

async def send_eth(private_key, to_address):
    """
    Sends MAX ETH (balance - gas fee) and ALWAYS returns the txid immediately.
    Never checks if RPC indexed the transaction.
    Works for web3.py v5/v6.
    """
    from eth_account import Account
    from web3 import Web3

    account = Account.from_key(private_key)
    from_address = account.address

    for rpc_url in ETH_RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                continue

            # Get balance and nonce
            balance = w3.eth.get_balance(from_address)
            nonce = w3.eth.get_transaction_count(from_address)

            # Gas settings
            gas_limit = 21000
            gas_price = w3.eth.gas_price

            gas_cost = gas_limit * gas_price

            if balance <= gas_cost:
                raise Exception("Not enough ETH to cover gas.")

            # Send EVERYTHING except gas fee
            amount_to_send = balance - gas_cost

            tx = {
                "nonce": nonce,
                "to": Web3.to_checksum_address(to_address),
                "value": amount_to_send,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "chainId": 1
            }

            # Sign transaction
            signed_tx = w3.eth.account.sign_transaction(tx, private_key)

            # v5/v6 compatibility
            raw_tx = getattr(
                signed_tx,
                "rawTransaction",
                getattr(signed_tx, "raw_transaction", None)
            )

            if raw_tx is None:
                raise Exception("Unable to get raw TX bytes")

            # Send transaction
            tx_hash = w3.eth.send_raw_transaction(raw_tx)

            # 🔥 ALWAYS RETURN TXID DIRECTLY — NO CHECKS
            return tx_hash.hex()

        except Exception as e:
            print(f"ETH send failed ({rpc_url}): {e}")
            continue

    raise Exception("All ETH RPC endpoints failed")

# =====================================================
# PRICE FUNCTIONS
# =====================================================
def estimate_required_gas(contract_address, private_key, to_address, amount, rpc_urls, decimals):
    account = Account.from_key(private_key)
    from_addr = account.address

    amount_wei = int(amount * (10 ** decimals))

    for rpc in rpc_urls:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 5}))
            if not w3.is_connected():
                continue

            contract = w3.eth.contract(
                address=w3.to_checksum_address(contract_address),
                abi=USDT_ABI
            )

            nonce = w3.eth.get_transaction_count(from_addr)

            tx = contract.functions.transfer(
                w3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                "from": from_addr,
                "nonce": nonce,
            })

            gas = w3.eth.estimate_gas(tx)
            gas_price = w3.eth.gas_price

            total_gas_native = (gas * gas_price) / (10 ** 18)

            return float(total_gas_native)

        except Exception as e:
            print("Gas estimation failed on RPC:", rpc, e)
            continue

    return None

async def get_cached_price(currency):
    """Get cached price or fetch new one"""
    current_time = time.time()
    cache_key = f"{currency}_price"
    
    if cache_key in price_cache:
        price, timestamp = price_cache[cache_key]
        if current_time - timestamp < CACHE_DURATION:
            return price
    
    # Fetch new price
    if currency == 'ltc':
        new_price = await get_ltc_price()
    elif currency == 'solana':
        new_price = await get_solana_price()
    elif currency == 'ethereum':
        new_price = await get_ethereum_price()
    else:
        new_price = await get_usdt_price()
    
    price_cache[cache_key] = (new_price, current_time)
    return new_price

async def get_usdt_price():
    """Get USDT price with multiple fallback APIs"""
    apis = [
        "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=usd",
        "https://min-api.cryptocompare.com/data/price?fsym=USDT&tsyms=USD",
        "https://api.binance.com/api/v3/ticker/price?symbol=USDTUSD",
    ]
    
    for api_url in apis:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if "tether" in data and "usd" in data["tether"]:
                            return float(data["tether"]["usd"])
                        
                        if "USD" in data:
                            return float(data["USD"])
                        
                        if "price" in data:
                            return float(data["price"])
                            
        except Exception:
            continue
    
    return 1.0

async def get_ltc_price():
    """Get LTC price with multiple fallback APIs"""
    apis = [
        "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd",
        "https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD",
        "https://api.binance.com/api/v3/ticker/price?symbol=LTCUSDT",
    ]
    
    for api_url in apis:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if "litecoin" in data and "usd" in data["litecoin"]:
                            return float(data["litecoin"]["usd"])
                        
                        if "USD" in data:
                            return float(data["USD"])
                        
                        if "price" in data:
                            return float(data["price"])
                            
        except Exception:
            continue
    
    return 80.0

async def get_solana_price():
    """Get SOL price with multiple fallback APIs"""
    apis = [
        "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd",
        "https://min-api.cryptocompare.com/data/price?fsym=SOL&tsyms=USD",
        "https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT",
    ]
    
    for api_url in apis:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if "solana" in data and "usd" in data["solana"]:
                            return float(data["solana"]["usd"])
                        
                        if "USD" in data:
                            return float(data["USD"])
                        
                        if "price" in data:
                            return float(data["price"])
                            
        except Exception:
            continue
    
    return 150.0

async def get_ethereum_price():
    """Get ETH price with multiple fallback APIs"""
    apis = [
        "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd",
        "https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD",
        "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT",
    ]
    
    for api_url in apis:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if "ethereum" in data and "usd" in data["ethereum"]:
                            return float(data["ethereum"]["usd"])
                        
                        if "USD" in data:
                            return float(data["USD"])
                        
                        if "price" in data:
                            return float(data["price"])
                            
        except Exception:
            continue
    
    return 3000.0

async def usd_to_currency_amount(amount_usd, currency):
    """Convert USD to crypto amount using cached prices"""
    rate = await get_cached_price(currency)
    if rate and rate > 0:
        result = amount_usd / rate
        return round(result, 8)
    
    fallback_rates = {
        'ltc': 80.0,
        'usdt_bep20': 1.0,
        'usdt_polygon': 1.0,
        'solana': 150.0,
        'ethereum': 3000.0
    }
    fallback_rate = fallback_rates.get(currency, 1.0)
    result = amount_usd / fallback_rate
    result = float(f"{result:.8f}")
    return result

async def currency_to_usd(amount, currency):
    """Convert crypto amount to USD using cached prices"""
    rate = await get_cached_price(currency)
    if rate and rate > 0:
        result = amount * rate
        return round(result, 2)
    return 0.0

# =====================================================
# GAS FUNCTIONS
# =====================================================

def get_required_gas(currency):
    if currency == "usdt_polygon":
        return POLYGON_GAS_REQUIRED, "MATIC"
    elif currency == "usdt_bep20":
        return BEP20_GAS_REQUIRED, "BNB"
    return 0, ""

async def check_gas_paid(currency, address, rpc_urls):
    from web3 import Web3

    for url in rpc_urls:
        try:
            w3 = Web3(Web3.HTTPProvider(url))
            bal = w3.eth.get_balance(address) / 1e18

            required_gas, _ = get_required_gas(currency)

            if bal >= required_gas:
                return True

        except:
            continue

    return False


# =====================================================
# SENDING FUNCTIONS
# =====================================================
import asyncio
import logging
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# ---------- LOGGER SETUP ----------
logger = logging.getLogger("LTC_SEND")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def _send_ltc_sync(sendaddy, private_key, to_address, amount):
    rpc = AuthServiceProxy(
        "http://rainyday:",
        timeout=120
    )

    # Import key once (wallet handles segwit metadata)
    try:
        rpc.importprivkey(private_key, "deal_key", False)
    except:
        pass

    utxos = rpc.listunspent(1, 9999999, [sendaddy])
    if not utxos:
        raise Exception("No UTXO found")

    total_balance = sum(u["amount"] for u in utxos)

    if amount is None or amount > total_balance:
        amount = total_balance

    inputs = [{"txid": u["txid"], "vout": u["vout"]} for u in utxos]
    outputs = {to_address: amount}

    raw = rpc.createrawtransaction(inputs, outputs)

    funded = rpc.fundrawtransaction(
        raw,
        {
            "subtractFeeFromOutputs": [0],
            "replaceable": False
        }
    )

    # ✅ WALLET SIGNING (FIX)
    signed = rpc.signrawtransactionwithwallet(funded["hex"])

    if not signed.get("complete"):
        raise Exception(f"Sign failed: {signed}")

    return rpc.sendrawtransaction(signed["hex"])


async def send_ltc(sendaddy, private_key, to_address, amount=None):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _send_ltc_sync,
        sendaddy,
        private_key,
        to_address,
        amount
    )

async def send_usdt(contract_address, private_key, to_address, amount, rpc_urls, decimals, chain_id):
    from eth_account import Account
    from web3 import Web3

    usdt_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        }
    ]

    acc = Account.from_key(private_key)
    from_address = acc.address

    for rpc in rpc_urls:
        print(f"Trying RPC: {rpc}")

        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            if not w3.is_connected():
                print(f"RPC offline: {rpc}")
                continue

            to_checksum = Web3.to_checksum_address(to_address)
            contract = w3.eth.contract(Web3.to_checksum_address(contract_address), abi=usdt_abi)
            from_checksum = Web3.to_checksum_address(from_address)

            # ⭐ FETCH CURRENT USDT BALANCE ⭐
            balance = contract.functions.balanceOf(from_checksum).call()

            print(f"USDT Balance: {balance}")

            if balance <= 0:
                print("❌ Wallet USDT balance is zero. Cannot send.")
                continue  # try next RPC

            # ⭐ SEND FULL BALANCE ⭐
            send_amount = balance

            print(f"➡ Sending full balance: {send_amount}")

            nonce = w3.eth.get_transaction_count(from_address)

            # ⭐ ESTIMATE GAS ⭐
            try:
                estimated_gas = contract.functions.transfer(
                    to_checksum,
                    send_amount
                ).estimate_gas({"from": from_address})
            except Exception as ge:
                print(f"Gas estimation failed: {ge}")
                continue

            tx = contract.functions.transfer(
                to_checksum,
                send_amount
            ).build_transaction({
                "chainId": chain_id,
                "gas": int(estimated_gas * 1.2),
                "gasPrice": w3.eth.gas_price,
                "nonce": nonce
            })

            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print("✅ Transaction sent!")
            return tx_hash.hex()

        except Exception as e:
            print(f"RPC Failed ({rpc}): {e}")
            continue

    raise Exception("All RPC failed or balance was zero")

async def send_solana(private_key_b58, to_address, amount):
    """
    Fully stable Solana sender:
    - Auto subtracts rent exemption
    - Auto subtracts network fee
    - Auto adjusts amount so sending never fails
    - Works with solana-rpc.publicnode.com
    """

    import base58
    import aiohttp
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.system_program import TransferParams, transfer
    from solders.transaction import Transaction
    from solders.message import Message
    from solders.hash import Hash  # required for blockhash

    RPC = "https://solana-rpc.publicnode.com"

    # ================================
    # DECODE PRIVATE KEY
    # ================================
    secret_bytes = base58.b58decode(private_key_b58)
    if len(secret_bytes) != 64:
        raise Exception(f"Invalid private key length ({len(secret_bytes)}) — expected 64 bytes")

    keypair = Keypair.from_bytes(secret_bytes)
    pubkey = keypair.pubkey()

    # ================================
    # HELPERS
    # ================================
    async def rpc(method, params):
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        async with aiohttp.ClientSession() as session:
            async with session.post(RPC, json=payload) as r:
                return await r.json()

    # ================================
    # FETCH BALANCE
    # ================================
    balance_res = await rpc("getBalance", [str(pubkey)])
    lamports_balance = balance_res["result"]["value"]

    # ================================
    # FETCH RENT EXEMPTION
    # ================================
    rent_res = await rpc("getMinimumBalanceForRentExemption", [0])
    rent_exempt = rent_res["result"]

    # Minimum network fee (fixed)
    network_fee = 5000  # lamports ≈ 0.000005 SOL

    # ================================
    # CALCULATE MAX SENDABLE
    # ================================
    max_sendable = lamports_balance - rent_exempt - network_fee

    if max_sendable <= 0:
        raise Exception(
            "This wallet does not have enough SOL to send anything "
            f"(balance={lamports_balance}, rent={rent_exempt})."
        )

    requested_lamports = int(amount * 1_000_000_000)

    # Auto adjust if user requested too much
    if requested_lamports > max_sendable:
        print(f"⚠ Adjusting amount from {requested_lamports} → {max_sendable} (max safe)")
        requested_lamports = max_sendable

    if requested_lamports <= 0:
        raise Exception("Requested send amount too small after fee + rent deduction.")

    # ================================
    # GET LATEST BLOCKHASH
    # ================================
    blockhash_res = await rpc("getLatestBlockhash", [{"commitment": "finalized"}])
    blockhash_str = blockhash_res["result"]["value"]["blockhash"]
    blockhash = Hash.from_string(blockhash_str)

    # ================================
    # BUILD TRANSFER INSTRUCTION
    # ================================
    ix = transfer(
        TransferParams(
            from_pubkey=pubkey,
            to_pubkey=Pubkey.from_string(to_address),
            lamports=requested_lamports
        )
    )

    # ================================
    # BUILD TRANSACTION
    # ================================
    msg = Message.new_with_blockhash([ix], pubkey, blockhash)
    tx = Transaction.new_unsigned(msg)
    tx.sign([keypair], blockhash)

    # MUST SEND BASE64 (NOT BASE58)
    import base64
    tx_base64 = base64.b64encode(bytes(tx)).decode()

    # ================================
    # SEND TRANSACTION
    # ================================
    send_res = await rpc("sendTransaction", [tx_base64, {"encoding": "base64"}])

    if "result" in send_res:
        return send_res["result"]  # tx signature

    raise Exception(f"SEND ERROR: {send_res}")

async def send_usdt_wallet_with_gas_embed(interaction, deal_id, currency, address):
    """Send panel with USDT + Gas payment instructions"""

    # Load deal
    data = load_all_data()
    deal = data[deal_id]

    # Amount user must send (USDT)
    usdt_amount = deal["amount"]

    # GAS required based on network
    if currency == "usdt_polygon":
        gas_required = POLYGON_GAS_REQUIRED
        gas_name = "MATIC"
    else:
        gas_required = BEP20_GAS_REQUIRED
        gas_name = "BNB"

    # Save required gas to deal
    deal["gas_required"] = gas_required
    deal["gas_paid"] = False
    data[deal_id] = deal
    save_all_data(data)

    embed = discord.Embed(
        title="Payment Required",
        color=0x0000ff,
        description="Please complete the payments below to continue the deal."
    )

    embed.add_field(
        name="USDT Payment",
        value=f"Send **{usdt_amount} USDT** to:\n`{address}`",
        inline=False
    )

    embed.add_field(
        name=f"{gas_name} Gas Fee",
        value=f"Send **{gas_required:.6f} {gas_name}** to the SAME address:\n`{address}`",
        inline=False
    )

    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/1438896774243942432/1446526617403920537/discotools-xyz-icon_7.png?ex=69344e64&is=6932fce4&hm=b330f1e3fb9fa6327bbcfcd5cf1e81eb3cf70e5671f8cff6e3bc8a2256e60f89&"
    )

    embed.set_footer(text="Both USDT and Gas must be received before deal begins.")

    # Send embed
    await interaction.followup.send(embed=embed)

    # Return for next steps
    return True

async def send_funds_based_on_currency(deal_info, to_address, amount=None):
    """Send funds based on deal currency"""
    currency = deal_info.get('currency', 'ltc')
    send_address = deal_info.get('address')
    private_key = deal_info.get('private_key')
    
    if currency == 'ltc':
        if amount is None:
            amount = deal_info.get('ltc_amount')
        return await send_ltc(send_address, private_key, to_address, amount)
    
    elif currency == 'usdt_bep20':
        if amount is None:
            amount = deal_info.get('ltc_amount')
        return await send_usdt(
            USDT_BEP20_CONTRACT, 
            private_key, 
            to_address, 
            amount, 
            BEP20_RPC_URLS, 
            USDT_BEP20_DECIMALS,
            chain_id=56
        )
    
    elif currency == 'usdt_polygon':
        if amount is None:
            amount = deal_info.get('ltc_amount')
        return await send_usdt(
            USDT_POLYGON_CONTRACT,
            private_key,
            to_address,
            amount,
            POLYGON_RPC_URLS,
            USDT_POLYGON_DECIMALS, 
            chain_id=137
        )
    
    elif currency == 'solana':
        if amount is None:
            amount = deal_info.get('ltc_amount')
        return await send_solana(private_key, to_address, amount)
    
    elif currency == 'ethereum':
        if amount is None:
            amount = deal_info.get('ltc_amount')
        return await send_eth(private_key, to_address)
    
    else:
        raise ValueError(f"Unsupported currency: {currency}")

# =====================================================
# BALANCE CHECKING FUNCTIONS
# =====================================================

async def get_usdt_balance_parallel(contract_address, wallet, rpc_urls, decimals):
    async def fetch_balance(rpc):
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 5}))
            if not w3.is_connected():
                return None
            contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=USDT_ABI)
            bal = contract.functions.balanceOf(w3.to_checksum_address(wallet)).call()
            return bal / (10 ** decimals)
        except:
            return None

    tasks = [asyncio.create_task(fetch_balance(url)) for url in rpc_urls]
    done, pending = await asyncio.wait(tasks, timeout=5, return_when=asyncio.FIRST_COMPLETED)

    for p in pending:
        p.cancel()

    for d in done:
        if d.result() is not None:
            return d.result()

    return 0.0

async def get_solana_balance_parallel(address):
    """Get Solana balance from multiple RPCs in parallel"""
    import aiohttp
    import asyncio
    
    async def fetch_balance(rpc_url):
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [address]
                }
                async with session.post(rpc_url, json=payload, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'result' in data and 'value' in data['result']:
                            balance_lamports = data['result']['value']
                            balance_sol = balance_lamports / 1_000_000_000
                            return float(balance_sol)
        except Exception as e:
            print(f"Solana RPC error ({rpc_url}): {e}")
        return None
    
    tasks = [fetch_balance(url) for url in SOLANA_RPC_URLS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, (int, float)) and result >= 0:
            return result
    
    return 0.0

async def get_solana_transactions(address):
    """Get recent transactions for Solana address"""
    import aiohttp
    import asyncio
    
    async def fetch_transactions(rpc_url):
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignaturesForAddress",
                    "params": [address, {"limit": 10}]
                }
                async with session.post(rpc_url, json=payload, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'result' in data:
                            return data['result']
        except Exception:
            pass
        return None
    
    tasks = [fetch_transactions(url) for url in SOLANA_RPC_URLS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if result and isinstance(result, list):
            return result
    
    return []

async def get_solana_transaction_details(tx_signature):
    """Get detailed transaction information"""
    import aiohttp
    import asyncio
    
    async def fetch_tx_details(rpc_url):
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [tx_signature, {"encoding": "json"}]
                }
                async with session.post(rpc_url, json=payload, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('result')
        except Exception:
            pass
        return None
    
    tasks = [fetch_tx_details(url) for url in SOLANA_RPC_URLS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if result:
            return result
    
    return None

# =====================================================
# FINAL UPDATED api_get_status() WITH TATUM + MEMPOOL
# =====================================================
from config import PROXY

def build_proxy_url():
    if not PROXY:
        return None
    return f"http://{PROXY}"

TATUM_LTC_RPC = "https://litecoin-mainnet.gateway.tatum.io/"
TATUM_LTC_HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": "t-66af6dd55d631f0041bd40094f0692f9f4d1"
}
BLOCKCYPHER_KEY = "cddb986"

async def tatum_ltc_balance(session, address):
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getreceivedbyaddress",
            "params": [address, 0]
        }
        async with session.post(
            TATUM_LTC_RPC,
            json=payload,
            headers=TATUM_LTC_HEADERS,
            timeout=3
        ) as r:
            data = await r.json()
            if "result" in data:
                return float(data["result"])
    except:
        return None

async def blockcypher_ltc_balance(session, address):
    try:
        url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}?token={BLOCKCYPHER_KEY}"
        async with session.get(url, timeout=3) as r:
            if r.status == 200:
                data = await r.json()
                return data.get("balance", 0) / 1e8
    except:
        return None

async def litecoinspace_ltc_balance(session, address):
    """LitecoinSpace with rotating proxy (fastest)"""
    try:
        proxy_url = build_proxy_url()
        url = f"https://litecoinspace.org/api/address/{address}"

        async with session.get(url, proxy=proxy_url, timeout=1.5) as r:
            if r.status != 200:
                return None

            d = await r.json()
            funded = d["chain_stats"]["funded_txo_sum"]
            spent = d["chain_stats"]["spent_txo_sum"]
            return (funded - spent) / 1e8

    except:
        return None

async def tatum_ltc_received(address):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getreceivedbyaddress",
                "params": [address, 0]
            }
            async with session.post(LTC_TATUM_RPC, json=payload, headers=LTC_TATUM_HEADERS, timeout=6) as r:
                data = await r.json()
                if "result" in data:
                    return float(data["result"])
    except:
        pass
    return None

async def tatum_ltc(method, params):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                TATUM_LTC_RPC,
                headers=TATUM_LTC_HEADERS,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                timeout=4,
            ) as r:
                return await r.json()
    except:
        return None


async def fetch_mempool_status(session, address):
    """absolute last fallback (never rate limits)"""
    try:
        url = f"https://mempool.space/api/address/{address}"
        async with session.get(url, timeout=4) as r:
            if r.status != 200:
                return None
            
            d = await r.json()

            conf = (
                d["chain_stats"]["funded_txo_sum"]
                - d["chain_stats"]["spent_txo_sum"]
            ) / 1e8

            unconf = (
                d["mempool_stats"]["funded_txo_sum"]
                - d["mempool_stats"]["spent_txo_sum"]
            ) / 1e8

            return {
                "confirmed": conf,
                "unconfirmed": unconf,
                "txids": [],
                "source": "mempool"
            }
    except:
        return None

async def safe_respond(interaction, *, content=None, embed=None, view=None, ephemeral=False, defer=False, edit_original=False):
    try:
        if defer:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=ephemeral)
            return True
        elif edit_original and interaction.message:
            await interaction.message.edit(content=content, embed=embed, view=view)
            return True
        elif not interaction.response.is_done():
            kwargs = {}
            if content is not None:
                kwargs['content'] = content
            if embed is not None:
                kwargs['embed'] = embed
            if view is not None:
                kwargs['view'] = view
            kwargs['ephemeral'] = ephemeral
            await interaction.response.send_message(**kwargs)
            return True
        else:
            await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
            return True
    except (discord.InteractionResponded, discord.NotFound, discord.HTTPException) as e:
        try:
            if interaction.message and not edit_original:
                await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
                return True
        except:
            pass
        return False

async def safe_modal(interaction, modal):
    """Safe way to send modals"""
    try:
        if not interaction.response.is_done():
            await interaction.response.send_modal(modal)
            return True
        return False
    except (discord.InteractionResponded, discord.NotFound, discord.HTTPException):
        return False

async def fetch_tatum_status(address):
    """lightweight fallback when all public APIs fail"""
    try:
        bal = await tatum_ltc("getBalance", [address])
        if not bal or "result" not in bal:
            return None
        
        confirmed = float(bal["result"]) / 1e8

        return {
            "confirmed": confirmed,
            "unconfirmed": 0.0,
            "txids": [],
            "source": "tatum"
        }
    except:
        return None


# =====================================================
# UPDATED MAIN STATUS FUNCTION (DROP-IN REPLACEMENT)
# =====================================================
async def api_get_status(address: str):
    """
    FINAL ultra-fast LTC balance checker.
    Priority:
        1) LitecoinSpace 40–90ms
        2) BlockCypher
        3) SoChain
    Always returns confirmed + unconfirmed
    """
    #print(f"[LTC] Checking balance → {address}")

    proxy_url = build_proxy_url()

    async with aiohttp.ClientSession() as session:

        # ① LITECOINSPACE (FASTEST)
        try:
            url = f"https://litecoinspace.org/api/address/{address}"
            async with session.get(url, proxy=proxy_url, timeout=1.2) as r:
                if r.status == 200:
                    d = await r.json()
                    conf = (d["chain_stats"]["funded_txo_sum"] - d["chain_stats"]["spent_txo_sum"]) / 1e8
                    unconf = (d["mempool_stats"]["funded_txo_sum"] - d["mempool_stats"]["spent_txo_sum"]) / 1e8
                    return {"confirmed": conf, "unconfirmed": unconf}
        except Exception as e:
            None#print("[LTC] LitecoinSpace fail →", e)

        # ② BLOCKCYPHER
        try:
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}?token={BLOCKCYPHER_KEY}"
            async with session.get(url, timeout=2) as r:
                if r.status == 200:
                    d = await r.json()
                    conf = d.get("balance", 0) / 1e8
                    unconf = d.get("unconfirmed_balance", 0) / 1e8
                    return {"confirmed": conf, "unconfirmed": unconf}
        except:
            pass

        # ③ SOCHAIN
        try:
            url = f"https://sochain.com/api/v2/address/LTC/{address}"
            async with session.get(url, timeout=2) as r:
                d = await r.json()
                data = d["data"]
                return {
                    "confirmed": float(data["confirmed_balance"]),
                    "unconfirmed": float(data["unconfirmed_balance"])
                }
        except:
            pass

    return {"confirmed": 0.0, "unconfirmed": 0.0}

async def fetch_blockcypher_status(session, address: str):
    try:
        url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}"
        async with session.get(url, timeout=4) as resp:
            if resp.status != 200:
                return None

            data = await resp.json()

            confirmed = data.get("balance", 0) / 1e8
            unconfirmed = data.get("unconfirmed_balance", 0) / 1e8

            txids = []
            for t in data.get("txrefs", []) or []:
                if t.get("tx_hash"):
                    txids.append(t["tx_hash"])
            for t in data.get("unconfirmed_txrefs", []) or []:
                if t.get("tx_hash"):
                    txids.append(t["tx_hash"])

            return {
                "confirmed": confirmed,
                "unconfirmed": unconfirmed,
                "txids": txids,
                "source": "blockcypher"
            }
    except:
        return None


async def fetch_sochain_status(session, address: str):
    try:
        url = f"https://sochain.com/api/v2/address/LTC/{address}"
        async with session.get(url, timeout=4) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
            if payload.get("status") != "success":
                return None

            data = payload["data"]

            txids = [t["txid"] for t in data.get("txs", []) if t.get("txid")]

            return {
                "confirmed": float(data.get("confirmed_balance", 0)),
                "unconfirmed": float(data.get("unconfirmed_balance", 0)),
                "txids": txids,
                "source": "sochain"
            }
    except:
        return None

async def fetch_blockchair_status(session, address: str):
    try:
        url = f"https://api.blockchair.com/litecoin/dashboards/address/{address}"
        async with session.get(url, timeout=8) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            d = data.get("data", {})
            if not d:
                return None

            key = next(iter(d.keys()))
            addr_info = d[key]["address"]
            txs = d[key].get("transactions", [])

            bal_sat = int(addr_info.get("balance", 0))
            unconf_sat = int(addr_info.get("unconfirmed_balance", 0))

            confirmed = bal_sat / 1e8
            unconfirmed = unconf_sat / 1e8

            return {
                "confirmed": float(confirmed),
                "unconfirmed": float(unconfirmed),
                "txids": txs,
                "source": "blockchair",
            }
    except:
        return None

async def fetch_litecoinspace_txid(session, address: str):
    try:
        url = f"https://litecoinspace.org/api/address/{address}/txs"
        async with session.get(url, timeout=3) as r:
            if r.status != 200:
                return None
            data = await r.json()

            if isinstance(data, list) and len(data) > 0:
                return {
                    "txids": [data[0].get("txid")],
                    "source": "litecoinspace"
                }
    except:
        return None

def get_hash(address):
    endpoint = f"https://litecoinspace.org/api/address/{address}/txs"
    response = requests.get(endpoint)

    if response.status_code != 200:
        return None

    data = response.json()

    if isinstance(data, list) and len(data) > 0:
        latest_tx = data[0]
        return latest_tx.get("txid")
    else:
        return None

# =====================================================
# PAYMENT DETECTION SYSTEM
# =====================================================

import aiohttp
import asyncio
import functools

async def get_ltc_confirmed_balance(address: str):
    """
    FAST confirmed balance checker with:
    1. RPC (instant, best)
    2. LitecoinSpace fallback
    3. BlockCypher fallback
    """

    # 1) TRY NODE FIRST (PRUNE MODE OK)
    try:
        utxos = rpc.listunspent(1, 999999999, [address])  # minconf=1
        total = sum(u["amount"] for u in utxos)
        return float(total)
    except Exception:
        pass

    # 2) FALLBACK → LITECOINSPACE
    try:
        url = f"https://litecoinspace.org/api/address/{address}"
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=5) as r:
                if r.status == 200:
                    data = await r.json()
                    confirmed = data["chain_stats"]["funded_txo_sum"] - data["chain_stats"]["spent_txo_sum"]
                    return confirmed / 1e8
    except:
        pass

    # 3) FALLBACK → BLOCKCYPHER (SLOWER, LAST RESORT)
    try:
        url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}"
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=5) as r:
                if r.status == 200:
                    data = await r.json()
                    bal = data.get("balance", 0)
                    return bal / 1e8
    except:
        pass

    return 0.0

async def run_blocking(func, *args):
    loop = asyncio.get_event_loop()
    partial = functools.partial(func, *args)
    return await loop.run_in_executor(None, partial)

async def get_balance_async(address):
    """Safe, fast, fully non-blocking LTC balance checker."""
    async with aiohttp.ClientSession() as session:

        # BlockCypher
        try:
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}"
            async with session.get(url, timeout=6) as r:
                if r.status == 200:
                    data = await r.json()
                    return (
                        data.get("balance", 0) / 1e8,
                        data.get("unconfirmed_balance", 0) / 1e8
                    )
        except:
            pass

        # SoChain (fallback)
        try:
            url = f"https://sochain.com/api/v2/address/LTC/{address}"
            async with session.get(url, timeout=6) as r:
                data = await r.json()
                d = data["data"]
                return (
                    float(d["confirmed_balance"]),
                    float(d["unconfirmed_balance"])
                )
        except:
            pass

    return 0.0, 0.0

def get_balance(address):
    """Get LTC balance from multiple APIs"""
    confirmed = 0.0
    unconfirmed = 0.0

    try:
        r = requests.get(f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}")
        data = r.json()
        confirmed = data.get("balance", 0) / 1e8
        unconfirmed = data.get("unconfirmed_balance", 0) / 1e8
        return confirmed, unconfirmed
    except:
        pass

    try:
        r = requests.get(f"https://api.blockchain.info/balance?active={address}")
        data = r.json().get(address, {})
        confirmed = data.get("final_balance", 0) / 1e8
        unconfirmed = data.get("unconfirmed_balance", 0) / 1e8
        return confirmed, unconfirmed
    except:
        pass

    try:
        r = requests.get(f"https://sochain.com/api/v2/address/LTC/{address}")
        data = r.json()["data"]
        confirmed = float(data["confirmed_balance"])
        unconfirmed = float(data["unconfirmed_balance"])
        return confirmed, unconfirmed
    except:
        pass

    return 0.0, 0.0

async def get_ltc_txid_async(address: str):
    """
    FINAL Guaranteed LTC TXID Finder
    1) LitecoinSpace unconfirmed txs
    2) LitecoinSpace confirmed txs
    3) BlockCypher
    4) SoChain
    Returns real txid always.
    """

    #print(f"[LTC-TXID] Fetching txid for {address}")

    proxy_url = build_proxy_url()

    async with aiohttp.ClientSession() as session:

        # ① LITECOINSPACE — CHECK UNCONFIRMED FIRST
        try:
            url = f"https://litecoinspace.org/api/address/{address}/txs/mempool"
            async with session.get(url, proxy=proxy_url, timeout=1.2) as r:
                if r.status == 200:
                    txs = await r.json()
                    if txs:
                        print("[LTC-TXID] mempool found →", txs[0]["txid"])
                        return txs[0]["txid"]
        except Exception as e:
            print("[LTC-TXID] Mempool fail →", e)

        # ② LITECOINSPACE — CONFIRMED TX LIST
        try:
            url = f"https://litecoinspace.org/api/address/{address}/txs"
            async with session.get(url, proxy=proxy_url, timeout=1.5) as r:
                if r.status == 200:
                    txs = await r.json()
                    if txs:
                        print("[LTC-TXID] confirmed found →", txs[0]["txid"])
                        return txs[0]["txid"]
        except:
            pass

        # ③ BLOCKCYPHER
        try:
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}?token={BLOCKCYPHER_KEY}"
            async with session.get(url, timeout=1.5) as r:
                if r.status == 200:
                    d = await r.json()
                    all_txs = (d.get("txrefs") or []) + (d.get("unconfirmed_txrefs") or [])
                    if all_txs:
                        return all_txs[0]["tx_hash"]
        except:
            pass

        # ④ SOCHAIN
        try:
            url = f"https://sochain.com/api/v2/address/LTC/{address}"
            async with session.get(url, timeout=1.5) as r:
                d = await r.json()
                data = d["data"]
                if data.get("txs"):
                    return data["txs"][0]["txid"]
        except:
            pass

    return None

def gas_needed_for_currency(currency):
    if currency == "usdt_polygon":
        return POLYGON_GAS_REQUIRED, "MATIC"
    elif currency == "usdt_bep20":
        return BEP20_GAS_REQUIRED, "BNB"
    return 0, ""

POLYGON_TATUM_RPC = "https://polygon-mainnet.gateway.tatum.io/"
POLYGON_TATUM_HEADERS = {
    "Content-Type": "application/json",
    "Accept-Encoding": "identity",
    "x-api-key": "t-66af6dd55d631f002f9f4d1"  # same key works
}

USDT_POLYGON_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"

async def polygon_tatum_rpc(method, params):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            POLYGON_TATUM_RPC,
            headers=POLYGON_TATUM_HEADERS,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        ) as r:
            return await r.json()


async def get_usdt_polygon_txid_tatum(address):
    try:
        if not address.startswith("0x"):
            address = "0x" + address
        address = address.lower()

        data = await polygon_tatum_rpc("eth_blockNumber", [])
        if "result" not in data:
            return None

        latest = int(data["result"], 16)
        start = latest - 1200  # scan window

        params = [{
            "fromBlock": hex(start),
            "toBlock": hex(latest),
            "address": USDT_POLYGON_CONTRACT,
            "topics": [TRANSFER_TOPIC]
        }]

        logs_data = await polygon_tatum_rpc("eth_getLogs", params)
        logs = logs_data.get("result", [])

        for log in reversed(logs):
            if len(log["topics"]) < 3:
                continue

            to_addr = "0x" + log["topics"][2][-40:]
            if to_addr.lower() == address:
                return log["transactionHash"]

        return None

    except:
        return None

TATUM_RPC = "https://bsc-mainnet.gateway.tatum.io/"
TATUM_HEADERS = {
    "Content-Type": "application/json",
    "Accept-Encoding": "identity",
    "x-api-key": "t-66af694f0692f9f4d1"  # <- your real key here
}

USDT_BEP20_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


async def tatum_rpc(method, params):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            TATUM_RPC,
            headers=TATUM_HEADERS,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        ) as r:
            return await r.json()


async def tatum_get_latest_block():
    data = await tatum_rpc("eth_blockNumber", [])
    if "result" in data:
        return int(data["result"], 16)
    return None


async def tatum_get_usdt_logs(start_block, end_block):
    params = [{
        "fromBlock": hex(start_block),
        "toBlock": hex(end_block),
        "address": USDT_BEP20_CONTRACT,
        "topics": [TRANSFER_TOPIC]
    }]
    data = await tatum_rpc("eth_getLogs", params)
    return data.get("result", [])


async def get_usdt_bep20_txid_tatum(address):
    """Pure blockchain USDT-BEP20 TXID detector (most reliable)"""
    try:
        address = address.lower()
        if not address.startswith("0x"):
            address = "0x" + address

        latest = await tatum_get_latest_block()
        if not latest:
            return None

        start_block = latest - 700
        logs = await tatum_get_usdt_logs(start_block, latest)

        for log in reversed(logs):
            if len(log["topics"]) < 3:
                continue

            to_addr = "0x" + log["topics"][2][-40:]
            if to_addr.lower() == address.lower():
                return log["transactionHash"]

        return None
    except:
        return None

async def fetch_txid_ultimate(address, currency, max_attempts=8):

    for _ in range(max_attempts):

        # ---------------------------
        # USDT BEP20 → USE TATUM RPC
        # ---------------------------
        if currency == "usdt_bep20":
            txid = await get_usdt_bep20_txid_tatum(address)
            if txid:
                return txid

        # ---------------------------
        # USDT POLYGON → KEEP OLD WORKING
        # ---------------------------
        elif currency == "usdt_polygon":
            txid = await get_usdt_polygon_txid_tatum(address)
            if txid:
                return txid

        # ---------------------------
        # OTHER CHAINS (unchanged)
        # ---------------------------
        elif currency == "ltc":
            return await get_ltc_txid_async(address)
            # s = await api_get_status(address)
           # if s.get("txids"):
               # return s["txids"][-1]

        elif currency == "solana":
            txs = await get_solana_transactions(address)
            if txs:
                return txs[0].get("signature")

        elif currency == "ethereum":
            return await get_last_eth_txhash(address)

        await asyncio.sleep(2)

    return None

# ========================================
# MAIN PAYMENT CHECK FUNCTION
# ========================================
async def check_payment_multicurrency(address, channel, expected_amount, deal_info, msg):
    currency = deal_info.get("currency")
    deal_id = deal_info.get("deal_id")
    buyer = deal_info.get("buyer")
    seller = deal_info.get("seller")

    monitoring_start_time = time.time()
    deal_creation_time = deal_info.get("start_time", monitoring_start_time)
    payment_timeout = deal_info.get("payment_timeout", 1200)
    absolute_expiry_time = deal_creation_time + 3600

    gas_warning_sent = False
    last_balance = 0
    rescan_message = None

    while True:
        current_time = time.time()
        monitoring_elapsed = current_time - monitoring_start_time

        # ======================
        # DEAL ABSOLUTE EXPIRY
        # ======================
        if current_time >= absolute_expiry_time:
            if rescan_message:
                try: await rescan_message.delete()
                except: pass

            await channel.send(
                embed=discord.Embed(
                    title="Deal Expired",
                    description=">>> Deal has been open for 1 hour. Closing.",
                    color=0xff0000
                )
            )
            try: await msg.delete()
            except: pass
            return

        # ======================
        # TIMEOUT (NO PAYMENT)
        # ======================
        if monitoring_elapsed >= payment_timeout and rescan_message is None:

            try:
                if currency == "ltc":
                    total = await get_ltc_confirmed_balance(address)
                elif currency == "usdt_bep20":
                    total = await get_usdt_balance_parallel(USDT_BEP20_CONTRACT, address, BEP20_RPC_URLS, USDT_BEP20_DECIMALS)
                elif currency == "usdt_polygon":
                    total = await get_usdt_balance_parallel(USDT_POLYGON_CONTRACT, address, POLYGON_RPC_URLS, USDT_POLYGON_DECIMALS)
                elif currency == "solana":
                    total = await get_solana_balance_parallel(address)
                elif currency == "ethereum":
                    total = await get_eth_balance_parallel(address)
                else:
                    total = 0
            except:
                total = 0

            # Only show timeout if still no payment
            if total == 0:
                remaining = absolute_expiry_time - current_time
                minutes_left = int(remaining // 60)

                timeout_embed = discord.Embed(
                    title="Payment Timeout",
                    description=f">>> No payment detected within {payment_timeout//60} minutes.\n\nYou still have {minutes_left} minutes to complete the payment.\n\nClick below to extend payment time by 20 minutes.",
                    color=0xffa500
                )
                rescan_message = await channel.send(embed=timeout_embed, view=RescanButton())

                # Wait for rescan or expiry
                while True:
                    await asyncio.sleep(5)

                    if time.time() >= absolute_expiry_time:
                        try: await rescan_message.delete()
                        except: pass
                        await channel.send(embed=discord.Embed(
                            title="Deal Expired",
                            description=">>> 1 hour passed. Deal closed.",
                            color=0xff0000
                        ))
                        return

                    updated_deal = get_deal_by_channel(channel.id)
                    if updated_deal and updated_deal["payment_timeout"] > payment_timeout:
                        payment_timeout = updated_deal["payment_timeout"]
                        monitoring_start_time = time.time()
                        try: await rescan_message.delete()
                        except: pass
                        rescan_message = None
                        await channel.send(embed=discord.Embed(
                            title="Payment Time Extended",
                            description=">>> +20 minutes added.",
                            color=0x00ff00
                        ))
                        break

        # If timeout UI active → pause checks
        if rescan_message:
            await asyncio.sleep(5)
            continue

        await asyncio.sleep(6)

        # ======================
        # MAIN BALANCE CHECK
        # ======================
        try:
            if currency == "ltc":
                s = await api_get_status(address)
                total = float(s["confirmed"] + s["unconfirmed"])
            elif currency == "usdt_bep20":
                total = await get_usdt_balance_parallel(USDT_BEP20_CONTRACT, address, BEP20_RPC_URLS, USDT_BEP20_DECIMALS)
            elif currency == "usdt_polygon":
                total = await get_usdt_balance_parallel(USDT_POLYGON_CONTRACT, address, POLYGON_RPC_URLS, USDT_POLYGON_DECIMALS)
            elif currency == "solana":
                total = await get_solana_balance_parallel(address)
            elif currency == "ethereum":
                total = await get_eth_balance_parallel(address)
            else:
                total = 0
        except:
            continue

        # GAS CHECK (USDT)
        if currency in ["usdt_bep20", "usdt_polygon"] and total > 0:
            if total > last_balance:
                last_balance = total
                await asyncio.sleep(4)

            needed, symbol = gas_needed_for_currency(currency)
            gas_bal = await get_gas_balance(address, currency)

            if gas_bal < needed:
                if not gas_warning_sent:
                    gas_warning_sent = True
                    txid = await fetch_txid_ultimate(address, currency)

                    await channel.send(embed=discord.Embed(
                        title=f"{symbol} Required For Network Fee",
                        color=0x0000ff,
                        description=f"USDT received but insufficient {symbol}.\n\nTXID: `{txid or 'Indexing...'}`\nReceived: `{total}`"
                    ))
                continue

            gas_warning_sent = False

        # PARTIAL
        if 0 < total < float(expected_amount):
            txid = await fetch_txid_ultimate(address, currency)
            await handle_partial_payment_fast(channel, deal_info, total, expected_amount, currency, msg, txid)
            return

        # FULL
        if total >= float(expected_amount):
            txid = await fetch_txid_ultimate(address, currency)
            await handle_full_payment(channel, deal_info, total, expected_amount, currency, address, msg, txid)
            return

# ========================================
# PARTIAL PAYMENT HANDLER (Original UI + Fast TXID)
# ========================================
async def handle_partial_payment_fast(channel, deal_info, received, expected, currency, msg, tx_hash):
    """
    PARTIAL PAYMENT HANDLER (Option A)
    - LTC → keep NEW UI & behavior (DO NOT TOUCH)
    - All other coins → restore OLD UI & explorer links
    """

    deal_id = deal_info["deal_id"]
    buyer = deal_info["buyer"]          # RECEIVER
    seller = deal_info["seller"]        # SENDER
    address = deal_info.get("address")

    # Convert to USD
    usd_received = await currency_to_usd(received, currency)
    usd_expected = await currency_to_usd(expected, currency)

    # Save updated amounts
    data = load_all_data()
    data[deal_id]["ltc_amount"] = float(received)
    data[deal_id]["amount"] = float(usd_received)
    save_all_data(data)

    # Display names
    cur_name = {
        "ltc": "LTC",
        "usdt_bep20": "USDT (BEP20)",
        "usdt_polygon": "USDT (Polygon)",
        "solana": "SOL",
        "ethereum": "ETH"
    }.get(currency, "Crypto")

    # ============================================================
    # FORCE TXID DETECTION IF NOT PROVIDED
    # ============================================================
    if not tx_hash:
        tx_hash = await fetch_txid_ultimate(address, currency, max_attempts=12)

    # ============================================================
    # SPECIAL CASE → LTC USES YOUR NEW LOGIC (DO NOT TOUCH)
    # ============================================================
    if currency == "ltc":
        # Build NEW UI (your preferred design)
        embed = discord.Embed(
            title="Transaction Detected (Partial)",
            color=0x0000ff,
            description="Received **less** than required. Confirm to proceed."
        )

        if tx_hash:
            explorer = f"https://live.blockcypher.com/ltc/tx/{tx_hash}/"
            embed.add_field(
                name="Transaction Hash",
                value=f"[{tx_hash}]({explorer})",
                inline=False
            )
        else:
            embed.add_field(name="Transaction Hash", value="Indexing...", inline=False)

        embed.add_field(name="Received (LTC)", value=f"`{received} | ${usd_received}`")
        embed.add_field(name="Required (LTC)", value=f"`{expected} | ${usd_expected}`")

        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1438896774243942432/1446526617403920537/discotools-xyz-icon_7.png"
        )

        try: await msg.delete()
        except: pass

        try:
            history = [m async for m in channel.history(limit=1, oldest_first=True)]
            await history[0].edit(view=ToSButtonsAllInOnee())
        except:
            pass

        await channel.send(f"<@{seller}>", embed=embed, view=ProceedButton())
        await channel.send(embed=discord.Embed(
            title="Waiting for confirmation",
            description="-# Don't pay extra before confirming.",
            color=0xfffff0
        ))
        return

    # ============================================================
    # OLD UI RESTORATION FOR USDT / SOL / ETH (Option A)
    # ============================================================

    # GAS CHECK FOR USDT CHAINS
    if currency in ["usdt_bep20", "usdt_polygon"]:
        needed_gas, gas_symbol = gas_needed_for_currency(currency)
        gas_balance = await get_gas_balance(address, currency)

        if gas_balance < needed_gas:
            gas_embed = discord.Embed(
                title=f"{gas_symbol} Required For Network Fee",
                color=0x0000ff,
                description=(
                    f"USDT received but **insufficient gas**.\n\n"
                    f"**TXID:** `{tx_hash if tx_hash else 'Indexing...'}`\n"
                    f"**USDT Received:** `{received}`\n"
                    f"**Required Gas:** `{needed_gas:.4f} {gas_symbol}`\n"
                    f"**Current Gas:** `{gas_balance:.6f} {gas_symbol}`\n\n"
                    f"**Send {gas_symbol} to:** `{address}`"
                )
            )
            gas_embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/1384928504189026466/1385290221607715038/IMG_1328.png"
            )

            try: await msg.delete()
            except: pass

            await channel.send(embed=gas_embed)
            return

    # ============================================================
    # BUILD OLD UI (Restored)
    # ============================================================
    embed = discord.Embed(
        title="Transaction Detected (Partial)",
        color=0x0000ff,
        description="Received **less** than required. Confirm to proceed."
    )

    # Explorer link restored for all coins
    if tx_hash:
        explorer = {
            "usdt_bep20": f"https://bscscan.com/tx/{tx_hash}",
            "usdt_polygon": f"https://polygonscan.com/tx/{tx_hash}",
            "solana": f"https://solscan.io/tx/{tx_hash}",
            "ethereum": f"https://etherscan.io/tx/{tx_hash}",
        }.get(currency)

        embed.add_field(
            name="Transaction Hash",
            value=f"[{tx_hash}]({explorer})" if explorer else tx_hash,
            inline=False
        )
    else:
        embed.add_field(name="Transaction Hash", value="*Blockchain indexing...*", inline=False)

    embed.add_field(name=f"Received ({cur_name})", value=f"`{received} | ${usd_received}`")
    embed.add_field(name=f"Required ({cur_name})", value=f"`{expected} | ${usd_expected}`")

    # OLD UI Thumbnail restored
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/1384928504189026466/1385290221607715038/IMG_1328.png"
    )

    # Clean old msg
    try: await msg.delete()
    except: pass

    # Restore ToS UI
    try:
        history = [m async for m in channel.history(limit=1, oldest_first=True)]
        await history[0].edit(view=ToSButtonsAllInOnee())
    except:
        pass

    # Send embed (old style)
    await channel.send(f"<@{buyer}>", embed=embed, view=ProceedButton())

    # Waiting UI restored
    await channel.send(embed=discord.Embed(
        title="Waiting for confirmation",
        description="-# Don't pay extra before confirming.",
        color=0xfffff0
    ))
# ========================================
# FULL PAYMENT HANDLER
# ========================================
async def handle_full_payment(
    channel, deal_info, received_amount, expected_amount,
    currency, address, msg, tx_hash
):
    """Full payment handler with OLD UI + ultra-fast LTC confirmation."""

    deal_id = deal_info['deal_id']
    buyer_id = deal_info['buyer']      # receiver
    seller_id = deal_info['seller']    # sender

    # Convert decimals → float for LTC only
    if currency == "ltc":
        try:
            received_amount = float(received_amount)
            expected_amount = float(expected_amount)
        except:
            received_amount = float(str(received_amount))
            expected_amount = float(str(expected_amount))

    # Save amount in USD + crypto
    data = load_all_data()
    usd_value = await currency_to_usd(float(received_amount), currency)
    data[deal_id]["amount"] = float(usd_value)
    data[deal_id]["ltc_amount"] = float(received_amount)
    save_all_data(data)

    # Remove monitoring message
    try:
        await msg.delete()
    except:
        pass

    # UI display names
    currency_display = {
        "ltc": "LTC",
        "usdt_bep20": "USDT (BEP20)",
        "usdt_polygon": "USDT (Polygon)",
        "solana": "SOL",
        "ethereum": "ETH"
    }.get(currency, "Crypto")

    # Ensure TXID exists
    if not tx_hash:
        tx_hash = await fetch_txid_ultimate(address, currency)

    # =========================================
    # MAIN "Transaction Detected" EMBED
    # =========================================
    embed = discord.Embed(title="Transaction Detected", color=0x0000ff)

    # Explorer links
    if tx_hash:
        explorer = {
            "ltc": f"https://live.blockcypher.com/ltc/tx/{tx_hash}/",
            "usdt_bep20": f"https://bscscan.com/tx/{tx_hash}",
            "usdt_polygon": f"https://polygonscan.com/tx/{tx_hash}",
            "solana": f"https://solscan.io/tx/{tx_hash}",
            "ethereum": f"https://etherscan.io/tx/{tx_hash}",
        }.get(currency)

        embed.add_field(
            name="Transaction Hash",
            value=f"[{tx_hash}]({explorer})",
            inline=False
        )
    else:
        embed.add_field(
            name="Transaction Hash",
            value="*Blockchain explorer is indexing...*",
            inline=False
        )

    embed.add_field(
        name="Total Received",
        value=f"`{received_amount} {currency_display} | ${usd_value:.2f}`"
    )

    # =========================================
    # USDT = INSTANT RELEASE (NO CONFIRMATION)
    # =========================================
    if currency in ["usdt_bep20", "usdt_polygon"]:

        embed.add_field(name="Status", value="`Confirmed ✅`")
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517314433454342/discotools-xyz-icon.png"
        )

        await channel.send(f"<@{seller_id}>", embed=embed)

        final_embed = discord.Embed(
            title="Deal Confirmed",
            description=">>> Payment successfully received.",
            color=0x0000ff
        )
        final_embed.add_field(name=f"{currency_display} Amount", value=str(received_amount))
        final_embed.add_field(name="USD Value", value=f"${usd_value:.2f}")
        final_embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517314433454342/discotools-xyz-icon.png"
        )

        await channel.send(
            content=f"<@{buyer_id}> <@{seller_id}>",
            embed=final_embed,
            view=ReleaseButton()
        )
        return

    # =========================================
    # NON-USDT — CONFIRMATION REQUIRED
    # =========================================
    embed.add_field(name="Required Confirmations", value="`1`")
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517362390990889/discotools-xyz-icon__6_-removebg-preview.png"
    )

    await channel.send(f"<@{seller_id}>", embed=embed)

    wait_msg = await channel.send(
        embed=discord.Embed(
            title="Waiting for confirmation",
            description="-# Waiting for 1 confirmation...",
            color=0xfffff0
        )
    )

    # =========================================
    # ⭐ ULTRA FAST LTC CONFIRMATION (BALANCE)
    # =========================================
    if currency == "ltc":

        confirmed = 0.0

        for _ in range(200):
            await asyncio.sleep(3)

            try:
                val = await get_ltc_confirmed_balance(address)

                # Convert Decimal → float safely
                try:
                    confirmed = float(val)
                except:
                    confirmed = float(str(val))

            except:
                continue

            if confirmed >= expected_amount:
                break

        # FIX: if API returned 0, fallback to received
        if confirmed == 0:
            confirmed = float(received_amount)

        final_usd = await currency_to_usd(float(confirmed), "ltc")

        final = discord.Embed(
            title="Deal Confirmed",
            description=">>> Payment successfully received.",
            color=0x0000ff
        )
        final.add_field(name="LTC Amount", value=str(confirmed))
        final.add_field(name="USD Value", value=f"${final_usd:.2f}")
        final.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517314433454342/discotools-xyz-icon.png"
        )

        try:
            await wait_msg.delete()
        except:
            pass

        await channel.send(
            content=f"<@{buyer_id}> <@{seller_id}>",
            embed=final,
            view=ReleaseButton()
        )
        return

    # =========================================
    # SOL / ETH CONFIRMATION (NO CHANGE)
    # =========================================
    confirmed = 0

    for _ in range(200):
        await asyncio.sleep(3)

        try:
            if currency == "solana":
                confirmed = await get_solana_balance_parallel(address)
            elif currency == "ethereum":
                confirmed = await get_eth_balance_parallel(address)
            else:
                confirmed = received_amount
        except:
            continue

        if confirmed >= expected_amount:
            break

    final = discord.Embed(
        title="Deal Confirmed",
        description=">>> Payment successfully received.",
        color=0x0000ff
    )
    final.add_field(name=f"{currency_display} Amount", value=f"{received_amount}")
    final.add_field(name="USD Value", value=f"${usd_value:.2f}")
    final.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517314433454342/discotools-xyz-icon.png"
    )

    try:
        await wait_msg.delete()
    except:
        pass

    await channel.send(
        content=f"<@{buyer_id}> <@{seller_id}>",
        embed=final,
        view=ReleaseButton()
    )
# =====================================================
# UI COMPONENTS - CURRENCY SELECTION
# =====================================================

class CurrencySelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CurrencySelectMenu())

class CurrencySelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Litecoin (LTC)",
                value="ltc",
                emoji="<:SA_LTC_LiteCoin:1252612731962396762>"
            ),
            discord.SelectOption(
                label="Ethereum (ETH)",
                value="ethereum",
                emoji="<:emoji_300:1443965910556741662>"
            ),
            discord.SelectOption(
                label="Solana (SOL)",
                value="solana"
                #emoji="<:emoji_299:1443965875685294131>"
            ),
            discord.SelectOption(
                label="USDT Binance Smart Chain (BEP20)",
                value="usdt_bep20"
                #emoji="<:USDTBSC:1443976861867573248>"
            ),
            discord.SelectOption(
                label="USDT Polygon (Matic)",
                value="usdt_polygon"
                #emoji="<:USDTpolygon:1443975267222818816>"
            )
        ]

        super().__init__(
            placeholder="Select The Cryptocurrency",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="currency_select_menu"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_currency = self.values[0]
        await interaction.response.send_modal(BuyerSellerModal(selected_currency))

class BuyerSellerModal(Modal, title="Fill properly below!"):
    def __init__(self, currency):
        super().__init__()
        self.currency = currency

    user_id = TextInput(
        label="Enter Seller/Buyer User ID",
        placeholder="Enter the Discord User ID...",
        required=True,
        style=discord.TextStyle.short,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = guild.get_member(int(self.user_id.value))
        if not user:
            return await interaction.followup.send("User not found in this server.", ephemeral=True)

        category = discord.utils.get(guild.categories, id=CATEGORY_ID_1)
        acategory = discord.utils.get(guild.categories, id=CATEGORY_ID_2)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        main_cat = None
        if category and len(category.channels) < 50:
            main_cat = category
        elif acategory and len(acategory.channels) < 50:
            main_cat = acategory
        else:
            return await interaction.followup.send("All deals are full, please try again later!", ephemeral=True)

        try:
            counter = load_counter()
            new_channel_number = counter + 1
            channel_name = f"auto-{new_channel_number}"
            channel = await guild.create_text_channel(name=channel_name, category=main_cat, overwrites=overwrites)
            save_counter(new_channel_number)

            # Generate unique deal ID
            deal_id = create_deal_id()
            
            data = load_all_data()
            data[deal_id] = {
                "channel_id": str(channel.id),
                "seller": "None",  # Now represents SENDER
                "buyer": "None",  # Now represents RECEIVER
                "amount": 0.00,
                "start_time": time.time(),
                "rescan_count": 0,
                "payment_timeout": 20 * 60,
                "creator_id": str(interaction.user.id),
                "other_user_id": str(user.id),
                "deal_id": deal_id,
                "currency": self.currency
            }
            save_all_data(data)

            # Create DM embed with both user information and deal ID
            dm_embed_1 = discord.Embed(
                title="New Deal Created",
                description=(
                    "A new deal has been created for you.\n\n"
                    f"**Deal ID:** `{deal_id}`\n"
                    f"**Channel:** {channel.mention}\n"
                    f"**Currency:** {self.currency.upper()}\n\n"
                    "**Deal Participants:**\n"
                    f"• **Ticket Creator:** {interaction.user.mention} (ID: {interaction.user.id})\n"
                    f"• **Other Participant:** {user.mention} (ID: {user.id})"
                ),
                color=0x0000ff
            )

            dm_embed_2 = discord.Embed(
                description=f"{deal_id}",
                color=0x0000ff
            )

            try:
                await user.send(embeds=[dm_embed_1, dm_embed_2])
            except discord.Forbidden:
                pass
            try:
                await interaction.user.send(embeds=[dm_embed_1, dm_embed_2])
            except discord.Forbidden:
                pass

            embed = discord.Embed(
                title="🛡️ RainyDay Auto MiddleMan System",
                description=(
                    "**RainyDay MM** is a premier platform specializing in secure intermediary transactions. What sets us apart?\n"
                    "• We prioritize your safety, ensuring you always feel secure during every transaction.\n"
                    "• We uphold fairness and transparency, guaranteeing an equitable experience for both Senders and Receivers.\n"
                    "• Our services are characterized by efficiency and reliability, swiftly addressing and resolving any issues that may arise.\n\n"
                    "⚠️ **Important Note:**\n"
                    "• Make sure funds will not be released until the goods are fully delivered as per your requirements.\n"
                    "• Always retain the Deal ID to safeguard against potential risks.\n"
                    "• If you encounter any issues, promptly notify us for immediate assistance.\n\n"
                    "➡️ At RainyDay MM, we strive to create a secure and seamless trading experience for all our users."
                ),
                color=discord.Color(0x0000ff)
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1383487913186169032/1384932699717898300/Untitled-2.png?ex=68543a96&is=6852e916&hm=3f5566d93ca1ba539950f47e4ea4fbcf1c4b2e6873af9d97424656d867830d7a&")
            embed.set_footer(text="RainyDay MM", icon_url="https://cdn.discordapp.com/attachments/1383487913186169032/1384932699717898300/Untitled-2.png?ex=68543a96&is=6852e916&hm=3f5566d93ca1ba539950f47e4ea4fbcf1c4b2e6873af9d97424656d867830d7a&")

            embed2 = discord.Embed(
                title="⚠️ Be Caution!",
                description=(
                    "If a seller asks you to send money to their address/UPI QR code first or claims that the bot will charge a fee "
                    "(our mm service is completely free), be cautious it's most likely a scam. "
                    "**NEVER PAY DIRECTLY TO THE SELLER.** Report it to the admin immediately, and we'll take action."
                ),
                color=discord.Color.red()
            )

            embedd = discord.Embed(title="User Selection", color=0x0000ff)
            embedd.add_field(name="Sender", value="`None`", inline=False)
            embedd.add_field(name="Receiver", value="`None`", inline=False)
            embedd.set_thumbnail(url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517323069521992/discotools-xyz-icon_1.png?ex=693445bc&is=6932f43c&hm=5dc48048ac28e07a15b124c51e0b07ff9c8b8ef927dccdcf9b002226febd9b77&")
            embedd.set_footer(text="RainyDay MM", icon_url="https://cdn.discordapp.com/attachments/1383487913186169032/1384932699717898300/Untitled-2.png?ex=68543a96&is=6852e916&hm=3f5566d93ca1ba539950f47e4ea4fbcf1c4b2e6873af9d97424656d867830d7a&")

            deal_id_embed = discord.Embed(
                description=f"{deal_id}",
                color=0x0000ff
            )

            await channel.send(embed=embed, content=f"{user.mention} {interaction.user.mention}", view=ToSButtonsAllInOne())
            await channel.send(embed=deal_id_embed)
            await channel.send(embed=embedd, view=SendButton())
            await channel.send(embed=embed2, view=LangButton(), content=f"{user.mention} {interaction.user.mention}")
            await interaction.followup.send(f"Deal created: {channel.mention}", ephemeral=True)

        except Exception as e:
            print(f"Error creating channel: {e}")
            await interaction.followup.send("An error occurred while creating the deal channel.", ephemeral=True)

# =====================================================
# EXISTING UI COMPONENTS (ALL PRESERVED)
# =====================================================

class ToSButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Product ToS and Warranty", style=discord.ButtonStyle.primary, custom_id="producttos")

    async def callback(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        self.seller_id = deal['seller']  # Now represents RECEIVER
        if interaction.user.id == int(self.seller_id):
           modal = ToSModal()
           await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("You are not authorized to use this.", ephemeral=True)

class ToSModal(Modal, title="Please tell properly!"):
    product = TextInput(
        label="Product",
        placeholder="Nitro, OwO, C2I, etc.",
        required=True,
        style=discord.TextStyle.short,
        max_length=40
    )
    tos = TextInput(
        label="TOS AND WARRANTY INFORMATION",
        placeholder="ToS: Record Video, etc | Warranty: Lifetime Warranty, etc.",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=4000
    )

    async def on_submit(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        self.buyer_id = deal['buyer']  # Now represents RECEIVER
        self.seller_id = deal['seller']  # Now represents SENDER
        await interaction.response.defer()
        try:
            embed = discord.Embed(title="Product Details", color=0x0000ff)
            embed.add_field(name="Product", value=f"```\n{self.product.value}\n```", inline=False)
            embed.add_field(name="ToS and Warranty", value=f"```\n{self.tos.value if self.tos.value else 'No ToS and Warranty'}\n```", inline=False)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517343084740688/discotools-xyz-icon__2_-removebg-preview.png?ex=693445c1&is=6932f441&hm=5c3da62aeac41487f233c248bd8f20c108e1a43795335ad57f0db85349b7c99b&")
            deal_id, deal = get_deal_by_channel(interaction.channel.id)
            if not deal:
                await interaction.followup.send("Deal not found.", ephemeral=True)
                return
                
            self.seller_id = deal['seller']  # Now represents SENDER
            self.buyer_id = deal['buyer']  # Now represents RECEIVER
            await interaction.message.edit(embed=embed, view=ToSCoButtons(), content=f"<@{self.seller_id}> <@{self.buyer_id}>")
        except Exception as e:
            print(f"Error in ToSModal: {e}")
            await interaction.followup.send("An error occurred while processing your ToS.", ephemeral=True)

class ToSCoButtons(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.seller_con = False  # Now represents SENDER confirmation
        self.buyer_con = False  # Now represents RECEIVER confirmation
        self.lock = asyncio.Lock()

        agree_button = Button(label="Agree", style=discord.ButtonStyle.green, custom_id="agree")
        agree_button.callback = self.agree
        self.add_item(agree_button)

        cancel_button = Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cants")
        cancel_button.callback = self.cancel
        self.add_item(cancel_button)

    async def agree(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return

        self.seller = deal['seller']  # Now represents SENDER
        self.buyer = deal['buyer']  # Now represents RECEIVER
        currency = deal.get("currency", "ltc")

        async with self.lock:
            # SENDER Agree (was seller)
            if interaction.user.id == int(self.seller):
                if not self.seller_con:
                    self.seller_con = True
                    await interaction.channel.send(
                        embed=discord.Embed(description=f"{interaction.user.mention} (Seller) has agreed.")
                    )
                else:
                    await interaction.response.send_message("You have already agreed.", ephemeral=True)
                    return

            # RECEIVER Agree (was buyer)
            elif interaction.user.id == int(self.buyer):
                if not self.buyer_con:
                    self.buyer_con = True
                    await interaction.channel.send(
                        embed=discord.Embed(description=f"{interaction.user.mention} (Buyer) has agreed.")
                    )
                else:
                    await interaction.response.send_message("You have already agreed.", ephemeral=True)
                    return

            else:
                await interaction.response.send_message("You are not authorized to agree to this.", ephemeral=True)
                return

            await interaction.response.defer()

            # Both agreed → ask for amount
            if self.seller_con and self.buyer_con:
                await interaction.message.edit(view=None, content=None)

                # ===========================================
                # SOLANA CUSTOM MINIMUM AMOUNT EMBED
                # ===========================================
                if currency == "solana":
                    sol_min_fee = 0.00206
                    sol_fee_usd = await currency_to_usd(sol_min_fee, "solana")
                    sol_required_usd = round(sol_fee_usd + 0.10, 4)

                    embed = discord.Embed(
                        title="Deal Amount (Solana)",
                        description=(
                            "Kindly specify the exact amount we are expected to receive in USD.\n"
                            "(example: 10.5)\n\n"
                            f"> **Solana Minimum Deal Requirement**\n"
                            f"> Wallet rent + gas = **0.00206 SOL** (~`${sol_fee_usd:.4f}` USD)\n"
                            f"> Base bot minimum = **$0.10 USD**\n"
                            f"> **Total Minimum = `${sol_required_usd}` USD**\n"
                            f"> You cannot enter an amount lower than this.\n"
                        ),
                        color=0x0000ff
                    )

                # ===========================================
                # NON-SOLANA NORMAL AMOUNT EMBED
                # ===========================================
                else:
                    embed = discord.Embed(
                        title="Deal Amount",
                        description=(
                            "Kindly specify the exact amount we are expected to receive in USD\n"
                            "(example: 10.5).\n\n"
                            "-# Note: The minimum amount is 0.1 USD"
                        ),
                        color=0x0000ff
                    )

                embed.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517334331097118/discotools-xyz-icon__4_-removebg-preview.png?ex=693445bf&is=6932f43f&hm=1b9730b7b0c4b222db4800e55c379936ce86b938bbe65709034a3cc30bd0dfdf&"
                )

                msgq = await interaction.channel.send(embed=embed, content=f"<@{self.buyer}>")

                # WAIT FOR SENDER INPUT (was seller)
                def check(m):
                    return (
                        m.channel == interaction.channel and
                        m.author.id == int(self.buyer) and
                        not m.author.bot
                    )

                while True:
                    try:
                        amount_message = await bot.wait_for('message', check=check)
                        try:
                            amount = float(amount_message.content)

                            # ==============================
                            # SOLANA MINIMUM CHECK
                            # ==============================
                            if currency == "solana":
                                sol_min_fee = 0.00206
                                sol_fee_usd = await currency_to_usd(sol_min_fee, "solana")
                                sol_required_usd = round(sol_fee_usd + 0.10, 4)

                                if amount < sol_required_usd:
                                    warn = await interaction.channel.send(
                                        f"**Minimum deal amount for Solana is `${sol_required_usd}` USD**"
                                    )
                                    await asyncio.sleep(6)
                                    await warn.delete()
                                    continue

                            # ==============================
                            # OTHER CURRENCIES MINIMUM
                            # ==============================
                            else:
                                if amount < 0.1:
                                    warn = await interaction.channel.send(
                                        "Amount must be at least **0.1 USD**."
                                    )
                                    await asyncio.sleep(6)
                                    await warn.delete()
                                    continue

                            # SAVE AMOUNT
                            data = load_all_data()
                            if deal_id in data:
                                data[deal_id]["amount"] = amount
                                save_all_data(data)

                            # Confirm Embed
                            confirm_embed = discord.Embed(
                                title="Confirm Amount",
                                description=f">>> Are you certain that we are expected to receive `{amount}`$ "
                                            f"in {currency.upper()}?",
                                color=0x0000ff
                            )

                            confirm_embed.set_thumbnail(
                                url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517354543714406/discotools-xyz-icon_5.png?ex=693445c4&is=6932f444&hm=9404a1004e35b98864b40386da81875c7b275d3d0c1d080d49fb8926c79421f7&"
                            )

                            await msgq.edit(
                                embed=confirm_embed,
                                view=AmountConButton(),
                                content=f"<@{self.seller}> <@{self.buyer}>"
                            )
                            break

                        except ValueError:
                            continue

                    except Exception as e:
                        print(f"Error waiting for amount: {e}")
                        await interaction.channel.send("An error occurred. Please try again.")
                        continue

    async def cancel(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return

        self.seller = deal['seller']  # Now represents SENDER
        self.buyer = deal['buyer']  # Now represents RECEIVER

        if interaction.user.id in (int(self.seller), int(self.buyer)):
            self.seller_con = False
            self.buyer_con = False

            tos_embed = discord.Embed(
                title="Product Details",
                description="- Please discuss ToS & Warranty.\n- Then click below to conclude your deal.",
                color=0x0000ff
            )
            tos_embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517343084740688/discotools-xyz-icon__2_-removebg-preview.png?ex=6938e301&is=69379181&hm=894ab566fd708a090f2ff2f58ef335ad8c3ce14f108c10f372d74f60d773be84&"
            )

            await interaction.message.edit(
                embed=tos_embed,
                view=TosView(),
                content=f"<@{self.seller}> Please set your ToS and Warranty below."
            )
            await interaction.response.defer()

        else:
            await interaction.response.send_message("You are not authorized to cancel this.", ephemeral=True)

class LangButton(View):
    def __init__(self, selected_lang="English"):
        super().__init__(timeout=None)
        self.selected_lang = selected_lang
        self.add_language_buttons()

    def add_language_buttons(self):
        languages = ["English", "Hindi", "Hinglish"]
        for lang in languages:
            is_selected = lang == self.selected_lang
            button = Button(
                label=lang,
                style=discord.ButtonStyle.danger if is_selected else discord.ButtonStyle.gray,
                disabled=is_selected,
                custom_id=f"lang_{lang.lower()}"
            )
            button.callback = self.create_callback(lang)
            self.add_item(button)

    def get_embed_for_language(self, lang: str) -> discord.Embed:
        if lang == "English":
            return discord.Embed(
                title="⚠️ Be Caution!",
                description="If a seller asks you to send money to their address/UPI QR code first or claims that the bot will charge a fee (our mm service is completely free), be cautious it's most likely a scam. **NEVER PAY DIRECTLY TO THE SELLER.** Report it to the admin immediately, and we'll take action.",
                color=discord.Color.red()
            )
        elif lang == "Hindi":
            return discord.Embed(
                title="⚠️ Be Caution!",
                description="अगर कोई विक्रेता आपसे पहले उनके Address/UPI QR कोड पर पैसे भेजने के लिए कहता है या दावा करता है कि बॉट फीस लेगा (हमारी मिडलमैन सेवा पूरी तरह से मुफ़्त है), तो सावधान रहें, यह सबसे अधिक संभावना है कि यह एक घोटाला है। **कभी भी सीधे भुगतान न करें।** इसकी सूचना तुरंत एडमिन को दें, हम कार्रवाई करेंगे।",
                color=discord.Color.red()
            )
        elif lang == "Hinglish":
            return discord.Embed(
                title="⚠️ Be Caution!",
                description="Agar koi seller aapse pehle unke Address/UPI QR code par paise bhejne ke liye kahe ya bole ki bot fees lega (hamari middleman service bilkul free hai), toh sambhal ke, yeh scam ho sakta hai. **Kabhi bhi directly payment mat karo Seller ko.** Aise case ki turant admin ko report karo, hum action lenge.",
                color=discord.Color.red()
            )
        else:
            return discord.Embed(title="Unknown Language", description="Please try again.")

    def create_callback(self, lang: str):
        async def callback(interaction: discord.Interaction):
            new_embed = self.get_embed_for_language(lang)
            new_view = LangButton(selected_lang=lang)
            await interaction.response.edit_message(embed=new_embed, view=new_view)
        return callback

class ToSButtonsAllInOne(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Ownership ToS", emoji="🏠", style=discord.ButtonStyle.blurple, custom_id="tos_ownership")
    async def ownership_tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👑 Ownership ToS",
            description="(Any Deal Related To Ownership Transfer)\n\n"
                        "🧑‍💼 **Sender**: Must record from the time you have paid until you receive ownership.\n"
                        "🧑‍💼 **Receiver**: Even the Receiver must record the process of bringing ownership to another.",
            color=0x0000ff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Nitro ToS", emoji="🚀", style=discord.ButtonStyle.blurple, custom_id="tos_nitro")
    async def nitro_tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🚀 Nitro ToS",
            description="(Any Deal Related To Discord Nitro, Ex: Nitro Boost, Basic , Promo, Vcc)\n\n"
                        "🧑‍💼 **Sender**: Turn on the screen recorder before the Receiver sends you the Nitro gift link in your DMs. Keep recording until you claim the product.\n"
                        "🧑‍💼 **Receiver**: The Receiver should confirm with the Sender whether they're ready to record their screen. Do not share the code without their confirmation.",
            color=0x0000ff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Account ToS", emoji="🎮", style=discord.ButtonStyle.blurple, custom_id="tos_account")
    async def account_tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎮 Account ToS",
            description="(Any Deal Related To Accounts, Ex: FF Account, BGMI account, Minecraft Account, etc...)\n\n"
                        "🧑‍💼 **Sender**: Must record from beginning when the Receiver drops the account credentials and record until the account is secured.\n"
                        "🧑‍💼 **Receiver**: Must confirm before dropping the account and guide the Sender fully.",
            color=0x0000ff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Exchange ToS", emoji="🔁", style=discord.ButtonStyle.blurple, custom_id="tos_exchange")
    async def exchange_tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔁 Exchange ToS",
            description="(Any Deal Related To I2C, C2I, C2C, PP2C, C2PP, etc...)\n\n"
                        "🧑‍💼 **Sender**: Must open their app and check if they received payment.\n"
                        "🧑‍💼 **Receiver**: Must provide payment proof after delivery.",
            color=0x0000ff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Member ToS", emoji="👤", style=discord.ButtonStyle.blurple, custom_id="tos_member")
    async def member_tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👤 Member ToS",
            description="(Any Deal Related To Auth Bot, Invites Link, etc...)\n\n"
                        "🧑‍💼 **Sender**: Should keep a screenshot with the Receiver before adding members and check thoroughly before releasing.\n"
                        "🧑‍💼 **Receiver**: Must provide product proof after delivery.",
            color=0x0000ff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ToSButtonsAllInOnee(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Ownership ToS", emoji="🏠", style=discord.ButtonStyle.blurple, custom_id="tos_ownership")
    async def ownership_tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👑 Ownership ToS",
            description="(Any Deal Related To Ownership Transfer)\n\n"
                        "🧑‍💼 **Sender**: Must record from the time you have paid until you receive ownership.\n"
                        "🧑‍💼 **Receiver**: Even the Receiver must record the process of bringing ownership to another.",
            color=0x0000ff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Nitro ToS", emoji="🚀", style=discord.ButtonStyle.blurple, custom_id="tos_nitro")
    async def nitro_tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🚀 Nitro ToS",
            description="(Any Deal Related To Discord Nitro, Ex: Nitro Boost, Basic , Promo, Vcc)\n\n"
                        "🧑‍💼 **Sender**: Turn on the screen recorder before the Receiver sends you the Nitro gift link in your DMs. Keep recording until you claim the product.\n"
                        "🧑‍💼 **Receiver**: The Receiver should confirm with the Sender whether they're ready to record their screen. Do not share the code without their confirmation.",
            color=0x0000ff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Account ToS", emoji="🎮", style=discord.ButtonStyle.blurple, custom_id="tos_account")
    async def account_tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎮 Account ToS",
            description="(Any Deal Related To Accounts, Ex: FF Account, BGMI account, Minecraft Account, etc...)\n\n"
                        "🧑‍💼 **Sender**: Must record from beginning when the Receiver drops the account credentials and record until the account is secured.\n"
                        "🧑‍💼 **Receiver**: Must confirm before dropping the account and guide the Sender fully.",
            color=0x0000ff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Exchange ToS", emoji="🔁", style=discord.ButtonStyle.blurple, custom_id="tos_exchange")
    async def exchange_tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔁 Exchange ToS",
            description="(Any Deal Related To I2C, C2I, C2C, PP2C, C2PP, etc...)\n\n"
                        "🧑‍💼 **Sender**: Must open their app and check if they received payment.\n"
                        "🧑‍💼 **Receiver**: Must provide payment proof after delivery.",
            color=0x0000ff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Member ToS", emoji="👤", style=discord.ButtonStyle.blurple, custom_id="tos_member")
    async def member_tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👤 Member ToS",
            description="(Any Deal Related To Auth Bot, Invites Link, etc...)\n\n"
                        "🧑‍💼 **Sender**: Should keep a screenshot with the Receiver before adding members and check thoroughly before releasing.\n"
                        "🧑‍💼 **Receiver**: Must provide product proof after delivery.",
            color=0x0000ff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ConfButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.buyer_confirmed = False  # Now represents RECEIVER confirmation
        self.seller_confirmed = False  # Now represents SENDER confirmation
        self.tos_sent = False

        button = Button(label="Confirm", style=discord.ButtonStyle.green, custom_id="confcon")
        button.callback = self.confirm_callback
        self.add_item(button)
        buttone = Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="confcan")
        buttone.callback = self.cancel_callback
        self.add_item(buttone)
    
    async def cancel_callback(self, interaction: discord.Interaction):
        uid = interaction.user.id
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        self.seller = deal['seller']  # Now represents SENDER
        self.buyer = deal['buyer']  # Now represents RECEIVER
        if uid == int(self.seller) or uid == int(self.buyer):
            await interaction.response.defer()
            deal['seller'] = "None"
            deal['buyer'] = "None"
            update_deal(interaction.channel.id, deal)
            self.buyer_confirmed = False
            self.seller_confirmed = False
            embedd = discord.Embed(title="User Selection", color=0x0000ff)
            embedd.add_field(name="Sender", value="`None`", inline=False)
            embedd.add_field(name="Receiver", value="`None`", inline=False)
            embedd.set_thumbnail(url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517323069521992/discotools-xyz-icon_1.png?ex=693445bc&is=6932f43c&hm=5dc48048ac28e07a15b124c51e0b07ff9c8b8ef927dccdcf9b002226febd9b77&")
            embedd.set_footer(text="RainyDay MM", icon_url="https://cdn.discordapp.com/attachments/1383487913186169032/1384932699717898300/Untitled-2.png?ex=68543a96&is=6852e916&hm=3f5566d93ca1ba539950f47e4ea4fbcf1c4b2e6873af9d97424656d867830d7a&")
            em = discord.Embed(description=f"Cancelled by {interaction.user.mention}")
            await interaction.message.delete()
            await interaction.channel.send(embed=em)
            await interaction.channel.send(embed=embedd, view=SendButton())

    async def confirm_callback(self, interaction: discord.Interaction):
        uid = interaction.user.id
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        self.seller = deal['seller']  # Now represents SENDER
        self.buyer = deal['buyer']  # Now represents RECEIVER
        if uid != int(self.buyer) and uid != int(self.seller):
            return await interaction.response.send_message("You are not authorized to confirm this deal.", ephemeral=True)

        if (uid == int(self.buyer) and self.buyer_confirmed) or (uid == int(self.seller) and self.seller_confirmed):
            return await interaction.response.send_message("You have already confirmed.", ephemeral=True)

        if uid == int(self.buyer):
            self.buyer_confirmed = True
        elif uid == int(self.seller):
            self.seller_confirmed = True

        await interaction.response.defer()
        confirm_embed = discord.Embed(
            description=f"{interaction.user.mention} has confirmed.",
            color=0x0000ff
        )
        await interaction.channel.send(embed=confirm_embed)

        if self.buyer_confirmed and self.seller_confirmed and not self.tos_sent:
            self.tos_sent = True

            embed = discord.Embed(title="User Confirmation", color=0x0000ff)
            embed.add_field(name="Sender", value=f"<@{self.buyer}>", inline=False)
            embed.add_field(name="Receiver", value=f"<@{self.seller}>", inline=False)
            embed.set_footer(text="RainyDay MM", icon_url="https://cdn.discordapp.com/attachments/1383487913186169032/1384932699717898300/Untitled-2.png")
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517323069521992/discotools-xyz-icon_1.png?ex=693445bc&is=6932f43c&hm=5dc48048ac28e07a15b124c51e0b07ff9c8b8ef927dccdcf9b002226febd9b77&")

            tos_embed = discord.Embed(
                title="Product Details",
                description="- Please discuss about ToS and Warranty of products you are dealing. And then click the button below to officially conclude your deal.\n- If you skip this process and put nothing in the ToS and Warranty button below, we will not take any responsibility if you have any problem.",
                color=0x0000ff
            )
            tos_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517343084740688/discotools-xyz-icon__2_-removebg-preview.png?ex=693445c1&is=6932f441&hm=5c3da62aeac41487f233c248bd8f20c108e1a43795335ad57f0db85349b7c99b&")

            await interaction.message.edit(embed=embed, view=None)
            await interaction.channel.send(embed=tos_embed, view=TosView(), content=f"<@{self.seller}> Please set your ToS and Warranty below.")

class TosView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ToSButton())

class SendButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # ============================
    #        SENDER BUTTON
    # ============================
    @discord.ui.button(label="Sending", style=discord.ButtonStyle.gray, custom_id="sensend")
    async def set_sender(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = interaction.channel.id
        user_id = str(interaction.user.id)

        deal_id, deal = get_deal_by_channel(channel_id)
        if not deal:
            return await interaction.response.send_message("Deal not found.", ephemeral=True)

        # Prevent selecting both roles
        if deal["seller"] == user_id:  # user is already receiver
            return await interaction.response.send_message("**You can't select both roles.**", ephemeral=True)

        # Prevent selecting sender if already chosen
        if deal["buyer"] != "None":
            return await interaction.response.send_message("**Sender is already selected.**", ephemeral=True)

        await interaction.response.defer()

        deal["buyer"] = user_id  # Sender
        update_deal(channel_id, deal)
        await self.update_embed(interaction, deal)

    # ============================
    #        RECEIVER BUTTON
    # ============================
    @discord.ui.button(label="Receiving", style=discord.ButtonStyle.gray, custom_id="senrecv")
    async def set_receiver(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = interaction.channel.id
        user_id = str(interaction.user.id)

        deal_id, deal = get_deal_by_channel(channel_id)
        if not deal:
            return await interaction.response.send_message("Deal not found.", ephemeral=True)

        # Prevent selecting both roles
        if deal["buyer"] == user_id:  # user is already sender
            return await interaction.response.send_message("**You can't select both roles.**", ephemeral=True)

        # Prevent selecting receiver if already chosen
        if deal["seller"] != "None":
            return await interaction.response.send_message("**Receiver is already selected.**", ephemeral=True)

        await interaction.response.defer()

        deal["seller"] = user_id  # Receiver
        update_deal(channel_id, deal)
        await self.update_embed(interaction, deal)

    # ============================
    #            RESET
    # ============================
    @discord.ui.button(label="Reset", style=discord.ButtonStyle.red, custom_id="senreset")
    async def reset_deal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        channel_id = interaction.channel.id

        deal_id, existing_deal = get_deal_by_channel(channel_id)

        deal = {
            "channel_id": str(channel_id),
            "seller": "None",      # receiver
            "buyer": "None",       # sender
            "amount": 0.00,
            "start_time": time.time(),
            "rescan_count": 0,
            "payment_timeout": 20 * 60,
            "deal_id": deal_id if existing_deal else "",
            "currency": existing_deal.get("currency", "ltc") if existing_deal else "ltc"
        }

        update_deal(channel_id, deal)
        await self.update_embed(interaction, deal)

    # ============================
    #        UPDATE EMBED
    # ============================
    async def update_embed(self, interaction: discord.Interaction, deal):
        sender = deal["buyer"]
        receiver = deal["seller"]

        embed = discord.Embed(title="User Selection", color=0x0000ff)

        embed.add_field(
            name="Sender",
            value=f"<@{sender}>" if sender != "None" else "`None`",
            inline=False
        )

        embed.add_field(
            name="Receiver",
            value=f"<@{receiver}>" if receiver != "None" else "`None`",
            inline=False
        )

        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517323069521992/discotools-xyz-icon_1.png?ex=693445bc&is=6932f43c&hm=5dc48048ac28e07a15b124c51e0b07ff9c8b8ef927dccdcf9b002226febd9b77&")
        embed.set_footer(
            text="RainyDay MM",
            icon_url="https://cdn.discordapp.com/attachments/1383487913186169032/1384932699717898300/Untitled-2.png"
        )

        await interaction.message.edit(embed=embed, view=self)

        # If both roles selected, send confirmation
        if sender != "None" and receiver != "None":
            confirm = discord.Embed(title="User Confirmation", color=0x0000ff)
            confirm.add_field(name="Sender", value=f"<@{sender}>", inline=False)
            confirm.add_field(name="Receiver", value=f"<@{receiver}>", inline=False)

            confirm.set_footer(
                text="RainyDay MM",
                icon_url="https://cdn.discordapp.com/attachments/1383487913186169032/1384932699717898300/Untitled-2.png"
            )
            confirm.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517323069521992/discotools-xyz-icon_1.png?ex=693445bc&is=6932f43c&hm=5dc48048ac28e07a15b124c51e0b07ff9c8b8ef927dccdcf9b002226febd9b77&"
            )

            await interaction.message.delete()
            await interaction.channel.send(embed=confirm, view=ConfButtons())

class AmountConButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.seller_con = False  # Now represents SENDER confirmation
        self.buyer_con = False  # Now represents RECEIVER confirmation
        self.final_embed_sent = False

        button = Button(label="Confirm", style=discord.ButtonStyle.green, custom_id="amtcon")
        button.callback = self.confirm
        self.add_item(button)

        cancel_button = Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="amtcan")
        cancel_button.callback = self.cancel
        self.add_item(cancel_button)

    async def cancel(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return

        self.seller_id = deal["seller"]  # Now represents SENDER
        self.buyer_id = deal["buyer"]  # Now represents RECEIVER
        self.currency = deal.get("currency", "ltc")

        if self.currency == "solana":
            sol_min_fee = 0.00206  # network rent + gas
            sol_fee_usd = await currency_to_usd(sol_min_fee, "solana")

            sol_required_usd = round(sol_fee_usd + 0.10, 4)

            minimum_text = (
                f"> **Solana Minimum Deal Requirement**\n"
                f"> Wallet rent + gas = **0.00206 SOL** (~`${sol_fee_usd:.4f}` USD)\n"
                f"> Base bot minimum = **$0.10 USD**\n"
                f"> **Total Minimum = `${sol_required_usd}` USD**\n"
                f"> You cannot enter an amount lower than this.\n"
            )
        else:
            minimum_text = "-# Note: Minimum deal amount is 0.1 USD"

        embed = discord.Embed(
            title="Deal Amount",
            description=(
                "Kindly specify the exact amount we are expected to receive in USD.\n"
                "(example: 10.5)\n\n"
                f"{minimum_text}"
            ),
            color=0x0000ff
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517354543714406/discotools-xyz-icon_5.png?ex=693445c4&is=6932f444&hm=9404a1004e35b98864b40386da81875c7b275d3d0c1d080d49fb8926c79421f7&"
        )

        await interaction.message.edit(
            embed=embed, view=None, content=f"<@{self.buyer_id}>"
        )
        await interaction.response.defer()

        def check(m):
            return (
                m.channel == interaction.channel and
                m.author.id == int(self.buyer_id) and
                not m.author.bot
            )

        while True:
            try:
                amount_msg = await bot.wait_for("message", check=check)
                try:
                    amount = float(amount_msg.content)

                    # ======================================================
                    # 🔥 ACTUAL VALIDATION CHECK (ENFORCE MINIMUM)
                    # ======================================================
                    if self.currency == "solana":
                        sol_min_fee = 0.00206
                        sol_fee_usd = await currency_to_usd(sol_min_fee, "solana")
                        sol_required_usd = round(sol_fee_usd + 0.10, 4)

                        if amount < sol_required_usd:
                            warn = await interaction.channel.send(
                                f"**Solana minimum is `${sol_required_usd}` USD**\n"
                                f"(Includes **0.00206 SOL fee** + **$0.10 base minimum**)"
                            )
                            await asyncio.sleep(6)
                            await warn.delete()
                            continue

                    else:
                        # Non-solana currencies
                        if amount < 0.1:
                            warn = await interaction.channel.send("Amount must be at least 0.1 USD.")
                            await asyncio.sleep(6)
                            await warn.delete()
                            continue

                    # Save amount
                    data = load_all_data()
                    if deal_id in data:
                        data[deal_id]["amount"] = amount
                        save_all_data(data)

                    confirm_embed = discord.Embed(
                        title="Confirm Amount",
                        description=f">>> Are you certain that we are expected to receive `{amount}`$ "
                                    f"in {self.currency.upper()}?",
                        color=0x0000ff
                    )
                    confirm_embed.set_thumbnail(
                        url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517354543714406/discotools-xyz-icon_5.png?ex=693445c4&is=6932f444&hm=9404a1004e35b98864b40386da81875c7b275d3d0c1d080d49fb8926c79421f7&"
                    )

                    await interaction.message.edit(
                        embed=confirm_embed,
                        view=AmountConButton(),
                        content=f"<@{self.buyer_id}> <@{self.seller_id}>"
                    )
                    break

                except ValueError:
                    continue

            except Exception as e:
                print("Amount error:", e)
                await interaction.channel.send("Error occurred. Try again.")
                continue

    async def confirm(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return

        self.seller_id = deal["seller"]  # Now represents SENDER
        self.buyer_id = deal["buyer"]  # Now represents RECEIVER
        self.amount = deal["amount"]
        self.currency = deal.get("currency", "ltc")

        if interaction.user.id == int(self.seller_id):
            if not self.seller_con:
                self.seller_con = True
                await interaction.channel.send(embed=discord.Embed(
                    description=f"{interaction.user.mention} (Seller) has confirmed."
                ))
            else:
                await interaction.response.send_message("You have already confirmed.", ephemeral=True)
                return

        elif interaction.user.id == int(self.buyer_id):
            if not self.buyer_con:
                self.buyer_con = True
                await interaction.channel.send(embed=discord.Embed(
                    description=f"{interaction.user.mention} (Buyer) has confirmed."
                ))
            else:
                await interaction.response.send_message("You have already confirmed.", ephemeral=True)
                return

        await interaction.response.defer()

        # ===================================
        # BOTH CONFIRMED → GENERATE ADDRESS
        # ===================================
        if self.seller_con and self.buyer_con and not self.final_embed_sent:
            self.final_embed_sent = True
            await interaction.message.edit(view=None, content=None)

            crypto_amount = await usd_to_currency_amount(self.amount, self.currency)

            wallet = await generate_wallet_for_currency(deal_id, self.currency)

            address = wallet['address']
            private_key = wallet['private_key']

            data = load_all_data()
            if deal_id in data:
                data[deal_id].update({
                    "address": address,
                    "private_key": private_key,
                    "ltc_amount": crypto_amount,
                    "payment_start_time": time.time()
                })
                save_all_data(data)

            currency_display = {
                'ltc': 'Litecoin',
                'usdt_bep20': 'USDT (BEP20)',
                'usdt_polygon': 'USDT (Polygon)',
                'solana': 'Solana',
                'ethereum': 'Ethereum'
            }.get(self.currency, 'Crypto')

            embed = discord.Embed(
                title="RainyDay MM",
                description=(
                    f"- <@{self.buyer_id}> Please proceed by transferring the agreed-upon funds\n"
                    f"- COPY & PASTE the EXACT AMOUNT to avoid errors.\n\n"
                ),
                color=0x0000ff
            )

            embed.add_field(name=f"{currency_display} Address", value=f"```\n{address}\n```", inline=False)
            embed.add_field(name=f"{currency_display} Amount", value=f"`{crypto_amount:.8f}`", inline=True)
            embed.add_field(name="USD Amount", value=f"`{self.amount}$`", inline=True)
            embed.set_footer(text="➤ RainyDay MM | Transaction Confirmed")

            em = discord.Embed()
            em.set_author(name="Waiting for transaction...")

            await interaction.channel.send(content=f"<@{self.buyer_id}>", embed=embed, view=AddyButtons())

            if self.currency in ["usdt_bep20", "usdt_polygon"]:
                await send_usdt_wallet_with_gas_embed(interaction, deal_id, self.currency, address)

            await interaction.channel.send(
                "# Note - If you don't send the amount within 20 minutes, the deal will be cancelled."
            )

            msg = await interaction.channel.send(embed=em)

            bot.loop.create_task(
                check_payment_multicurrency(address, interaction.channel, crypto_amount, data[deal_id], msg)
            )

class AddyButtons(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.copy_used = False
        button = Button(label="Copy", style=discord.ButtonStyle.primary, custom_id="addycopy")
        button.callback = self.copy
        self.add_item(button)
        buttone = Button(label="Scan QR", style=discord.ButtonStyle.primary, custom_id="addyqr")
        buttone.callback = self.qr
        self.add_item(buttone)

    async def copy(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        self.seller_id = deal['seller']  # Now represents SENDER
        self.buyer_id = deal['buyer']  # Now represents RECEIVER
        self.addy = deal['address']
        self.amount = deal['ltc_amount']
        
        if interaction.user.id == int(self.seller_id) or interaction.user.id == int(self.buyer_id):
            if self.copy_used:
                await interaction.response.send_message("You've already used the copy button.", ephemeral=True)
                return
                
            self.copy_used = True
            await interaction.response.send_message(f"{self.addy}")
            await interaction.followup.send(f"{self.amount:.8f}")

            for item in self.children:
                if item.custom_id == "addycopy":
                    item.disabled = True
            await interaction.message.edit(view=self)
        else:
            await interaction.response.send_message("You are not authorized to use this.", ephemeral=True)

    async def qr(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        self.seller_id = deal['seller']  # Now represents SENDER
        self.buyer_id = deal['buyer']  # Now represents RECEIVER
        self.addy = deal['address']
        self.amount = deal['ltc_amount']
        if interaction.user.id == int(self.seller_id) or interaction.user.id == int(self.buyer_id):
            await interaction.response.defer(ephemeral=True)
            
            qr_bytes = await generate_qr_bytes(self.addy)
            
            if qr_bytes:
                file = discord.File(io.BytesIO(qr_bytes), filename="qrcode.png")
                
                currency_display = {
                    'ltc': 'Litecoin',
                    'usdt_bep20': 'USDT (BEP20)',
                    'usdt_polygon': 'USDT (Polygon)',
                    'solana': 'Solana (SOL)',
                    'ethereum': 'Ethereum (ETH)'
                }.get(deal.get('currency', 'ltc'), 'Crypto')
                
                embed = discord.Embed(
                    title="Payment QR Code",
                    color=0x0000FF
                )
                embed.add_field(name="Address", value=f"`{self.addy}`", inline=False)
                embed.add_field(name="Amount", value=f"`{self.amount} {currency_display}`", inline=False)
                embed.set_image(url="attachment://qrcode.png")
                
                await interaction.followup.send(embed=embed, file=file, ephemeral=True)
            else:
                await interaction.followup.send("Failed to generate QR code. Please try again.", ephemeral=True)
        else:
            await interaction.response.defer()

class ProceedButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        button = Button(label="Continue", style=discord.ButtonStyle.green, custom_id="processcon")
        button.callback = self.process
        self.add_item(button)
        buttone = Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="processcan")
        buttone.callback = self.cancel
        self.add_item(buttone)

    async def process(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        buyer = deal['buyer']  # Now represents RECEIVER
        seller = deal['seller']  # Now represents SENDER
        currency = deal.get('currency', 'ltc')
        
        if interaction.user.id == int(seller):  # SENDER confirms
           await interaction.response.defer()
           await interaction.message.edit(view=None)
           embed = discord.Embed(description=f"{interaction.user.mention} has confirmed to proceed with the deal.")
           await interaction.channel.send(embed=embed)
           while True:
              await asyncio.sleep(30)
              address = deal['address']
              
              # Check balance based on currency
              if currency == 'ltc':
                  bal, _ = await get_balance_async(address)
              elif currency == 'usdt_bep20':
                  bal = await get_usdt_balance_parallel(USDT_BEP20_CONTRACT, address, BEP20_RPC_URLS, USDT_BEP20_DECIMALS)
              elif currency == 'usdt_polygon':
                  bal = await get_usdt_balance_parallel(USDT_POLYGON_CONTRACT, address, POLYGON_RPC_URLS, USDT_POLYGON_DECIMALS)
              elif currency == 'solana':
                  bal = await get_solana_balance_parallel(address)
              elif currency == 'ethereum':
                  bal = await get_eth_balance_parallel(address)
              else:
                  bal = 0
                  
              if bal > 0:
                 usbal = await currency_to_usd(bal, currency)
                 deal['ltc_amount'] = bal
                 update_deal(interaction.channel.id, deal)
                 
                 currency_display = {
                     'ltc': 'LTC',
                     'usdt_bep20': 'USDT (BEP20)',
                     'usdt_polygon': 'USDT (Polygon)',
                     'solana': 'SOL',
                     'ethereum': 'ETH'
                 }.get(currency, 'Crypto')
                 
                 confirmed_embed = discord.Embed(title="Deal Confirmation", color=0x0000ff, description=">>> Payment successfully received.")
                 confirmed_embed.add_field(name=f"{currency_display} Amount", value=f"{bal}", inline=False)
                 confirmed_embed.add_field(name="USD Amount", value=f"{usbal}$", inline=False)
                 confirmed_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1438896774243942432/1446517314433454342/discotools-xyz-icon.png?ex=693445ba&is=6932f43a&hm=379aa3c340acbe860daf7e83bea918027868d2b08b73594728a73220cbc340bf&")
                 await interaction.channel.send(embed=confirmed_embed, view=ReleaseButton(), content=f"<@{buyer}> <@{seller}>")
                 break
        else:
            await interaction.response.send_message("You are not authorized to use this.", ephemeral=True)

    async def cancel(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        seller = deal['seller']  # Now represents SENDER
        currency = deal.get('currency', 'ltc')
        
        if interaction.user.id == int(seller):  # SENDER cancels
            await interaction.response.defer()
            await interaction.message.edit(view=None)
            embed = discord.Embed(description=f"{interaction.user.mention} has cancelled the deal.")
            await interaction.channel.send(embed=embed)
            seller_id = int(deal['seller'])  # SENDER ID
            buyer_id = int(deal['buyer'])  # RECEIVER ID
            
            currency_display = {
                'ltc': 'LTC',
                'usdt_bep20': 'USDT (BEP20)',
                'usdt_polygon': 'USDT (Polygon)',
                'solana': 'SOL',
                'ethereum': 'ETH'
            }.get(currency, 'crypto')
            
            await interaction.channel.send(f"Please send your {currency_display} address to get the funds back. ||<@{buyer_id}>||")
            def check(msg):
                return msg.author.id == buyer_id and msg.channel == interaction.channel

            while True:
                msg = await interaction.client.wait_for("message", check=check)
                address = msg.content.strip()

                if await is_valid_address(address, currency):
                    try:
                        tx_hash = await send_funds_based_on_currency(deal, address)
                        
                        currency_display_full = {
                            'ltc': 'Litecoin',
                            'usdt_bep20': 'USDT (BEP20)',
                            'usdt_polygon': 'USDT (Polygon)',
                            'solana': 'Solana (SOL)',
                            'ethereum': 'Ethereum (ETH)'
                        }.get(currency, 'Crypto')
                        
                        explorer_url = get_explorer_url(currency, tx_hash)
                        
                        em = discord.Embed(title=f"{currency_display_full} Sent", description=f"Address: `{address}`\nTransaction ID: [{tx_hash}]({explorer_url})", color=0x0000ff)
                        await msg.reply(embed=em)
                        await send_transcript(interaction.channel, seller_id, buyer_id)
                        deals = load_all_data()
                        await asyncio.sleep(100)
                        await interaction.channel.delete()
                    except Exception as e:
                        await msg.reply(f"Failed to send {currency_display}: `{str(e)}`")
                    break
                else:
                    continue
        else:
            await interaction.response.send_message("You are not authorized to use this.", ephemeral=True)

class RescanButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        button = Button(label="Rescan", style=discord.ButtonStyle.green, custom_id="rescan")
        button.callback = self.rescan
        self.add_item(button)

    async def rescan(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        seller_id = int(deal['seller'])  # Now represents SENDER
        buyer_id = int(deal['buyer'])  # Now represents RECEIVER
        
        if interaction.user.id not in (seller_id, buyer_id):
            await interaction.response.send_message("You are not authorized to use this.", ephemeral=True)
            return
            
        rescan_count = deal.get('rescan_count', 0)
        if rescan_count >= 2:
            await interaction.response.send_message("You've already used all rescan attempts.", ephemeral=True)
            return
            
        deal['rescan_count'] = rescan_count + 1
        deal['payment_timeout'] = deal.get('payment_timeout', 1 * 1200) + 1 * 60
        update_deal(interaction.channel.id, deal)
        
        await interaction.response.defer()
        await interaction.message.delete()
        
        embed = discord.Embed(
            title="Payment Time Extended",
            color=0x00ff00,
            description=f">>> Payment time has been extended by 20 minutes. You have {2 - deal['rescan_count']} rescan attempts remaining."
        )
        await interaction.channel.send(embed=embed)
        
        address = deal['address']
        crypto_amount = deal['ltc_amount']
        em = discord.Embed()
        em.set_author(name="Waiting for transaction...")
        msg = await interaction.channel.send(embed=em)
        bot.loop.create_task(check_payment_multicurrency(address, interaction.channel, crypto_amount, deal, msg))

class ReleaseButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.release_button = Button(label="Release", style=discord.ButtonStyle.green, custom_id="release")
        self.release_button.callback = self.release
        self.add_item(self.release_button)
        self.cancel_button = Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="canrel")
        self.cancel_button.callback = self.cancel
        self.add_item(self.cancel_button)
        self.seller_con = False  # Now represents SENDER confirmation
        self.buyer_con = False  # Now represents RECEIVER confirmation
        self.lock = asyncio.Lock()
        buttonu = Button(label="More Info", style=discord.ButtonStyle.gray, custom_id="jfo")
        buttonu.callback = self.info
        self.add_item(buttonu)

    async def info(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        seller_id = int(deal['seller'])  # Now represents SENDER
        buyer_id = int(deal['buyer'])  # Now represents RECEIVER
        if interaction.user.id == seller_id or interaction.user.id == buyer_id:
            embed = discord.Embed(title="Deal Guide", color=0x0000ff, description=f"**After Completing the deal:**\n<@{buyer_id}> must click **Release** and **Confirm** to transfer the funds to <@{seller_id}>.\n**To Cancel this deal:**\n<@{seller_id}> must click **Cancel** and **Confirm** to transfer the funds to <@{buyer_id}>.")
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1373630302710399039/1387516877139476551/ddg9MWL.png?ex=685da14a&is=685c4fca&hm=7f2145fa614533ed4b84661299cb955e67d54bd4f16962b67e7350cfc593d972&")
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
             await interaction.response.send_message("You are not authorized to check this.", ephemeral=True)
             return

    async def cancel(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        seller_id = int(deal['seller'])  # Now represents SENDER
        buyer_id = int(deal['buyer'])  # Now represents RECEIVER
        ltc_amount = deal['ltc_amount']
        usd_amount = deal['amount']
        currency = deal.get('currency', 'ltc')

        if interaction.user.id == seller_id:  # SENDER cancels
            if getattr(self, "seller_con", False):
                await interaction.response.send_message("You have already confirmed cancellation.", ephemeral=True)
                return
            self.seller_con = True
        elif interaction.user.id == buyer_id:  # RECEIVER cancels
            if getattr(self, "buyer_con", False):
                await interaction.response.send_message("You have already confirmed cancellation.", ephemeral=True)
                return
            self.buyer_con = True
        else:
            await interaction.response.send_message("You are not authorized to cancel the deal.", ephemeral=True)
            return

        await interaction.response.defer()
        embed = discord.Embed(description=f"{interaction.user.mention} has cancelled the deal.")
        await interaction.channel.send(embed=embed)

        if getattr(self, "seller_con", False) and getattr(self, "buyer_con", False):
            self.cancel_button.disabled = True
            self.release_button.disabled = True

            deal["release_message_id"] = interaction.message.id
            update_deal(interaction.channel.id, deal)

            currency_display = {
                'ltc': 'LTC',
                'usdt_bep20': 'USDT (BEP20)',
                'usdt_polygon': 'USDT (Polygon)',
                'solana': 'SOL',
                'ethereum': 'ETH'
            }.get(currency, 'Crypto')

            embed = discord.Embed(
                title="Confirm Cancellation",
                color=discord.Color.red(),
                description=(
                    f"Are you sure you would like to cancel this deal? Funds will be refunded to the **SENDER** (<@{buyer_id}>). "
                    "This means that the deal is now cancelled, and cannot be reverted once cancelled."
                )
            )
            embed.add_field(name="Refunding Amount", value=f"USD: `{usd_amount}$`\n{currency_display}: `{ltc_amount:.8f}`", inline=False)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1373630302710399039/1387685827697442876/3mjo6QL.png")

            await interaction.message.edit(view=self)
            await interaction.channel.send(embed=embed, view=CancelConButton(), content=f"<@{seller_id}>")

    async def release(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        seller_id = int(deal['seller'])  # Now represents SENDER
        buyer_id = int(deal['buyer'])  # Now represents RECEIVER
        currency = deal.get('currency', 'ltc')
        
        if interaction.user.id == buyer_id:  # RECEIVER releases funds to SENDER
            await interaction.response.defer()
            
            currency_display = {
                'ltc': 'LTC',
                'usdt_bep20': 'USDT (BEP20)',
                'usdt_polygon': 'USDT (Polygon)',
                'solana': 'SOL',
                'ethereum': 'ETH'
            }.get(currency, 'crypto')
            
            embed = discord.Embed(title="Release Confirmation", color=0x0000ff, description=f"<@{buyer_id}> Are you sure you want to release the funds to <@{seller_id}>?\n\n**Note:** Once released, the funds cannot be reversed.")
            embed.set_footer(text="Our Staffs will never ask you to release the funds.")
            await interaction.followup.send(embed=embed, view=ReleaseConButton())
            await interaction.message.delete()
        else:
            await interaction.response.send_message("You are not authorized to release the funds.", ephemeral=True)
            return

class ReleaseConButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        button = Button(label="Confirm", style=discord.ButtonStyle.green, custom_id="relcon")
        button.callback = self.confirm
        self.add_item(button)
        buttons = Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="relcan")
        buttons.callback = self.cancel
        self.add_item(buttons)

    async def confirm(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        seller_id = int(deal['seller'])  # Now represents SENDER
        buyer_id = int(deal['buyer'])  # Now represents RECEIVER
        currency = deal.get('currency', 'ltc')

        if interaction.user.id == buyer_id:  # RECEIVER confirms release to SENDER
            await interaction.response.defer()
            await interaction.message.edit(view=None)
            embed = discord.Embed(description=f"{interaction.user.mention} has confirmed to release the funds.")
            await interaction.channel.send(embed=embed)
            
            currency_display = {
                'ltc': 'LTC',
                'usdt_bep20': 'USDT (BEP20)',
                'usdt_polygon': 'USDT (Polygon)',
                'solana': 'SOL',
                'ethereum': 'ETH'
            }.get(currency, 'crypto')
            
            em = discord.Embed(title="Release Funds", color=0x0000ff, description=f"<@{seller_id}> Please send your {currency_display} address to get the funds.")
            await interaction.channel.send(embed=em)
            def check(msg):
                return msg.author.id == seller_id and msg.channel == interaction.channel

            while True:
                msg = await interaction.client.wait_for("message", check=check)
                address = msg.content.strip()

                if await is_valid_address(address, currency):
                    try:
                        tx_hash = await send_funds_based_on_currency(deal, address)
                        
                        currency_display_full = {
                            'ltc': 'Litecoin',
                            'usdt_bep20': 'USDT (BEP20)',
                            'usdt_polygon': 'USDT (Polygon)',
                            'solana': 'Solana (SOL)',
                            'ethereum': 'Ethereum (ETH)'
                        }.get(currency, 'Crypto')
                        
                        explorer_url = get_explorer_url(currency, tx_hash)
                        
                        em = discord.Embed(title=f"{currency_display_full} Released", description=f"Address: `{address}`\nTransaction ID: [{tx_hash}]({explorer_url})", color=0x0000ff)
                        await msg.reply(embed=em)
                        await send_transcript(interaction.channel, seller_id, buyer_id)
                        deals = load_all_data()
                        if deal_id in deals:
                            del deals[deal_id]
                        save_all_data(deals)
                        await asyncio.sleep(100)
                        await interaction.channel.delete()
                    except Exception as e:
                        await msg.reply(f"Failed to send {currency_display}: `{str(e)}`")
                    break
                else:
                    continue
        else:
            await interaction.response.send_message("You are not authorized to use this.", ephemeral=True)

    async def cancel(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        seller_id = int(deal['seller'])  # Now represents SENDER
        buyer_id = int(deal['buyer'])  # Now represents RECEIVER
        ltcamt = deal['ltc_amount']
        currency = deal.get('currency', 'ltc')

        if interaction.user.id == buyer_id:  # RECEIVER cancels release
            await interaction.response.defer()
            await interaction.message.edit(view=None)
            embed = discord.Embed(description=f"{interaction.user.mention} has cancelled the release.")
            await interaction.channel.send(embed=embed)
            usbal = await currency_to_usd(ltcamt, currency)
            
            currency_display = {
                'ltc': 'LTC',
                'usdt_bep20': 'USDT (BEP20)',
                'usdt_polygon': 'USDT (Polygon)',
                'solana': 'SOL',
                'ethereum': 'ETH'
            }.get(currency, 'Crypto')
            
            confirmed_embed = discord.Embed(title="Deal Confirmation", color=0x0000ff, description=">>> Payment successfully received.")
            confirmed_embed.add_field(name=f"{currency_display} Amount", value=f"{ltcamt:.8f}", inline=False)
            confirmed_embed.add_field(name="USD Amount", value=f"{usbal}$", inline=False)
            confirmed_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1384928504189026466/1385336614699532449/IMG_1336.png?ex=6855b2c3&is=68546143&hm=f3ad66f898ac9a5281b0cbd027111eebcb0f4bebc4cfb1fbe9f53922a45793d7&")
            await interaction.channel.send(embed=confirmed_embed, view=ReleaseButton())
        else:
            await interaction.response.send_message("You are not authorized to use this.", ephemeral=True)

class CancelConButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        button = Button(label="Confirm", style=discord.ButtonStyle.green, custom_id="cancon")
        button.callback = self.confirm
        self.add_item(button)
        buttons = Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancan")
        buttons.callback = self.cancel
        self.add_item(buttons)

    async def confirm(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        seller_id = int(deal['seller'])  # Now represents SENDER
        buyer_id = int(deal['buyer'])  # Now represents RECEIVER
        currency = deal.get('currency', 'ltc')

        if interaction.user.id == seller_id:  # SENDER confirms cancellation
            await interaction.response.defer()
            await interaction.message.edit(view=None)
            embed = discord.Embed(description=f"{interaction.user.mention} has confirmed to cancel the deal.")
            await interaction.channel.send(embed=embed)
            
            currency_display = {
                'ltc': 'LTC',
                'usdt_bep20': 'USDT (BEP20)',
                'usdt_polygon': 'USDT (Polygon)',
                'solana': 'SOL',
                'ethereum': 'ETH'
            }.get(currency, 'crypto')
            
            em = discord.Embed(title="Cancel Deal", color=0x0000ff, description=f"<@{buyer_id}> Please send your {currency_display} address to get the funds back.")
            await interaction.channel.send(embed=em)
            def check(msg):
                return msg.author.id == buyer_id and msg.channel == interaction.channel

            while True:
                msg = await interaction.client.wait_for("message", check=check)
                address = msg.content.strip()

                if await is_valid_address(address, currency):
                    try:
                        tx_hash = await send_funds_based_on_currency(deal, address)
                        
                        currency_display_full = {
                            'ltc': 'Litecoin',
                            'usdt_bep20': 'USDT (BEP20)',
                            'usdt_polygon': 'USDT (Polygon)',
                            'solana': 'Solana (SOL)',
                            'ethereum': 'Ethereum (ETH)'
                        }.get(currency, 'Crypto')
                        
                        explorer_url = get_explorer_url(currency, tx_hash)
                        
                        em = discord.Embed(title=f"{currency_display_full} Sent", description=f"Address: `{address}`\nTransaction ID: [{tx_hash}]({explorer_url})", color=0x0000ff)
                        await msg.reply(embed=em)
                        await send_transcript(interaction.channel, seller_id, buyer_id)
                        deals = load_all_data()
                        await asyncio.sleep(100)
                        await interaction.channel.delete()
                    except Exception as e:
                        await msg.reply(f"Failed to send {currency_display}: `{str(e)}`")
                    break
                else:
                    continue

        else:
            await interaction.response.send_message("You are not authorized to use this.", ephemeral=True)

    async def cancel(self, interaction: discord.Interaction):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            await interaction.response.send_message("Deal not found.", ephemeral=True)
            return
            
        seller_id = int(deal['seller'])  # Now represents SENDER
        buyer_id = int(deal['buyer'])  # Now represents RECEIVER
        ltcamt = deal['ltc_amount']

        if interaction.user.id == buyer_id:  # RECEIVER cancels
            await interaction.response.defer()
            embed = discord.Embed(description=f"{interaction.user.mention} has cancelled the release.")
            await interaction.channel.send(embed=embed)
            release_msg_id = deal['release_message_id']
            msg = await interaction.channel.fetch_message(release_msg_id)
            view = ReleaseButton()
            view.release_button.disabled = False
            view.cancel_button.disabled = False
            await msg.edit(view=view)
        else:
            await interaction.response.send_message("You are not authorized to use this.", ephemeral=True)

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

async def is_valid_address(address: str, currency: str) -> bool:
    """Validate address based on currency"""
    if currency == 'ltc':
        return await is_valid_ltc_address(address)
    elif currency in ['usdt_bep20', 'usdt_polygon', 'ethereum']:
        return Web3.is_address(address)
    elif currency == 'solana':
        try:
            from solders.pubkey import Pubkey
            Pubkey.from_string(address)
            return True
        except:
            return False
    return False

async def is_valid_ltc_address(address: str) -> bool:
    """Validate LTC address"""
    url = f"https://litecoinspace.org/api/address/{address}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return resp.status == 200
    except Exception:
        return False

def get_explorer_url(currency: str, tx_hash: str) -> str:
    """Get blockchain explorer URL for transaction"""
    if currency == 'ltc':
        return f"https://live.blockcypher.com/ltc/tx/{tx_hash}/"
    elif currency == 'usdt_bep20':
        return f"https://bscscan.com/tx/0x{tx_hash}"
    elif currency == 'usdt_polygon':
        return f"https://polygonscan.com/tx/0x{tx_hash}"
    elif currency == 'solana':
        return f"https://solscan.io/tx/{tx_hash}"
    elif currency == 'ethereum':
        return f"https://etherscan.io/tx/0x{tx_hash}"
    return "#"

async def generate_qr_bytes(text):
    """Generate QR code bytes"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        with io.BytesIO() as output:
            img.save(output, format="PNG")
            return output.getvalue()
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

# =====================================================
# BOT COMMANDS
# =====================================================

@bot.tree.command(name="check_balance", description="Check balance for any currency address")
@app_commands.describe(address="Wallet address", currency="Currency type")
async def check_balance_cmd(interaction: discord.Interaction, address: str, currency: str = "ltc"):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in OWNER:
        await interaction.followup.send("You are not authorized.", ephemeral=True)
        return

    try:
        if currency == "ltc":
            confirmed, unconfirmed = await get_balance_async(address)
            total = confirmed + unconfirmed
        elif currency == "usdt_bep20":
            total = await get_usdt_balance_parallel(USDT_BEP20_CONTRACT, address, BEP20_RPC_URLS, USDT_BEP20_DECIMALS)
            confirmed = total
            unconfirmed = 0
        elif currency == "usdt_polygon":
            total = await get_usdt_balance_parallel(USDT_POLYGON_CONTRACT, address, POLYGON_RPC_URLS, USDT_POLYGON_DECIMALS)
            confirmed = total
            unconfirmed = 0
        elif currency == "solana":
            total = await get_solana_balance_parallel(address)
            confirmed = total
            unconfirmed = 0
        elif currency == "ethereum":
            total = await get_eth_balance_parallel(address)
            confirmed = total
            unconfirmed = 0
        else:
            await interaction.followup.send("Unsupported currency.", ephemeral=True)
            return

        usd_value = await currency_to_usd(total, currency)
        
        currency_display = {
            'ltc': 'LTC',
            'usdt_bep20': 'USDT (BEP20)',
            'usdt_polygon': 'USDT (Polygon)',
            'solana': 'SOL',
            'ethereum': 'ETH'
        }.get(currency, currency.upper())
        
        embed = discord.Embed(title=f"{currency_display} Balance", color=0x0000ff)
        embed.add_field(name="Address", value=f"`{address}`", inline=False)
        embed.add_field(name="Confirmed", value=f"`{confirmed}`", inline=True)
        embed.add_field(name="Unconfirmed", value=f"`{unconfirmed}`", inline=True)
        embed.add_field(name="Total", value=f"`{total}`", inline=True)
        embed.add_field(name="USD Value", value=f"`${usd_value:.2f}`", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="check_txid", description="Check Ethereum transaction details")
@app_commands.describe(tx_signature="Ethereum transaction hash")
async def check_txid_cmd(interaction: discord.Interaction, tx_signature: str):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in OWNER:
        await interaction.followup.send("You are not authorized.", ephemeral=True)
        return

    try:
        # For ETH transactions, we need to use web3 to get details
        tx_details = None
        for rpc_url in ETH_RPC_URLS:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    tx_details = w3.eth.get_transaction(tx_signature)
                    if tx_details:
                        break
            except:
                continue

        if not tx_details:
            await interaction.followup.send("Transaction not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Ethereum Transaction Details",
            color=0x0000ff
        )

        # Extract basic info
        block_number = tx_details.blockNumber
        from_addr = tx_details['from']
        to_addr = tx_details['to']
        value_eth = tx_details.value / (10 ** 18)
        gas_used = tx_details.gas
        gas_price = tx_details.gasPrice / (10 ** 9)  # Convert to Gwei

        # Get block timestamp
        block_timestamp = None
        for rpc_url in ETH_RPC_URLS:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    block = w3.eth.get_block(block_number)
                    block_timestamp = block.timestamp
                    break
            except:
                continue

        if block_timestamp:
            from datetime import datetime
            timestamp = datetime.fromtimestamp(block_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp = 'Unknown'

        embed.add_field(name="Transaction Hash", value=f"`{tx_signature}`", inline=False)
        embed.add_field(name="From", value=f"`{from_addr}`", inline=False)
        embed.add_field(name="To", value=f"`{to_addr}`", inline=False)
        embed.add_field(name="Value", value=f"`{value_eth:.6f} ETH`", inline=True)
        embed.add_field(name="Block", value=f"`{block_number}`", inline=True)
        embed.add_field(name="Gas Used", value=f"`{gas_used}`", inline=True)
        embed.add_field(name="Gas Price", value=f"`{gas_price:.2f} Gwei`", inline=True)
        embed.add_field(name="Timestamp", value=f"`{timestamp}`", inline=True)

        embed.add_field(
            name="Explorer", 
            value=f"[View on Etherscan](https://etherscan.io/tx/0x{tx_signature})", 
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="list_transactions", description="List recent Ethereum transactions for address")
@app_commands.describe(address="Ethereum address")
async def list_transactions_cmd(interaction: discord.Interaction, address: str):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in OWNER:
        await interaction.followup.send("You are not authorized.", ephemeral=True)
        return

    try:
        # For ETH, we'll get recent transactions from Etherscan-like API
        # Note: This is a simplified version - you might want to use a proper ETH block explorer API
        embed = discord.Embed(
            title=f"Ethereum Address - {address[:8]}...{address[-8:]}",
            color=0x0000ff
        )

        # Get current balance
        balance = await get_eth_balance_parallel(address)
        usd_value = await currency_to_usd(balance, "ethereum")

        embed.add_field(name="Current Balance", value=f"`{balance:.6f} ETH` (${usd_value:.2f})", inline=False)
        embed.add_field(
            name="Explorer", 
            value=f"[View on Etherscan](https://etherscan.io/address/{address})", 
            inline=False
        )

        embed.add_field(
            name="Note", 
            value="For detailed transaction history, please use Etherscan directly.", 
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="force_cancel", description="Force cancel a deal and refund (Owner Only)")
@app_commands.describe(deal_id="The deal ID", user="User to refund")
async def force_cancel(interaction: discord.Interaction, deal_id: str, user: discord.User):
    await interaction.response.defer()

    if interaction.user.id not in OWNER:
        await interaction.followup.send("You are not authorized.", ephemeral=True)
        return

    deal = get_deal_by_dealid(deal_id)
    if not deal:
        await interaction.followup.send("Deal not found.", ephemeral=True)
        return

    pending_force_actions[user.id] = {
        "deal_id": deal_id,
        "type": "cancel", 
        "deal": deal
    }

    currency_display = {
        'ltc': 'LTC',
        'usdt_bep20': 'USDT (BEP20)',
        'usdt_polygon': 'USDT (Polygon)',
        'solana': 'SOL',
        'ethereum': 'ETH'
    }.get(deal.get('currency', 'ltc'), 'crypto')

    embed = discord.Embed(
        title="Force Cancel Initiated",
        color=0xff0000,
        description=(
            f"<@{user.id}> your deal has been force-cancelled by the admin.\n\n"
            f"Please **send your {currency_display} address here** to receive your refund."
        )
    )
    
    channel_id = deal.get('channel_id')
    if channel_id:
        channel = bot.get_channel(int(channel_id))
        if channel:
            await channel.send(embed=embed)
    
    await interaction.followup.send("Force cancel started.", ephemeral=True)

@bot.tree.command(name="force_release", description="Force release funds to the seller. (Owner Only)")
@app_commands.describe(deal_id="The deal ID", user="User to release to")
async def force_release(interaction: discord.Interaction, deal_id: str, user: discord.User):
    await interaction.response.defer()

    if interaction.user.id not in OWNER:
        await interaction.followup.send("You are not authorized.", ephemeral=True)
        return

    deal = get_deal_by_dealid(deal_id)
    if not deal:
        await interaction.followup.send("Deal not found.", ephemeral=True)
        return

    pending_force_actions[user.id] = {
        "deal_id": deal_id,
        "type": "release",
        "deal": deal
    }

    currency_display = {
        'ltc': 'LTC',
        'usdt_bep20': 'USDT (BEP20)',
        'usdt_polygon': 'USDT (Polygon)',
        'solana': 'SOL',
        'ethereum': 'ETH'
    }.get(deal.get('currency', 'ltc'), 'crypto')

    embed = discord.Embed(
        title="Force Release Initiated",
        color=0x0000ff,
        description=(
            f"<@{user.id}> admin has force-released the deal.\n\n"
            f"Please **send your {currency_display} address** to receive the funds."
        )
    )

    channel_id = deal.get('channel_id')
    if channel_id:
        channel = bot.get_channel(int(channel_id))
        if channel:
            await channel.send(embed=embed)
    
    await interaction.followup.send("Force release started.", ephemeral=True)

@bot.tree.command(name="add", description="Add a user to this deal channel.")
@app_commands.describe(user="User to add in this channel.")
async def add_user_cmd(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id not in OWNER:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    channel = interaction.channel

    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("This command can only be used inside a text channel.", ephemeral=True)
        return

    try:
        await channel.set_permissions(
            user,
            read_messages=True,
            send_messages=True,
            read_message_history=True,
            view_channel=True
        )
    except Exception as e:
        await interaction.response.send_message(f"Failed to add user: {e}", ephemeral=True)
        return

    embed = discord.Embed(
        title="User Added",
        description=f"> **{user.mention}** has been added to this channel.",
        color=0x0000ff
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="remove", description="Remove a user from this deal channel.")
@app_commands.describe(user="User to remove from this channel.")
async def remove_user_cmd(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id not in OWNER:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    channel = interaction.channel

    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("This command can only be used inside a text channel.", ephemeral=True)
        return

    try:
        await channel.set_permissions(user, overwrite=None)
    except Exception as e:
        await interaction.response.send_message(f"Failed to remove user: {e}", ephemeral=True)
        return

    embed = discord.Embed(
        title="User Removed",
        description=f"> **{user.mention}** has been removed from this channel.",
        color=0xff0000
    )

    await interaction.response.send_message(embed=embed)

# =====================================================
# EXISTING COMMANDS (PRESERVED)
# =====================================================

@bot.tree.command(name="transcript", description="Export transcript of a channel")
@app_commands.describe(
    channel_id="The channel ID to export transcript from",
    user="User to DM the transcript to (optional)",
    target_channel="Channel to send transcript to (optional)"
)
async def transcript_cmd(
    interaction: discord.Interaction, 
    channel_id: str,
    user: discord.User = None,
    target_channel: discord.TextChannel = None
):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in OWNER:
        await interaction.followup.send("You are not authorized to use this command.", ephemeral=True)
        return

    try:
        channel = bot.get_channel(int(channel_id))
        if not channel:
            await interaction.followup.send("Invalid channel ID.", ephemeral=True)
            return

        transcript = await chat_exporter.export(
            channel,
            tz_info="Asia/Kolkata",
            military_time=True,
            fancy_times=True
        )

        if not transcript:
            await interaction.followup.send("Failed to export transcript.", ephemeral=True)
            return

        transcript_bytes = transcript.encode("utf-8")
        file = discord.File(io.BytesIO(transcript_bytes), filename=f"{channel.name}_transcript.html")

        embed = discord.Embed(
            title="Channel Transcript",
            description=f"Transcript for channel: {channel.mention}",
            color=0x0000ff
        )

        if user:
            try:
                await user.send(embed=embed, file=file)
                await interaction.followup.send(f"Transcript sent to {user.mention}", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Failed to DM user: {e}", ephemeral=True)
        
        elif target_channel:
            await target_channel.send(embed=embed, file=file)
            await interaction.followup.send(f"Transcript sent to {target_channel.mention}", ephemeral=True)
        
        else:
            await interaction.followup.send(embed=embed, file=file, ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="send_funds", description="Send funds from a deal wallet (Owner Only)")
@app_commands.describe(deal_id="The deal ID", address="Address to send to")
async def send_funds_command(interaction: discord.Interaction, deal_id: str, address: str):
    await interaction.response.defer()

    if interaction.user.id not in OWNER:
        await interaction.followup.send("You are not authorized to use this command.", ephemeral=True)
        return

    deal = get_deal_by_dealid(deal_id)
    if not deal:
        await interaction.followup.send("Deal not found.", ephemeral=True)
        return

    currency = deal.get('currency', 'ltc')
    if not await is_valid_address(address, currency):
        await interaction.followup.send(f"Invalid {currency.upper()} address.", ephemeral=True)
        return

    try:
        tx_hash = await send_funds_based_on_currency(deal, address)
        
        currency_display = {
            'ltc': 'Litecoin',
            'usdt_bep20': 'USDT (BEP20)',
            'usdt_polygon': 'USDT (Polygon)',
            'solana': 'Solana (SOL)',
            'ethereum': 'Ethereum (ETH)'
        }.get(currency, 'Crypto')
        
        explorer_url = get_explorer_url(currency, tx_hash)
        
        em = discord.Embed(
            title=f"{currency_display} Sent (Admin)",
            description=f"Address: `{address}`\nTransaction ID: [{tx_hash}]({explorer_url})",
            color=0x0000ff
        )
        await interaction.followup.send(embed=em)

    except Exception as e:
        await interaction.followup.send(f"Failed to send funds: `{str(e)}`", ephemeral=True)


@bot.tree.command(name="find_deal_id", description="Find deal ID by address or channel ID")
@app_commands.describe(
    address="Address to search for (optional)",
    channel_id="Channel ID to search for (optional)"
)
async def find_deal_id_cmd(
    interaction: discord.Interaction, 
    address: str = None, 
    channel_id: str = None
):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in OWNER:
        await interaction.followup.send("You are not authorized to use this command.", ephemeral=True)
        return

    if not address and not channel_id:
        await interaction.followup.send("Please provide either address or channel ID.", ephemeral=True)
        return

    data = load_all_data()
    found_deals = []

    if address:
        for deal_id, deal in data.items():
            if deal.get("address") == address:
                found_deals.append((deal_id, deal))
    
    if channel_id:
        for deal_id, deal in data.items():
            if str(deal.get("channel_id")) == str(channel_id):
                found_deals.append((deal_id, deal))

    if not found_deals:
        await interaction.followup.send("No deals found matching the criteria.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Found Deals",
        color=0x0000ff
    )

    for deal_id, deal in found_deals:
        channel_info = f"Channel: `{deal.get('channel_id', 'Unknown')}`"
        seller_info = f"Seller: `{deal.get('seller', 'Unknown')}`"
        buyer_info = f"Buyer: `{deal.get('buyer', 'Unknown')}`"
        address_info = f"Address: `{deal.get('address', 'Unknown')}`"
        currency_info = f"Currency: `{deal.get('currency', 'ltc')}`"
        
        embed.add_field(
            name=f"Deal ID: `{deal_id}`",
            value=f"{channel_info}\n{seller_info}\n{buyer_info}\n{address_info}\n{currency_info}",
            inline=False
        )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="change_channel_id", description="Change channel ID for a deal")
@app_commands.describe(
    deal_id="The deal ID to update",
    new_channel_id="The new channel ID"
)
async def change_channel_id_cmd(interaction: discord.Interaction, deal_id: str, new_channel_id: str):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in OWNER:
        await interaction.followup.send("You are not authorized to use this command.", ephemeral=True)
        return

    data = load_all_data()
    if deal_id not in data:
        await interaction.followup.send("Deal not found.", ephemeral=True)
        return

    old_channel_id = data[deal_id].get("channel_id")
    data[deal_id]["channel_id"] = new_channel_id
    save_all_data(data)

    embed = discord.Embed(
        title="Channel ID Updated",
        description=f"Deal `{deal_id}` channel ID updated from `{old_channel_id}` to `{new_channel_id}`",
        color=0x00ff00
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="get_deal_info", description="Get full information about a deal")
@app_commands.describe(deal_id="The deal ID to get information for")
async def get_deal_info_cmd(interaction: discord.Interaction, deal_id: str):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in OWNER:
        await interaction.followup.send("You are not authorized to use this command.", ephemeral=True)
        return

    deal = get_deal_by_dealid(deal_id)
    if not deal:
        await interaction.followup.send("Deal not found.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"Deal Information - {deal_id}",
        color=0x0000ff
    )

    for key, value in deal.items():
        if key == "private_key":
            if value and len(value) > 20:
                display_value = f"{value[:10]}...{value[-10:]}"
            else:
                display_value = "***"
        else:
            display_value = str(value) if value else "None"
        
        embed.add_field(name=key, value=f"`{display_value}`", inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="close", description="Close the ticket and save transcript.")
async def close_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    # --- EXECUTIVE ROLE CHECK ---
    if EXECUTIVE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        await interaction.followup.send("You are not authorized to use this command.", ephemeral=True)
        return
    # -----------------------------

    try:
        deal_id, deal = get_deal_by_channel(interaction.channel.id)

        if deal is None:
            await interaction.followup.send("No deal data found for this channel.", ephemeral=True)
            return

        seller_id = None
        buyer_id = None

        if isinstance(deal, dict):
            if deal.get("seller") not in ("None", None, ""):
                try:
                    seller_id = int(deal["seller"])
                except:
                    seller_id = None

            if deal.get("buyer") not in ("None", None, ""):
                try:
                    buyer_id = int(deal["buyer"])
                except:
                    buyer_id = None
        else:
            await interaction.followup.send("Deal data format error.", ephemeral=True)
            return

        # Save transcript
        if seller_id or buyer_id:
            try:
                await send_transcript(interaction.channel, seller_id or 0, buyer_id or 0)
            except Exception as e:
                print("Transcript error:", e)
                await interaction.followup.send("Transcript could not be created, but the ticket will still close.", ephemeral=True)
        else:
            await interaction.followup.send("No valid participants found. Closing ticket without transcript.", ephemeral=True)

        # DELETE CHANNEL (This was missing)
        try:
            await interaction.channel.delete(reason="Ticket closed by executive.")
        except Exception as e:
            print("Channel delete error:", e)

    except Exception as e:
        print("Close command error:", e)
        await interaction.followup.send("An error occurred while closing the ticket.", ephemeral=True)
# ========== CONFIRMATION BUTTONS ==========
class CloseAllConfirm(discord.ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=60)
        self.interaction = interaction

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        # Only original user can confirm
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message("This confirmation is not for you.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Closing all deal channels… please wait.", ephemeral=True)

        # Load data.json for seller/buyer
        try:
            with open("data.json", "r") as f:
                all_deals = json.load(f)
        except:
            all_deals = {}

        deleted = 0

        # Loop through both categories
        for cat_id in [CATEGORY_ID_1, CATEGORY_ID_2]:

            category = interaction.guild.get_channel(cat_id)
            if not category:
                continue

            for channel in category.channels:
                ch_id = str(channel.id)

                # Use real seller/buyer if exists in data.json
                if ch_id in all_deals:
                    deal = all_deals[ch_id]
                    seller_id = int(deal.get("seller", 0) or 0)
                    buyer_id = int(deal.get("buyer", 0) or 0)
                else:
                    # Not in data.json → transcript only, no logs or seller/buyer
                    seller_id = 0
                    buyer_id = 0

                # Save transcript no matter what
                try:
                    await send_transcript(channel, seller_id, buyer_id)
                except Exception as e:
                    print(f"[Transcript Error] {channel.id} → {e}")

                # Delete channel
                try:
                    await channel.delete(reason="Close-All executed by owner.")
                    deleted += 1
                except Exception as e:
                    print(f"[Delete Error] {channel.id} → {e}")

        await self.interaction.followup.send(
            f"✅ **Close-All Completed**\nAll deal channels deleted.\nTotal deleted: **{deleted}**",
            ephemeral=True
        )

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message("This is not for you.", ephemeral=True)

        await interaction.response.send_message("❌ Close-all cancelled.", ephemeral=True)
        self.stop()



# ========== MAIN /close_all COMMAND ==========
@bot.tree.command(name="close_all", description="Owner-only: Delete ALL deal channels and save transcripts.")
async def close_all(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    # OWNER CHECK
    if interaction.user.id not in OWNER:
        return await interaction.followup.send("You are not authorized to use this command.", ephemeral=True)

    embed = discord.Embed(
        title="⚠ Confirm Close All",
        description=(
            f"This will **delete every channel** inside:\n"
            f"- <#{CATEGORY_ID_1}>\n"
            f"- <#{CATEGORY_ID_2}>\n\n"
            f"✔ Transcript will be saved for ALL channels\n"
            f"✔ If channel is in `data.json` → real seller/buyer will be used\n"
            f"✔ If not → seller/buyer will be set to 0\n"
            f"✖ No logs will be sent for missing data\n\n"
            f"Are you sure you want to continue?"
        ),
        color=0x0000ff
    )
    embed.set_footer(text="RainyDay MM")

    await interaction.followup.send(
        embed=embed,
        view=CloseAllConfirm(interaction),
        ephemeral=True
    )

# =====================================================
# BOT EVENTS
# =====================================================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()
    ist = pytz.timezone('Asia/Kolkata')
    time = datetime.datetime.now(ist)
    date = time.strftime('%d/%m/%y')
    embed = discord.Embed(
        description=(
            "## <:emoji_303:1444562870208823377> RainyDay Auto Middleman\n\n"
            "## What is Auto Middleman?\n"
            "An escrow system used during trades. The buyer sends the funds to the escrow wallet, "
            "the seller delivers the product, and once the buyer confirms, the escrow safely releases the funds.\n\n"
            
            "## Why RainyDay MM?\n"
            "- Fully automated 24/7\n"
            "- Protects both buyer & seller\n"
            "- Fast support & instant updates\n"
            "- Zero service fees (only blockchain fees apply)\n"
            "- Secure, reliable and designed for smooth deals.\n\n"
            
        ),
        color=0x0000ff
    )

    # Footer icon = your logo (thumbnail removed)
    embed.set_footer(
        text=f"Always check https://rainyday.one",
        icon_url="https://cdn.discordapp.com/attachments/1383487913186169032/1384932699717898300/Untitled-2.png"
    )

    #embed = discord.Embed(description="# RainyDay Auto Middleman\n\n**What is Auto Middleman?**\nRainyDay Auto Middleman is an automated, secure escrow system designed to hold cryptocurrency on your behalf. It streamlines transactions, saves time, and ensures safer dealings between buyers and sellers.\n\n**Key Features:**\n- Supports LTC, USDT (BEP20), USDT (Polygon), Solana (SOL), and Ethereum (ETH)\n- Fully automated and available 24/7\n- Fast, efficient, and secure\n- Zero fees", color=0x0000ff)
    #embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1383487913186169032/1384932699717898300/Untitled-2.png?ex=68543a96&is=6852e916&hm=3f5566d93ca1ba539950f47e4ea4fbcf1c4b2e6873af9d97424656d867830d7a&")
    #embed.set_footer(text=f"RainyDay MM | {date}, {time}")
    channel = bot.get_channel(CHANNEL_ID)
    await channel.purge()
    await channel.send(embed=embed, view=CurrencySelectView())
    
    # Add all views
    bot.add_view(CurrencySelectView())
    bot.add_view(ToSButtonsAllInOne())
    bot.add_view(ToSButtonsAllInOnee())
    bot.add_view(LangButton())
    bot.add_view(SendButton())
    bot.add_view(ConfButtons())
    bot.add_view(TosView())
    bot.add_view(ToSCoButtons())
    bot.add_view(AmountConButton())
    bot.add_view(AddyButtons())
    bot.add_view(ProceedButton())
    bot.add_view(RescanButton())
    bot.add_view(ReleaseButton())
    bot.add_view(ReleaseConButton())
    bot.add_view(CancelConButton())

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id

    if user_id in pending_force_actions:
        action = pending_force_actions[user_id]
        deal_id = action["deal_id"]
        deal = action["deal"]
        addr = message.content.strip()
        currency = deal.get('currency', 'ltc')

        if not await is_valid_address(addr, currency):
            #await message.channel.send(f"Invalid {currency.upper()} address. Try again.")
            return

        try:
            txid = await send_funds_based_on_currency(deal, addr)

            currency_display = {
                'ltc': 'Litecoin',
                'usdt_bep20': 'USDT (BEP20)',
                'usdt_polygon': 'USDT (Polygon)',
                'solana': 'Solana (SOL)',
                'ethereum': 'Ethereum (ETH)'
            }.get(currency, 'Crypto')
            
            explorer_url = get_explorer_url(currency, txid)
            
            done_embed = discord.Embed(
                title="Funds Sent",
                color=0x00ff00,
                description=(
                    f"Funds successfully sent to `{addr}`.\n\n"
                    f"TXID: [{txid}]({explorer_url})"
                )
            )

            await message.channel.send(embed=done_embed)

        except Exception as e:
            await message.channel.send(f"Error sending {currency.upper()}: `{e}`")
            return

        del pending_force_actions[user_id]
        return

    await bot.process_commands(message)
# =====================================================
# EXISTING FUNCTIONS (PRESERVED)
# =====================================================

async def send_transcript(channel, seller_id, buyer_id, txid: str | None = None):
    """Existing transcript function"""
    try:
        seller = bot.get_user(seller_id)
        buyer = bot.get_user(buyer_id)
        log_channel = bot.get_channel(LOG_CHANNEL)
        history_channel = bot.get_channel(HISTORY_CHANNEL)

        deal_id = None
        deal = None

        result = get_deal_by_channel(channel.id)
        if result:
            deal_id, deal = result

        deal_id_str = str(deal_id) if deal_id else "Unknown"

        if isinstance(deal, dict):
            creator_raw = deal.get("creator_id", seller_id) or seller_id
            other_raw = deal.get("other_user_id", buyer_id) or buyer_id

            try:
                creator_id = int(creator_raw)
            except Exception:
                creator_id = seller_id

            try:
                other_id = int(other_raw)
            except Exception:
                other_id = buyer_id
        else:
            creator_id = seller_id
            other_id = buyer_id

        transcript = await chat_exporter.export(
            channel,
            tz_info="Asia/Kolkata",
            military_time=True,
            fancy_times=True
        )

        if not transcript:
            print("Transcript empty")
            return

        transcript_bytes = transcript.encode("utf-8")

        def id_only(uid: int | str):
            try:
                return f"{int(uid)}"
            except Exception:
                return str(uid)

        base_desc = (
            f"DEAL ID: `{deal_id_str}`\n"
            f"Channel: {channel.name}\n"
            f"**Deal Participants:**\n"
            f"• Ticket Creator: `{id_only(creator_id)}`\n"
            f"• Other Participant: `{id_only(other_id)}`"
        )

        transcript_embed = discord.Embed(
            title="RainyDay MM - Deal Transcript",
            description=f"{base_desc}\n\nTranscript file attached below.",
            color=0x0000ff
        )
        transcript_embed.add_field(name="Seller", value=f"`{id_only(seller_id)}`")
        transcript_embed.add_field(name="Buyer", value=f"`{id_only(buyer_id)}`")

        await channel.send(
            embed=transcript_embed,
            file=discord.File(io.BytesIO(transcript_bytes), filename=f"{channel.name}.html")
        )

        if log_channel:
            log_embed = discord.Embed(
                title="Deal completed",
                color=0x0000ff
            )
            log_embed.add_field(name="Buyer", value=f"`{id_only(buyer_id)}`", inline=True)
            log_embed.add_field(name="Seller", value=f"`{id_only(seller_id)}`", inline=True)

            view = None
            if txid:
                view = View()
                deal_currency = deal.get('currency', 'ltc') if deal else 'ltc'
                explorer_url = get_explorer_url(deal_currency, txid)
                view.add_item(Button(
                    label="Check on Blockchain",
                    style=discord.ButtonStyle.link,
                    url=explorer_url
                ))

            await log_channel.send(embed=log_embed)

        if history_channel and history_channel.id not in (channel.id, getattr(log_channel, "id", None)):
            await history_channel.send(
                embed=transcript_embed,
                file=discord.File(io.BytesIO(transcript_bytes), filename=f"{channel.name}.html")
            )

        if seller:
            try:
                dm_embed_seller = discord.Embed(
                    title="RainyDay MM - Deal Transcript",
                    color=0x0000ff,
                    description=(
                        f"{base_desc}\n\n"
                        f"**You (Seller):** `{id_only(seller_id)}`\n"
                        f"**Buyer:** `{id_only(buyer_id)}`"
                    )
                )

                await seller.send(
                    embed=dm_embed_seller,
                    file=discord.File(io.BytesIO(transcript_bytes), filename=f"{channel.name}.html")
                )
            except Exception:
                pass

        if buyer:
            try:
                dm_embed_buyer = discord.Embed(
                    title="RainyDay MM - Deal Transcript",
                    color=0x0000ff,
                    description=(
                        f"{base_desc}\n\n"
                        f"**Seller:** `{id_only(seller_id)}`\n"
                        f"**You (Buyer):** `{id_only(buyer_id)}`"
                    )
                )

                await buyer.send(
                    embed=dm_embed_buyer,
                    file=discord.File(io.BytesIO(transcript_bytes), filename=f"{channel.name}.html")
                )
            except Exception:
                pass

    except Exception as e:
        print(f"Error sending transcript: {e}")

# =====================================================
# RUN THE BOT
# =====================================================

bot.run(TOKEN)