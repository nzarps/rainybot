import asyncio
import config
from web3 import Web3

# The deal wallet address from the screenshot
DEAL_WALLET = "0xd2be00e5174382DAaDf3A7c3788d3a8dff15c29D"

async def check_deal_wallet():
    """Check if the deal wallet has USDT and MATIC"""
    print(f"📍 Deal Wallet: {DEAL_WALLET}")
    
    for rpc in config.POLYGON_RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            if not w3.is_connected():
                print(f"  ❌ RPC offline: {rpc}")
                continue
            
            # Check MATIC balance
            balance_wei = w3.eth.get_balance(DEAL_WALLET)
            balance_matic = balance_wei / (10**18)
            print(f"  MATIC Balance: {balance_matic:.6f} MATIC")
            
            # Check USDT balance
            usdt_abi = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]
            contract = w3.eth.contract(Web3.to_checksum_address(config.USDT_POLYGON_CONTRACT), abi=usdt_abi)
            usdt_wei = contract.functions.balanceOf(Web3.to_checksum_address(DEAL_WALLET)).call()
            usdt_balance = usdt_wei / (10**config.USDT_POLYGON_DECIMALS)
            print(f"  USDT Balance: {usdt_balance:.6f} USDT")
            
            # Check if gas is sufficient
            if balance_matic >= config.POLYGON_GAS_REQUIRED:
                print(f"  ✅ Gas is SUFFICIENT (need {config.POLYGON_GAS_REQUIRED}, have {balance_matic:.6f})")
            else:
                print(f"  ❌ Gas is INSUFFICIENT (need {config.POLYGON_GAS_REQUIRED}, have {balance_matic:.6f})")
            
            break
        except Exception as e:
            print(f"  ❌ RPC error ({rpc}): {e}")

if __name__ == "__main__":
    asyncio.run(check_deal_wallet())
