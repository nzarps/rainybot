#!/usr/bin/env python3
"""
Check all deal wallets for any remaining balances (any crypto).
"""

import json
from web3 import Web3

# Configuration
DATA_FILE = "/home/k/rainyday-bot/data.json"

# RPCs
POLYGON_RPC = "https://polygon-rpc.com"
BSC_RPC = "https://bsc-dataseed.binance.org"
ETH_RPC = "https://eth.llamarpc.com"

# USDT Contracts
USDT_POLYGON = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
USDT_BEP20 = "0x55d398326f99059fF775485246999027B3197955"

USDT_ABI = [{"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}]

def load_deals():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def check_polygon_balance(address):
    """Check MATIC and USDT on Polygon."""
    try:
        w3 = Web3(Web3.HTTPProvider(POLYGON_RPC, request_kwargs={"timeout": 10}))
        if not w3.is_connected():
            return None, None
        
        # MATIC
        matic = float(w3.from_wei(w3.eth.get_balance(w3.to_checksum_address(address)), 'ether'))
        
        # USDT
        contract = w3.eth.contract(address=w3.to_checksum_address(USDT_POLYGON), abi=USDT_ABI)
        usdt_raw = contract.functions.balanceOf(w3.to_checksum_address(address)).call()
        usdt = usdt_raw / 1e6  # 6 decimals
        
        return matic, usdt
    except Exception as e:
        return None, None

def check_bsc_balance(address):
    """Check BNB and USDT on BSC."""
    try:
        w3 = Web3(Web3.HTTPProvider(BSC_RPC, request_kwargs={"timeout": 10}))
        if not w3.is_connected():
            return None, None
        
        # BNB
        bnb = float(w3.from_wei(w3.eth.get_balance(w3.to_checksum_address(address)), 'ether'))
        
        # USDT
        contract = w3.eth.contract(address=w3.to_checksum_address(USDT_BEP20), abi=USDT_ABI)
        usdt_raw = contract.functions.balanceOf(w3.to_checksum_address(address)).call()
        usdt = usdt_raw / 1e18  # 18 decimals
        
        return bnb, usdt
    except Exception as e:
        return None, None

def check_eth_balance(address):
    """Check ETH balance."""
    try:
        w3 = Web3(Web3.HTTPProvider(ETH_RPC, request_kwargs={"timeout": 10}))
        if not w3.is_connected():
            return None
        
        eth = float(w3.from_wei(w3.eth.get_balance(w3.to_checksum_address(address)), 'ether'))
        return eth
    except:
        return None

def main():
    print(f"\n{'='*70}")
    print(f"BALANCE CHECKER - All Deal Wallets")
    print(f"{'='*70}\n")
    
    deals = load_deals()
    print(f"[INFO] Found {len(deals)} deals in database\n")
    
    wallets_with_balance = []
    
    for deal_id, deal_info in deals.items():
        address = deal_info.get('address')
        currency = deal_info.get('currency', 'unknown')
        
        if not address:
            continue
        
        balances = {}
        
        if currency == 'usdt_polygon':
            matic, usdt = check_polygon_balance(address)
            if matic and matic > 0.0001:
                balances['MATIC'] = matic
            if usdt and usdt > 0.0001:
                balances['USDT_Polygon'] = usdt
                
        elif currency == 'usdt_bep20':
            bnb, usdt = check_bsc_balance(address)
            if bnb and bnb > 0.00001:
                balances['BNB'] = bnb
            if usdt and usdt > 0.0001:
                balances['USDT_BEP20'] = usdt
                
        elif currency == 'ethereum':
            eth = check_eth_balance(address)
            if eth and eth > 0.00001:
                balances['ETH'] = eth
        
        if balances:
            wallets_with_balance.append({
                'deal_id': deal_id[:20],
                'address': address,
                'currency': currency,
                'balances': balances
            })
            print(f"💰 {address[:20]}... ({currency})")
            for coin, amount in balances.items():
                print(f"    {coin}: {amount:.8f}")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY: {len(wallets_with_balance)} wallets with balance")
    print(f"{'='*70}\n")
    
    if wallets_with_balance:
        for w in wallets_with_balance:
            print(f"Address: {w['address']}")
            print(f"Deal: {w['deal_id']}")
            for coin, amount in w['balances'].items():
                print(f"  {coin}: {amount:.8f}")
            print()

if __name__ == "__main__":
    main()
