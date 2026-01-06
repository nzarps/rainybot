#!/usr/bin/env python3
"""Test POA middleware with actual transaction."""

from web3 import Web3
try:
    from web3.middleware.geth_poa import geth_poa_middleware
except ImportError:
    from web3.middleware import geth_poa_middleware
import config

BLOCK_NUM = 81244793

print("Testing POA middleware...")

for i, rpc in enumerate(config.POLYGON_RPC_URLS):
    print(f"\n[RPC {i+1}] {rpc}")
    try:
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
        
        # Inject POA middleware
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if not w3.is_connected():
            print("  ❌ Not connected")
            continue
        
        print("  ✅ Connected")
        
        # Fetch block
        print(f"  Fetching block {BLOCK_NUM}...")
        block = w3.eth.get_block(BLOCK_NUM)
        
        print(f"  ✅ Block fetched successfully")
        print(f"  Block type: {type(block)}")
        
        if 'timestamp' in block:
            ts = block['timestamp']
            print(f"  ✅ Timestamp: {ts} (type: {type(ts)})")
            
            # Convert to int
            ts_int = int(ts)
            print(f"  ✅ Converted: {ts_int}")
            print(f"  ✅ Discord format: <t:{ts_int}:f>")
        else:
            print(f"  ❌ No timestamp in block")
        
        break
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\nDone!")
