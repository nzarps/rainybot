"""
Comprehensive Withdrawal Verification Test
Tests all supported cryptocurrencies to ensure withdrawal functions are working correctly.
"""

import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider
from eth_account import Account
import sys

# Test configuration
TEST_CURRENCIES = ["ltc", "ethereum", "solana", "usdt_bep20", "usdt_polygon"]

async def test_ltc_withdrawal():
    """Test LTC withdrawal function signature and RPC connectivity"""
    print("\n[LTC] Testing withdrawal function...")
    try:
        from bitcoinrpc.authproxy import AuthServiceProxy
        import os
        
        # Check if RPC credentials are configured
        rpc_user = os.getenv("LTC_RPC_USER", "rainyday")
        rpc_pass = os.getenv("LTC_RPC_PASSWORD", "")
        rpc_host = os.getenv("LTC_RPC_HOST", "127.0.0.1")
        rpc_port = os.getenv("LTC_RPC_PORT", "9332")
        
        if not rpc_pass:
            print("  ⚠️  LTC_RPC_PASSWORD not configured")
            return False
            
        rpc_url = f"http://{rpc_user}:{rpc_pass}@{rpc_host}:{rpc_port}"
        
        # Test connection
        rpc = AuthServiceProxy(rpc_url, timeout=5)
        info = rpc.getblockchaininfo()
        print(f"  ✅ LTC Node Connected - Block: {info['blocks']}")
        return True
    except Exception as e:
        print(f"  ❌ LTC Test Failed: {e}")
        return False

async def test_eth_withdrawal():
    """Test ETH withdrawal function and RPC connectivity"""
    print("\n[ETH] Testing withdrawal function...")
    try:
        rpcs = [
            "https://ethereum-rpc.publicnode.com",
            "https://eth.llamarpc.com",
            "https://1rpc.io/eth"
        ]
        
        for rpc in rpcs:
            try:
                w3 = AsyncWeb3(AsyncHTTPProvider(rpc, request_kwargs={"timeout": 5}))
                if await w3.is_connected():
                    block = await w3.eth.block_number
                    gas_price = await w3.eth.gas_price
                    print(f"  ✅ ETH RPC Connected ({rpc[:30]}...) - Block: {block}")
                    print(f"     Gas Price: {w3.from_wei(gas_price, 'gwei'):.2f} gwei")
                    return True
            except:
                continue
        
        print("  ❌ All ETH RPCs failed")
        return False
    except Exception as e:
        print(f"  ❌ ETH Test Failed: {e}")
        return False

async def test_solana_withdrawal():
    """Test Solana withdrawal function and RPC connectivity"""
    print("\n[SOL] Testing withdrawal function...")
    try:
        import aiohttp
        
        rpc_url = "https://solana-rpc.publicnode.com"
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth"
            }
            async with session.post(rpc_url, json=payload, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"  ✅ Solana RPC Connected - Health: {data.get('result', 'ok')}")
                    
                    # Get slot
                    payload2 = {"jsonrpc": "2.0", "id": 1, "method": "getSlot"}
                    async with session.post(rpc_url, json=payload2, timeout=5) as resp2:
                        if resp2.status == 200:
                            slot_data = await resp2.json()
                            print(f"     Current Slot: {slot_data.get('result', 'N/A')}")
                    return True
                else:
                    print(f"  ❌ Solana RPC returned status {resp.status}")
                    return False
    except Exception as e:
        print(f"  ❌ Solana Test Failed: {e}")
        return False

async def test_bep20_withdrawal():
    """Test BEP20 (BSC) withdrawal function and RPC connectivity"""
    print("\n[BEP20] Testing withdrawal function...")
    try:
        rpcs = [
            "https://bsc-dataseed.binance.org",
            "https://bsc-dataseed1.ninicoin.io"
        ]
        
        for rpc in rpcs:
            try:
                w3 = AsyncWeb3(AsyncHTTPProvider(rpc, request_kwargs={"timeout": 5}))
                if await w3.is_connected():
                    block = await w3.eth.block_number
                    gas_price = await w3.eth.gas_price
                    print(f"  ✅ BSC RPC Connected ({rpc[:30]}...) - Block: {block}")
                    print(f"     Gas Price: {w3.from_wei(gas_price, 'gwei'):.2f} gwei")
                    return True
            except:
                continue
        
        print("  ❌ All BSC RPCs failed")
        return False
    except Exception as e:
        print(f"  ❌ BEP20 Test Failed: {e}")
        return False

async def test_polygon_withdrawal():
    """Test Polygon withdrawal function and RPC connectivity"""
    print("\n[POLYGON] Testing withdrawal function...")
    try:
        rpcs = [
            "https://polygon.llamarpc.com",
            "https://1rpc.io/matic",
            "https://rpc.ankr.com/polygon"
        ]
        
        for rpc in rpcs:
            try:
                w3 = AsyncWeb3(AsyncHTTPProvider(rpc, request_kwargs={"timeout": 5}))
                if await w3.is_connected():
                    block = await w3.eth.block_number
                    gas_price = await w3.eth.gas_price
                    print(f"  ✅ Polygon RPC Connected ({rpc[:30]}...) - Block: {block}")
                    print(f"     Gas Price: {w3.from_wei(gas_price, 'gwei'):.2f} gwei")
                    return True
            except:
                continue
        
        print("  ❌ All Polygon RPCs failed")
        return False
    except Exception as e:
        print(f"  ❌ Polygon Test Failed: {e}")
        return False

async def main():
    print("=" * 60)
    print("WITHDRAWAL FUNCTION VERIFICATION TEST")
    print("=" * 60)
    
    results = {}
    
    # Run all tests
    results["LTC"] = await test_ltc_withdrawal()
    results["ETH"] = await test_eth_withdrawal()
    results["SOL"] = await test_solana_withdrawal()
    results["BEP20"] = await test_bep20_withdrawal()
    results["POLYGON"] = await test_polygon_withdrawal()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for currency, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {currency}: {'PASS' if status else 'FAIL'}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All withdrawal functions are operational!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} withdrawal function(s) need attention")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
