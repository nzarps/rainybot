#!/usr/bin/env python3
"""
Sweep USDT (Polygon) from deal wallets to destination address.
Requires MATIC for gas - will check and warn if insufficient.
"""

import json
import time
from web3 import Web3

# Configuration
DESTINATION = "0x3e3917d098Df6113156BEFeaa1298DAd39F94f03"
DATA_FILE = "/home/k/rainyday-bot/data.json"
POLYGON_RPC = "https://polygon-rpc.com"

# USDT Contract
USDT_POLYGON = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
USDT_DECIMALS = 6

USDT_ABI = [
    {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"recipient","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}
]

# Wallets with balance (from previous check)
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

def sweep_usdt(w3, private_key, destination):
    """Sweep all USDT from wallet to destination."""
    try:
        account = w3.eth.account.from_key(private_key)
        address = account.address
        
        # Check MATIC for gas
        matic_balance = w3.eth.get_balance(address)
        matic = float(w3.from_wei(matic_balance, 'ether'))
        
        if matic < 0.01:
            return None, 0, f"Need MATIC for gas (have {matic:.6f})"
        
        # Get USDT balance
        contract = w3.eth.contract(address=w3.to_checksum_address(USDT_POLYGON), abi=USDT_ABI)
        usdt_raw = contract.functions.balanceOf(w3.to_checksum_address(address)).call()
        usdt = usdt_raw / (10 ** USDT_DECIMALS)
        
        if usdt < 0.001:
            return None, 0, "No USDT balance"
        
        # Build transfer transaction
        gas_price = w3.eth.gas_price
        nonce = w3.eth.get_transaction_count(address)
        
        tx = contract.functions.transfer(
            w3.to_checksum_address(destination),
            usdt_raw
        ).build_transaction({
            'from': address,
            'gas': 65000,  # USDT transfer typically ~60k
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
    print(f"USDT SWEEPER - Polygon")
    print(f"Destination: {DESTINATION}")
    print(f"{'='*70}\n")
    
    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    if not w3.is_connected():
        print("[ERROR] Failed to connect to Polygon RPC")
        return
    
    deals = load_deals()
    
    total_swept = 0
    success_count = 0
    
    for address, deal_id in WALLETS_TO_SWEEP:
        private_key = get_private_key(deals, deal_id)
        
        if not private_key:
            print(f"[{address[:16]}...] ❌ Private key not found for {deal_id}")
            continue
        
        print(f"[{address[:16]}...] Sweeping...", end=" ")
        
        tx_hash, amount, status = sweep_usdt(w3, private_key, DESTINATION)
        
        if tx_hash:
            print(f"✅ Swept {amount:.6f} USDT - TX: {tx_hash}")
            total_swept += amount
            success_count += 1
            time.sleep(2)  # Rate limit
        else:
            print(f"❌ {status}")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Wallets swept: {success_count}")
    print(f"Total USDT recovered: {total_swept:.6f}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
