#!/usr/bin/env python3
"""Debug script to inspect Polygon block timestamp structure."""

from web3 import Web3
import config

# Use block number from the screenshot
BLOCK_NUM = 81244793

print("=" * 60)
print("POLYGON TIMESTAMP DEBUG")
print("=" * 60)

for i, rpc in enumerate(config.POLYGON_RPC_URLS):
    print(f"\n[RPC {i+1}] {rpc}")
    try:
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
        
        if not w3.is_connected():
            print("  ❌ Not connected")
            continue
        
        print("  ✅ Connected")
        
        # Get block directly
        print(f"  Fetching block {BLOCK_NUM}...")
        
        block = w3.eth.get_block(BLOCK_NUM)
        print(f"  Block type: {type(block)}")
        print(f"  Block keys: {list(block.keys())}")
        
        if 'timestamp' in block:
            ts = block['timestamp']
            print(f"  ✅ timestamp found: {ts} (type: {type(ts)})")
            print(f"     repr: {repr(ts)}")
            print(f"     str: {str(ts)}")
            
            # Try different access methods
            try:
                ts_get = block.get('timestamp')
                print(f"     .get('timestamp'): {ts_get} (type: {type(ts_get)})")
            except Exception as e:
                print(f"     .get('timestamp') failed: {e}")
            
            try:
                ts_attr = block.timestamp
                print(f"     .timestamp: {ts_attr} (type: {type(ts_attr)})")
            except Exception as e:
                print(f"     .timestamp failed: {e}")
            
            # Try conversion
            try:
                if hasattr(ts, 'hex'):
                    ts_int = int(ts.hex(), 16)
                    print(f"     Converted via hex: {ts_int}")
                else:
                    ts_int = int(ts)
                    print(f"     Converted via int(): {ts_int}")
                
                # Test Discord format
                discord_fmt = f"<t:{ts_int}:f>"
                print(f"     Discord format: {discord_fmt}")
            except Exception as e:
                print(f"     ❌ Conversion failed: {e}")
        else:
            print(f"  ❌ 'timestamp' not in block!")
        
        # Success - stop after first working RPC
        break
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
