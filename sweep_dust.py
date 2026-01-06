#!/usr/bin/env python3
"""
Sweep all leftover MATIC dust from deal wallets to a single address.
Reads private keys from data.json and sends remaining balances.
"""

import json
import time
from web3 import Web3

# Configuration
DESTINATION = "0x3e3917d098Df6113156BEFeaa1298DAd39F94f03"
DATA_FILE = "/home/k/rainyday-bot/data.json"
POLYGON_RPC = "https://polygon-rpc.com"
MIN_BALANCE = 0.001  # Minimum MATIC to bother sweeping

def load_deals():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def sweep_wallet(w3, private_key, destination):
    """Sweep all MATIC from a wallet to destination."""
    try:
        account = w3.eth.account.from_key(private_key)
        address = account.address
        
        balance = w3.eth.get_balance(address)
        balance_matic = float(w3.from_wei(balance, 'ether'))
        
        if balance_matic < MIN_BALANCE:
            return None, balance_matic, "Below threshold"
        
        # Calculate gas cost
        gas_price = w3.eth.gas_price
        gas_limit = 21000
        gas_cost = gas_limit * gas_price
        
        send_amount = balance - gas_cost
        
        if send_amount <= 0:
            return None, balance_matic, "Insufficient for gas"
        
        send_matic = float(w3.from_wei(send_amount, 'ether'))
        
        tx = {
            'to': w3.to_checksum_address(destination),
            'value': send_amount,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(address),
            'chainId': 137  # Polygon
        }
        
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return w3.to_hex(tx_hash), send_matic, "Success"
        
    except Exception as e:
        return None, 0, str(e)

def main():
    print(f"\n{'='*60}")
    print(f"DUST SWEEPER - Polygon MATIC")
    print(f"Destination: {DESTINATION}")
    print(f"{'='*60}\n")
    
    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    if not w3.is_connected():
        print("[ERROR] Failed to connect to Polygon RPC")
        return
    
    deals = load_deals()
    print(f"[INFO] Found {len(deals)} deals in database\n")
    
    total_swept = 0
    success_count = 0
    
    for deal_id, deal_info in deals.items():
        private_key = deal_info.get('private_key')
        address = deal_info.get('address')
        currency = deal_info.get('currency', 'unknown')
        
        # Only sweep Polygon deals (they have MATIC dust)
        if currency != 'usdt_polygon':
            continue
            
        if not private_key or not address:
            continue
        
        print(f"[{deal_id[:16]}...] Checking {address[:16]}...", end=" ")
        
        tx_hash, amount, status = sweep_wallet(w3, private_key, DESTINATION)
        
        if tx_hash:
            print(f"✅ Swept {amount:.6f} MATIC - TX: {tx_hash}")
            total_swept += amount
            success_count += 1
            time.sleep(1)  # Rate limit
        else:
            print(f"⏭️  {status}")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Wallets swept: {success_count}")
    print(f"Total MATIC recovered: {total_swept:.6f}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
