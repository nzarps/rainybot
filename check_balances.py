
import asyncio
from web3 import Web3
import os

# Configs from .env/config
GAS_SOURCE_PRIVATE_KEY = "0f92243b912a1c853bfe01e68a8b454e5b75dd0337a652ecbb04f5ac17d69732"
DEAL_WALLET_ADDRESS = "0xd922e52d27dAd701b2f3BF565228fB9A66cD45A9"
USDT_POLYGON_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
POLYGON_RPC_URLS = ["https://polygon-rpc.com", "https://rpc-mainnet.matic.quiknode.pro"]

async def check_balances():
    w3 = None
    for rpc in POLYGON_RPC_URLS:
        try:
            temp_w3 = Web3(Web3.HTTPProvider(rpc))
            if temp_w3.is_connected():
                w3 = temp_w3
                print(f"Connected to RPC: {rpc}")
                break
        except Exception as e:
            print(f"Failed to connect to {rpc}: {e}")
    
    if not w3:
        print("Could not connect to any Polygon RPC")
        return

    # Gas Source Info
    from eth_account import Account
    gas_acc = Account.from_key(GAS_SOURCE_PRIVATE_KEY)
    gas_source_addr = gas_acc.address
    print(f"Gas Source Address: {gas_source_addr}")
    
    matic_balance = w3.eth.get_balance(gas_source_addr) / 10**18
    print(f"Gas Source MATIC Balance: {matic_balance:.6f}")
    
    # Deal Wallet Info
    deal_matic = w3.eth.get_balance(DEAL_WALLET_ADDRESS) / 10**18
    print(f"Deal Wallet MATIC Balance: {deal_matic:.6f}")
    
    # USDT Balance
    usdt_abi = [
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
    ]
    contract = w3.eth.contract(address=Web3.to_checksum_address(USDT_POLYGON_CONTRACT), abi=usdt_abi)
    usdt_bal_raw = contract.functions.balanceOf(Web3.to_checksum_address(DEAL_WALLET_ADDRESS)).call()
    usdt_bal = usdt_bal_raw / 10**6
    print(f"Deal Wallet USDT Balance: {usdt_bal:.6f}")

    # Gas Price and Cost
    gas_price_gwei = w3.eth.gas_price / 10**9
    print(f"Current Gas Price: {gas_price_gwei:.2f} Gwei")
    
    # Estimate cost for 2 ERC20 transfers (approx 65k gas each)
    est_gas = 65000 * 2
    est_cost = (est_gas * w3.eth.gas_price) / 10**18
    print(f"Estimated MATIC cost for 2 transfers: {est_cost:.6f} MATIC")
    if est_cost > deal_matic:
        print("CRITICAL: Deal wallet MATIC balance is TOO LOW for two transactions!")

if __name__ == "__main__":
    asyncio.run(check_balances())
