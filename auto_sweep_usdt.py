#!/usr/bin/env python3
"""
Auto-fund wallets with MATIC and sweep USDT to destination.
Uses GAS_SOURCE_PRIVATE_KEY to fund gas, then sweeps USDT.
"""

import json
import time
from web3 import Web3

# Configuration
DESTINATION = "0x3e3917d098Df6113156BEFeaa1298DAd39F94f03"
DATA_FILE = "/home/k/rainyday-bot/data.json"
POLYGON_RPC = "https://polygon-rpc.com"
GAS_SOURCE_KEY = "0f92243b912a1c853bfe01e68a8b454e5b75dd0337a652ecbb04f5ac17d69732"
GAS_AMOUNT = 0.02  # MATIC to send for gas

# USDT Contract
USDT_POLYGON = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
USDT_DECIMALS = 6

USDT_ABI = [
    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"recipient","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}
]

# Wallets with USDT balance
WALLETS_TO_SWEEP = [
    ("0x33405eaF46cb1111146F40827deF10b6d553A82E", "bo63fhmtebuip9u5q62r"),
    ("0x1A8FDf2CC75366002576D67b3E3C07356974e985", "3ceys44j9a82p0cp3h6e"),
    ("0x4b2243F8D3D5448Ae58Ac3172af34951E12006fb", "tsok98za2cs2zgmgauzy"),
]

def load_deals():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def get_private_key(deals, deal_id):
    for did, info in deals.items():
        if did.startswith(deal_id) or deal_id.startswith(did[:20]):
            return info.get('private_key')
    return None

def fund_gas(w3, gas_source_key, target_address, amount):
    """Send MATIC to target address for gas."""
    try:
        account = w3.eth.account.from_key(gas_source_key)
        
        gas_price = w3.eth.gas_price
        nonce = w3.eth.get_transaction_count(account.address)
        
        tx = {
            'to': w3.to_checksum_address(target_address),
            'value': w3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': 137
        }
        
        signed = w3.eth.account.sign_transaction(tx, gas_source_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return w3.to_hex(tx_hash)
    except Exception as e:
        return None

def sweep_usdt(w3, private_key, destination):
    """Sweep all USDT from wallet to destination."""
    try:
        account = w3.eth.account.from_key(private_key)
        address = account.address
        
        # Get USDT balance
        contract = w3.eth.contract(address=w3.to_checksum_address(USDT_POLYGON), abi=USDT_ABI)
        usdt_raw = contract.functions.balanceOf(w3.to_checksum_address(address)).call()
        usdt = usdt_raw / (10 ** USDT_DECIMALS)
        
        if usdt < 0.001:
            return None, 0, "No USDT balance"
        
        # Build transfer
        gas_price = w3.eth.gas_price
        nonce = w3.eth.get_transaction_count(address)
        
        tx = contract.functions.transfer(
            w3.to_checksum_address(destination),
            usdt_raw
        ).build_transaction({
            'from': address,
            'gas': 65000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': 137
        })
        
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return w3.to_hex(tx_hash), usdt, "Success"
        
    except Exception as e:
        return None, 0, str(e)

def main():
    print(f"\n{'='*70}")
    print(f"AUTO-FUND & SWEEP USDT - Polygon")
    print(f"Destination: {DESTINATION}")
    print(f"{'='*70}\n")
    
    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    if not w3.is_connected():
        print("[ERROR] Failed to connect to Polygon RPC")
        return
    
    # Check gas source balance
    gas_account = w3.eth.account.from_key(GAS_SOURCE_KEY)
    gas_balance = float(w3.from_wei(w3.eth.get_balance(gas_account.address), 'ether'))
    print(f"[GAS SOURCE] {gas_account.address}")
    print(f"[GAS SOURCE] Balance: {gas_balance:.6f} MATIC\n")
    
    if gas_balance < GAS_AMOUNT * len(WALLETS_TO_SWEEP):
        print(f"[ERROR] Insufficient MATIC in gas source. Need {GAS_AMOUNT * len(WALLETS_TO_SWEEP):.4f}")
        return
    
    deals = load_deals()
    
    total_swept = 0
    success_count = 0
    
    for address, deal_id in WALLETS_TO_SWEEP:
        private_key = get_private_key(deals, deal_id)
        
        if not private_key:
            print(f"[{address[:16]}...] ❌ Private key not found")
            continue
        
        # Step 1: Fund gas
        print(f"[{address[:16]}...] Funding {GAS_AMOUNT} MATIC...", end=" ")
        fund_tx = fund_gas(w3, GAS_SOURCE_KEY, address, GAS_AMOUNT)
        if fund_tx:
            print(f"✅ TX: {fund_tx}")
        else:
            print("❌ Failed to fund")
            continue
        
        # Wait for funding to confirm
        print(f"[{address[:16]}...] Waiting for confirmation...", end=" ")
        time.sleep(5)
        print("✅")
        
        # Step 2: Sweep USDT
        print(f"[{address[:16]}...] Sweeping USDT...", end=" ")
        tx_hash, amount, status = sweep_usdt(w3, private_key, DESTINATION)
        
        if tx_hash:
            print(f"✅ Swept {amount:.6f} USDT - TX: {tx_hash}")
            total_swept += amount
            success_count += 1
        else:
            print(f"❌ {status}")
        
        time.sleep(2)
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Wallets swept: {success_count}")
    print(f"Total USDT recovered: {total_swept:.6f}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
