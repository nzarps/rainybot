import os
from dotenv import load_dotenv

load_dotenv()

# Discord Configuration
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_IDS = [int(x) for x in os.getenv("OWNER_IDS", "0").split(",") if x.strip().isdigit()]

# Channels and Categories
# REPLACE THESE WITH YOUR ACTUAL IDS
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "1456658196247744543"))
CATEGORY_ID_1 = int(os.getenv("CATEGORY_ID_1", "1456657580674912256"))
CATEGORY_ID_2 = int(os.getenv("CATEGORY_ID_2", "0"))
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL_ID", "1456661028841721939"))
HISTORY_CHANNEL = int(os.getenv("HISTORY_CHANNEL_ID", "1456661028841721939"))
SUPPORT_CHANNEL_ID = int(os.getenv("SUPPORT_CHANNEL_ID", "1456661028841721939")) # Fallback to Log
CONTACT_MOD_LOG_CHANNEL_ID = int(os.getenv("CONTACT_MOD_LOG_CHANNEL_ID", "0"))

# Roles
EXECUTIVE_ROLE_ID = int(os.getenv("EXECUTIVE_ROLE_ID", "0"))

# Proxy (if used)
PROXY = None

# =====================================================
# CRYPTO RPC CONFIGURATION
# =====================================================

# LTC RPC
RPC_USER = os.getenv("LTC_RPC_USER", "rainyday")
RPC_PASSWORD = os.getenv("LTC_RPC_PASSWORD", "")
RPC_HOST = os.getenv("LTC_RPC_HOST", "127.0.0.1")
RPC_PORT = int(os.getenv("LTC_RPC_PORT", "9332"))
RPC_URL = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"

# ETH RPC
ETH_RPC_URLS = [
    url.strip() for url in os.getenv("ETH_RPC_URLS", "https://ethereum-rpc.publicnode.com,https://cloudflare-eth.com,https://rpc.flashbots.net,https://eth-mainnet.public.blastapi.io,https://eth.llamarpc.com,https://1rpc.io/eth").split(",")
]
ETH_DECIMALS = 18

# BSC (BEP20) RPC
BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/")
BEP20_RPC_URLS = [
    url.strip() for url in os.getenv("BSC_RPC_URLS", "https://bsc-dataseed.binance.org,https://bsc-dataseed1.ninicoin.io,https://bsc-dataseed1.defibit.io").split(",")
]
USDT_BEP20_CONTRACT = os.getenv("USDT_BEP20_CONTRACT", "0x55d398326f99059fF775485246999027B3197955")
USDT_BEP20_DECIMALS = 18
BEP20_GAS_REQUIRED = 0.00003

# POLYGON RPC
POLYGON_RPC = os.getenv("POLYGON_RPC", "https://polygon.llamarpc.com")
POLYGON_RPC_URLS = [
    url.strip() for url in os.getenv("POLYGON_RPC_URLS", "https://polygon.llamarpc.com,https://1rpc.io/matic,https://rpc.ankr.com/polygon,https://polygon-rpc.com").split(",")
]
USDT_POLYGON_CONTRACT = os.getenv("USDT_POLYGON_CONTRACT", "0xc2132D05D31c914a87C6611C10748AEb04B58e8F")
USDT_POLYGON_DECIMALS = 6
POLYGON_GAS_REQUIRED = 0.7  # Increased from 0.1 due to Polygon congestion

# SOLANA RPC
SOLANA_RPC_URLS = [
    url.strip() for url in os.getenv("SOLANA_RPC_URLS", "https://solana-rpc.publicnode.com").split(",")
]

# Chains Mapping
CHAINS = {
    "usdt_bep20": {
        "rpc": BSC_RPC,
        "chain_id": 56,
        "symbol": "BNB",
        "usdt": USDT_BEP20_CONTRACT,
        "decimals": USDT_BEP20_DECIMALS,
        "solana": "So11111111111111111111111111111111111111112"
    },
    "usdt_polygon": {
        "rpc": POLYGON_RPC,
        "chain_id": 137,
        "symbol": "MATIC",
        "usdt": USDT_POLYGON_CONTRACT,
        "decimals": USDT_POLYGON_DECIMALS
    }
}

# ABIs
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

# Fee and Gas Config
FEE_ADDRESSES = {
    'ltc': os.getenv('FEE_ADDRESS_LTC'),
    'usdt_bep20': os.getenv('FEE_ADDRESS_BSC'),
    'usdt_polygon': os.getenv('FEE_ADDRESS_POLYGON'),
    'solana': os.getenv('FEE_ADDRESS_SOL'),
    'ethereum': os.getenv('FEE_ADDRESS_ETH')
}

# Dust Sweep Address (Fallback to fee addresses if not set)
DUST_SWEEP_ADDRESS = os.getenv('DUST_SWEEP_ADDRESS')
DUST_SWEEP_ADDRESS_BSC = os.getenv('DUST_SWEEP_ADDRESS_BSC')

GAS_SOURCE_PRIVATE_KEY = os.getenv('GAS_SOURCE_PRIVATE_KEY')
GAS_SOURCE_PRIVATE_KEY_BSC = os.getenv('GAS_SOURCE_PRIVATE_KEY_BSC')

# Voice Channel Stats (Set to your VC ID, or None to disable)
VC_STATS_CHANNEL_ID = os.getenv('VC_STATS_CHANNEL_ID', '1456697637821616384')

# Client Role (Assigned to users on deal completion)
CLIENT_ROLE_ID = int(os.getenv('CLIENT_ROLE_ID', '0'))

# Fee Configuration
FEES_ENABLED = os.getenv('FEES_ENABLED', 'false').lower() == 'true'
FEES_PERCENTAGE = float(os.getenv('FEES_PERCENTAGE', '0'))

# Per-Crypto Fee Overrides (Falls back to FEES_PERCENTAGE if not set)
CRYPTO_FEES = {
    'ltc': float(os.getenv('FEE_PERCENT_LTC', FEES_PERCENTAGE)),
    'eth': float(os.getenv('FEE_PERCENT_ETH', FEES_PERCENTAGE)),
    'btc': float(os.getenv('FEE_PERCENT_BTC', FEES_PERCENTAGE)),
    'sol': float(os.getenv('FEE_PERCENT_SOL', FEES_PERCENTAGE)),
    'solana': float(os.getenv('FEE_PERCENT_SOL', FEES_PERCENTAGE)),
    'usdt_bep20': float(os.getenv('FEE_PERCENT_BSC', FEES_PERCENTAGE)),
    'usdt_polygon': float(os.getenv('FEE_PERCENT_POLYGON', FEES_PERCENTAGE)),
}

# Assets
VERIFIED_ICON_URL = os.getenv("VERIFIED_ICON_URL", "https://cdn.discordapp.com/emojis/1321450257917251706.png?v=1")
