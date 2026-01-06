"""Retry MATIC sweep for the failed wallet."""
import asyncio
import json
from web3 import Web3

POLYGON_RPC_URLS = ['https://polygon-rpc.com', 'https://rpc-mainnet.matic.quiknode.pro']
DESTINATION = '0x3e3917d098Df6113156BEFeaa1298DAd39F94f03'

def load_deals():
    with open("data.json", "r") as f:
        return json.load(f)

async def sweep():
    deals = load_deals()
    deal = deals.get('vvsik05zeahoh36c3m214gs3a6unwo7nxl2wf2kntx7byhtgznx8bfnbvbs5t879', {})
    
    if not deal:
        print("Deal not found")
        return
    
    address = deal.get('address')
    private_key = deal.get('private_key')
    
    print(f"Retrying MATIC sweep for: {address}")
    
    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URLS[0]))
    if not w3.is_connected():
        print('RPC not connected')
        return
    
    balance = w3.eth.get_balance(address)
    print(f'Balance: {balance / 10**18:.6f} MATIC')
    
    gas_price = w3.eth.gas_price
    gas_limit = 21000
    gas_cost = gas_limit * gas_price
    amount = balance - gas_cost
    
    if amount <= 0:
        print('Not enough to sweep (gas cost exceeds balance)')
        return
    
    nonce = w3.eth.get_transaction_count(address)
    print(f'Using nonce: {nonce}')
    
    tx = {
        'nonce': nonce,
        'to': DESTINATION,
        'value': amount,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'chainId': 137
    }
    
    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f'TX: {tx_hash.hex()}')

if __name__ == "__main__":
    asyncio.run(sweep())
