#!/usr/bin/env python3
"""
Dynamic USDT Sweep Script for Polygon.
Identifies all wallets in data.json with USDT balances,
auto-funds them with MATIC if needed, and sweeps USDT to destination.
"""

import json
import time
import sys
import argparse
from web3 import Web3
from eth_account import Account

# Configuration
DESTINATION = "0x3e3917d098Df6113156BEFeaa1298DAd39F94f03"
DATA_FILE = "/home/k/rainyday-bot/data.json"
POLYGON_RPC = "https://polygon-rpc.com"
# Read from secret if possible, or use hardcoded if known safe
GAS_SOURCE_KEY = "0f92243b912a1c853bfe01e68a8b454e5b75dd0337a652ecbb04f5ac17d69732"
GAS_AMOUNT = 0.05  # MATIC to fund for safety (gas is cheap but let's be sure)

# USDT Contract
USDT_POLYGON = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
USDT_DECIMALS = 6

USDT_ABI = [
    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"recipient","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}
]

def load_deals():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data.json: {e}")
        return {}

def fund_gas(w3, gas_source_key, target_address, amount):
    """Send MATIC to target address for gas."""
    try:
        account = Account.from_key(gas_source_key)
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
        print(f"  ❌ Gas funding error: {e}")
        return None

def sweep_usdt(w3, private_key, destination):
    """Sweep all USDT from wallet to destination."""
    try:
        account = Account.from_key(private_key)
        address = account.address
        
        # Get USDT balance
        contract = w3.eth.contract(address=w3.to_checksum_address(USDT_POLYGON), abi=USDT_ABI)
        usdt_raw = contract.functions.balanceOf(w3.to_checksum_address(address)).call()
        usdt = usdt_raw / (10 ** USDT_DECIMALS)
        
        if usdt < 0.0001:
            return None, 0, "No USDT balance"
        
        # Build transfer
        gas_price = w3.eth.gas_price
        nonce = w3.eth.get_transaction_count(address)
        
        # Check MATIC balance first
        matic_bal = w3.eth.get_balance(address)
        if matic_bal < w3.to_wei(0.01, 'ether'):
             return None, usdt, "Insufficient MATIC for gas"

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
    parser = argparse.ArgumentParser(description="Sweep USDT from Polygon wallets")
    parser.add_argument("--dry-run", action="store_true", help="Only check balances and planned actions")
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"DYNAMIC USDT SWEEP - Polygon")
    print(f"Destination: {DESTINATION}")
    print(f"Dry Run: {args.dry_run}")
    print(f"{'='*70}\n")
    
    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    if not w3.is_connected():
        print("[ERROR] Failed to connect to Polygon RPC")
        return
    
    # Check gas source balance
    try:
        gas_account = Account.from_key(GAS_SOURCE_KEY)
        gas_balance = float(w3.from_wei(w3.eth.get_balance(gas_account.address), 'ether'))
        print(f"[GAS SOURCE] {gas_account.address}")
        print(f"[GAS SOURCE] Balance: {gas_balance:.6f} MATIC\n")
    except Exception as e:
        print(f"[ERROR] Could not check gas source: {e}")
        return

    deals = load_deals()
    print(f"[INFO] Loaded {len(deals)} deals from data.json\n")
    
    wallets_to_process = []
    
    # Identify wallets with USDT balances
    contract = w3.eth.contract(address=w3.to_checksum_address(USDT_POLYGON), abi=USDT_ABI)
    
    for deal_id, info in deals.items():
        address = info.get('address')
        private_key = info.get('private_key')
        currency = info.get('currency')
        
        if not address or not private_key or currency != 'usdt_polygon':
            continue
            
        try:
            usdt_raw = contract.functions.balanceOf(w3.to_checksum_address(address)).call()
            usdt = usdt_raw / (10 ** USDT_DECIMALS)
            
            if usdt > 0.0001:
                matic_raw = w3.eth.get_balance(w3.to_checksum_address(address))
                matic = float(w3.from_wei(matic_raw, 'ether'))
                
                wallets_to_process.append({
                    'address': address,
                    'private_key': private_key,
                    'usdt': usdt,
                    'matic': matic,
                    'deal_id': deal_id
                })
                print(f"📍 Found {address[:20]}... | {usdt:10.6f} USDT | {matic:8.6f} MATIC")
        except Exception as e:
            print(f"⚠️ Error checking {address}: {e}")

    print(f"\n[SUMMARY] Found {len(wallets_to_process)} wallets with balance")
    
    if not wallets_to_process:
        print("No funds to sweep.")
        return

    if args.dry_run:
        print("\n[DRY RUN] Exiting without making transactions.")
        return

    # Execute
    total_swept = 0
    success_count = 0
    
    for w in wallets_to_process:
        address = w['address']
        print(f"\nProcessing {address}...")
        
        # Step 1: Fund gas if needed
        if w['matic'] < 0.02:
            print(f"  ⛽ Funding gas ({GAS_AMOUNT} MATIC)...", end=" ")
            fund_tx = fund_gas(w3, GAS_SOURCE_KEY, address, GAS_AMOUNT)
            if fund_tx:
                print(f"✅ {fund_tx}")
                print("  ⏳ Waiting for confirmation...", end=" ")
                time.sleep(10) # 10s wait for Polygon
                print("✅")
            else:
                print("❌ Skipping due to funding failure")
                continue
        else:
            print(f"  ✅ Has sufficient gas ({w['matic']:.6f} MATIC)")

        # Step 2: Sweep USDT
        print(f"  💸 Sweeping USDT...", end=" ")
        tx_hash, amount, status = sweep_usdt(w3, w['private_key'], DESTINATION)
        
        if tx_hash:
            print(f"✅ Sent {amount:.6f} USDT | TX: {tx_hash}")
            total_swept += amount
            success_count += 1
        else:
            print(f"❌ {status}")
            
        time.sleep(2)

    print(f"\n{'='*70}")
    print(f"FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"Wallets swept: {success_count}/{len(wallets_to_process)}")
    print(f"Total USDT recovered: {total_swept:.6f}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
