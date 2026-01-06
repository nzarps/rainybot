#!/usr/bin/env python3
"""Debug script to check USDT balance on both chains for a specific address."""

from web3 import Web3
import sys

# --- Configuration from config.py ---
USDT_ABI = [{"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]

BEP20_RPC_URLS = [
    "https://bsc-dataseed.binance.org",
    "https://bsc-dataseed1.ninicoin.io",
]
POLYGON_RPC_URLS = [
    "https://polygon-rpc.com",
    "https://rpc-mainnet.matic.quiknode.pro",
]

USDT_BEP20_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
USDT_POLYGON_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"

USDT_BEP20_DECIMALS = 18
USDT_POLYGON_DECIMALS = 6

# Address from screenshot
ADDRESS = "0x63239A2A99594cB723Dc94500CC6FD3a288fdD46"

def check_balance(rpc, contract_addr, wallet_addr, decimals, chain_name):
    try:
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
        if not w3.is_connected():
            print(f"  {chain_name}: Failed to connect to {rpc}")
            return None
        
        contract = w3.eth.contract(address=w3.to_checksum_address(contract_addr), abi=USDT_ABI)
        balance_raw = contract.functions.balanceOf(w3.to_checksum_address(wallet_addr)).call()
        balance = balance_raw / (10 ** decimals)
        print(f"  {chain_name} via {rpc}: {balance} USDT")
        return balance
    except Exception as e:
        print(f"  {chain_name} via {rpc}: Error - {e}")
        return None

def check_native_balance(rpc, wallet_addr, chain_name, symbol):
    try:
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
        if not w3.is_connected():
            return None
        balance = w3.eth.get_balance(w3.to_checksum_address(wallet_addr))
        balance_eth = w3.from_wei(balance, 'ether')
        print(f"  {chain_name} Native ({symbol}): {balance_eth}")
        return float(balance_eth)
    except Exception as e:
        print(f"  {chain_name} Native: Error - {e}")
        return None

if __name__ == "__main__":
    addr = sys.argv[1] if len(sys.argv) > 1 else ADDRESS
    print(f"\n=== Checking balances for: {addr} ===\n")
    
    print("--- BEP20 (BSC) ---")
    for rpc in BEP20_RPC_URLS:
        check_balance(rpc, USDT_BEP20_CONTRACT, addr, USDT_BEP20_DECIMALS, "BEP20")
    check_native_balance(BEP20_RPC_URLS[0], addr, "BEP20", "BNB")
    
    print("\n--- POLYGON ---")
    for rpc in POLYGON_RPC_URLS:
        check_balance(rpc, USDT_POLYGON_CONTRACT, addr, USDT_POLYGON_DECIMALS, "Polygon")
    check_native_balance(POLYGON_RPC_URLS[0], addr, "Polygon", "MATIC")
    
    print()
