"""
Sweep all remaining funds from deal wallets to the user's address.
"""
import asyncio
import json
from web3 import Web3
from eth_account import Account

# Config
POLYGON_RPC_URLS = ["https://polygon-rpc.com", "https://rpc-mainnet.matic.quiknode.pro"]
USDT_POLYGON_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"

# Destination address (from config FEE_ADDRESS_POLYGON)
DESTINATION_ADDRESS = "0x3e3917d098Df6113156BEFeaa1298DAd39F94f03"

def load_deals():
    with open("data.json", "r") as f:
        return json.load(f)

async def get_balances(address):
    """Get USDT and MATIC balances for an address."""
    for rpc in POLYGON_RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            if not w3.is_connected():
                continue
            
            # MATIC balance
            matic_bal = w3.eth.get_balance(address) / 10**18
            
            # USDT balance
            usdt_abi = [
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
            ]
            contract = w3.eth.contract(address=Web3.to_checksum_address(USDT_POLYGON_CONTRACT), abi=usdt_abi)
            usdt_bal = contract.functions.balanceOf(Web3.to_checksum_address(address)).call() / 10**6
            
            return matic_bal, usdt_bal
        except Exception as e:
            print(f"Error checking {address}: {e}")
            continue
    return 0, 0

async def sweep_matic(private_key, from_address, to_address, w3):
    """Sweep remaining MATIC (leave enough for gas if sweeping USDT first)."""
    try:
        balance = w3.eth.get_balance(from_address)
        gas_price = w3.eth.gas_price
        gas_limit = 21000
        gas_cost = gas_limit * gas_price
        
        amount_to_send = balance - gas_cost
        if amount_to_send <= 0:
            return None
        
        nonce = w3.eth.get_transaction_count(from_address)
        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': amount_to_send,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'chainId': 137
        }
        
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()
    except Exception as e:
        print(f"MATIC sweep error: {e}")
        return None

async def sweep_usdt(private_key, from_address, to_address, w3):
    """Sweep USDT balance."""
    try:
        usdt_abi = [
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
        ]
        contract = w3.eth.contract(address=Web3.to_checksum_address(USDT_POLYGON_CONTRACT), abi=usdt_abi)
        
        balance = contract.functions.balanceOf(Web3.to_checksum_address(from_address)).call()
        if balance <= 0:
            return None
        
        nonce = w3.eth.get_transaction_count(from_address)
        gas_estimate = contract.functions.transfer(Web3.to_checksum_address(to_address), balance).estimate_gas({'from': from_address})
        
        tx = contract.functions.transfer(Web3.to_checksum_address(to_address), balance).build_transaction({
            'chainId': 137,
            'gas': int(gas_estimate * 1.2),
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce
        })
        
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()
    except Exception as e:
        print(f"USDT sweep error: {e}")
        return None

async def main():
    deals = load_deals()
    
    print(f"Checking {len(deals)} deals for remaining funds...")
    print(f"Destination: {DESTINATION_ADDRESS}")
    print("-" * 60)
    
    wallets_with_funds = []
    
    for deal_id, deal in deals.items():
        address = deal.get('address')
        private_key = deal.get('private_key')
        currency = deal.get('currency', 'ltc')
        
        if not address or not private_key:
            continue
        
        # Only check Polygon wallets for now
        if currency != 'usdt_polygon':
            continue
        
        matic_bal, usdt_bal = await get_balances(address)
        
        if matic_bal > 0.001 or usdt_bal > 0.001:
            wallets_with_funds.append({
                'deal_id': deal_id,
                'address': address,
                'private_key': private_key,
                'matic': matic_bal,
                'usdt': usdt_bal
            })
            print(f"Deal {deal_id[:16]}...: {matic_bal:.6f} MATIC, {usdt_bal:.6f} USDT")
    
    print("-" * 60)
    print(f"Found {len(wallets_with_funds)} wallets with funds")
    
    if not wallets_with_funds:
        print("No funds to sweep!")
        return
    
    # Calculate totals
    total_matic = sum(w['matic'] for w in wallets_with_funds)
    total_usdt = sum(w['usdt'] for w in wallets_with_funds)
    print(f"Total MATIC: {total_matic:.6f}")
    print(f"Total USDT: {total_usdt:.6f}")
    
    # Confirm before sweeping
    confirm = input("\nSweep all funds? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborted.")
        return
    
    # Connect to RPC
    w3 = None
    for rpc in POLYGON_RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            if w3.is_connected():
                break
        except:
            continue
    
    if not w3:
        print("Could not connect to RPC")
        return
    
    # Sweep each wallet
    for wallet in wallets_with_funds:
        print(f"\nSweeping {wallet['deal_id'][:16]}...")
        
        # Sweep USDT first (needs gas)
        if wallet['usdt'] > 0.001:
            tx = await sweep_usdt(wallet['private_key'], wallet['address'], DESTINATION_ADDRESS, w3)
            if tx:
                print(f"  USDT TX: {tx}")
                await asyncio.sleep(5)  # Wait for USDT tx to process
        
        # Then sweep remaining MATIC
        if wallet['matic'] > 0.01:
            tx = await sweep_matic(wallet['private_key'], wallet['address'], DESTINATION_ADDRESS, w3)
            if tx:
                print(f"  MATIC TX: {tx}")
    
    print("\nSweep complete!")

if __name__ == "__main__":
    asyncio.run(main())
