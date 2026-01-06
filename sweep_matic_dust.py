#!/usr/bin/env python3
"""Sweep leftover MATIC dust from specific wallets."""

import json
import time
from web3 import Web3

DESTINATION = "0x3e3917d098Df6113156BEFeaa1298DAd39F94f03"
DATA_FILE = "/home/k/rainyday-bot/data.json"
POLYGON_RPC = "https://polygon-rpc.com"

WALLETS = [
    ("0x33405eaF46cb1111146F40827deF10b6d553A82E", "bo63fhmtebuip9u5q62r"),
    ("0x1A8FDf2CC75366002576D67b3E3C07356974e985", "3ceys44j9a82p0cp3h6e"),
    ("0x4b2243F8D3D5448Ae58Ac3172af34951E12006fb", "tsok98za2cs2zgmgauzy"),
]

def load_deals():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def get_private_key(deals, deal_id):
    for did, info in deals.items():
        if did.startswith(deal_id):
            return info.get('private_key')
    return None

def sweep_matic(w3, private_key, destination):
    try:
        account = w3.eth.account.from_key(private_key)
        address = account.address
        
        balance = w3.eth.get_balance(address)
        gas_price = w3.eth.gas_price
        gas_cost = 21000 * gas_price
        send_amount = balance - gas_cost
        
        if send_amount <= 0:
            return None, 0, "Insufficient"
        
        tx = {
            'to': w3.to_checksum_address(destination),
            'value': send_amount,
            'gas': 21000,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(address),
            'chainId': 137
        }
        
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        matic = float(w3.from_wei(send_amount, 'ether'))
        return w3.to_hex(tx_hash), matic, "Success"
    except Exception as e:
        return None, 0, str(e)

def main():
    print(f"\nSweeping MATIC dust to {DESTINATION}\n")
    
    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    deals = load_deals()
    total = 0
    
    for address, deal_id in WALLETS:
        pk = get_private_key(deals, deal_id)
        if not pk:
            print(f"[{address[:16]}...] No key found")
            continue
        
        tx, amount, status = sweep_matic(w3, pk, DESTINATION)
        if tx:
            print(f"[{address[:16]}...] ✅ {amount:.6f} MATIC - TX: {tx}")
            total += amount
        else:
            print(f"[{address[:16]}...] ❌ {status}")
        time.sleep(1)
    
    print(f"\nTotal MATIC swept: {total:.6f}\n")

if __name__ == "__main__":
    main()
