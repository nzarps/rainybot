import asyncio
import os
import sys
import logging
from web3 import AsyncWeb3, AsyncHTTPProvider, Web3
from eth_account import Account
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("SweepFinal")

# Config
DESTINATION_ADDRESS = "0x3e3917d098Df6113156BEFeaa1298DAd39F94f03"
POLYGON_RPC_URLS = [
    "https://polygon.llamarpc.com",
    "https://1rpc.io/matic",
    "https://rpc.ankr.com/polygon",
    "https://polygon-rpc.com"
]
USDT_POLYGON_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
USDT_DECIMALS = 6
USDT_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
]

# Add database.py and project root to path
sys.path.append(os.getcwd())
try:
    from database import load_all_data
except ImportError:
    logger.error("Could not import database.py. Make sure you are in the bot root.")
    sys.exit(1)

async def get_w3():
    for rpc in POLYGON_RPC_URLS:
        try:
            w3 = AsyncWeb3(AsyncHTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if await w3.is_connected():
                return w3, rpc
        except Exception:
            continue
    return None, None

async def sweep_wallet(wallet_info, destination, w3):
    address = wallet_info.get('address')
    private_key = wallet_info.get('private_key')
    deal_id = wallet_info.get('deal_id', 'Unknown')
    
    if not address or not private_key:
        logger.warning(f"Skipping deal {deal_id}: Missing address or private key.")
        return None
        
    try:
        addr_checksum = Web3.to_checksum_address(address)
        dest_checksum = Web3.to_checksum_address(destination)
        
        # 1. Check Balances
        matic_bal_wei = await w3.eth.get_balance(addr_checksum)
        matic_bal = float(matic_bal_wei / (10**18))
        
        contract = w3.eth.contract(address=Web3.to_checksum_address(USDT_POLYGON_CONTRACT), abi=USDT_ABI)
        usdt_bal_raw = await contract.functions.balanceOf(addr_checksum).call()
        usdt_bal = usdt_bal_raw / (10**USDT_DECIMALS)
        
        if matic_bal < 0.0001 and usdt_bal < 0.0001:
            return None
            
        logger.info(f"Processing {deal_id[:12]} ({address}): {matic_bal:.6f} MATIC, {usdt_bal:.6f} USDT")
        
        # 2. Sweep USDT first (requires gas)
        if usdt_bal > 0.001:
            gas_price = await w3.eth.gas_price
            nonce = await w3.eth.get_transaction_count(addr_checksum)
            
            # Use conservative multipliers for USDT sweep
            gas_estimate = 65000 
            try:
                gas_estimate = await contract.functions.transfer(dest_checksum, usdt_bal_raw).estimate_gas({'from': addr_checksum})
            except Exception as e:
                pass
                
            gas_cost_wei = int(gas_estimate * 1.1 * gas_price * 1.1)
            
            if matic_bal_wei < gas_cost_wei:
                logger.warning(f"  [USDT] Not enough gas for {address} (Need {gas_cost_wei/(10**18):.6f} MATIC, have {matic_bal:.6f}). Skipping USDT.")
            else:
                tx = await contract.functions.transfer(dest_checksum, usdt_bal_raw).build_transaction({
                    'chainId': 137,
                    'gas': int(gas_estimate * 1.1),
                    'gasPrice': int(gas_price * 1.1), 
                    'nonce': nonce
                })
                signed = w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = await w3.eth.send_raw_transaction(signed.raw_transaction)
                logger.info(f"  [USDT] Sent! TX: {tx_hash.hex()}")
                # Wait a bit for nonce update
                await asyncio.sleep(3)
        
        # 3. Sweep MATIC
        # Refresh balance after USDT tx
        matic_bal_wei = await w3.eth.get_balance(addr_checksum)
        gas_price = await w3.eth.gas_price
        gas_limit = 21000
        # Subtract gas cost AND a tiny extra 0.001 MATIC buffer for safety
        gas_cost_wei = int(gas_limit * gas_price * 1.05)
        
        amount_to_send = matic_bal_wei - gas_cost_wei
        if amount_to_send > 10**15: # > 0.001 MATIC
            nonce = await w3.eth.get_transaction_count(addr_checksum)
            tx = {
                'nonce': nonce,
                'to': dest_checksum,
                'value': amount_to_send,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = await w3.eth.send_raw_transaction(signed.raw_transaction)
            logger.info(f"  [MATIC] Sent! TX: {tx_hash.hex()}")
            
        return True
    except Exception as e:
        logger.error(f"  [ERR] Failed {address}: {e}")
        return False

async def main():
    logger.info("Loading deals from database...")
    data = load_all_data()
    
    wallets = []
    for deal_id, deal in data.items():
        if deal.get('currency') == 'usdt_polygon':
            wallets.append({
                'deal_id': deal_id,
                'address': deal.get('address'),
                'private_key': deal.get('private_key')
            })
            
    if not wallets:
        logger.info("No Polygon deals found.")
        return
        
    logger.info(f"Found {len(wallets)} Polygon wallets. Scanning balances...")
    
    # We will try each RPC in a loop if needed
    results = 0
    for wallet in wallets:
        success = False
        for rpc_url in POLYGON_RPC_URLS:
            try:
                w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
                if not await w3.is_connected():
                    continue
                
                if await sweep_wallet(wallet, DESTINATION_ADDRESS, w3):
                    results += 1
                    success = True
                    break # Successful for this wallet
                else:
                    # sweep_wallet returns None if no funds, which is 'success' in a sense but results don't increment
                    # If it returns False, it means an error occurred.
                    success = True # Wallet scanned, just no funds
                    break
            except Exception as e:
                if "rate limit" in str(e).lower() or "429" in str(e):
                    logger.warning(f"Rate limited on {rpc_url}, trying next...")
                    continue
                logger.error(f"RPC {rpc_url} failed: {e}")
                continue
        
        # Cooldown between wallets to avoid triggering anti-spam
        await asyncio.sleep(3)
            
    logger.info(f"\nTask Finished. Swept {results} wallets with funds.")

if __name__ == "__main__":
    asyncio.run(main())
