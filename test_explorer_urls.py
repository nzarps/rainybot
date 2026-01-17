import sys
import os

# Mock the globals that get_explorer_url might use if it were imported normally
# but since we are just testing the logic, we can copy the function or import it carefully

def get_explorer_url(currency, txid):
    """Generate blockchain explorer link based on currency."""
    if not txid or str(txid).lower() == "none" or str(txid).lower() == "manual":
        return None
        
    c = currency.lower()
    txid_str = str(txid)
    
    # Helper to ensure 0x prefix for EVM
    def ensure_0x(h):
        return f"0x{h}" if not h.startswith("0x") else h

    if "polygon" in c or c == "matic":
        return f"https://polygonscan.com/tx/{ensure_0x(txid_str)}"
    elif "bep20" in c or "binance" in c or c == "bnb":
        return f"https://bscscan.com/tx/{ensure_0x(txid_str)}"
    elif "ltc" in c or "litecoin" in c:
        return f"https://blockchair.com/litecoin/transaction/{txid_str}"
    elif "sol" in c or "solana" in c:
        return f"https://solscan.io/tx/{txid_str}"
    elif "eth" in c:
        return f"https://etherscan.io/tx/{ensure_0x(txid_str)}"
        
    return None

def test():
    test_cases = [
        ("ethereum", "123", "https://etherscan.io/tx/0x123"),
        ("eth", "0xabc", "https://etherscan.io/tx/0xabc"),
        ("usdt_bep20", "456", "https://bscscan.com/tx/0x456"),
        ("usdt_polygon", "789", "https://polygonscan.com/tx/0x789"),
        ("ltc", "abc", "https://blockchair.com/litecoin/transaction/abc"),
        ("solana", "def", "https://solscan.io/tx/def"),
        ("invalid", "123", None)
    ]
    
    passed = 0
    for currency, txid, expected in test_cases:
        actual = get_explorer_url(currency, txid)
        if actual == expected:
            print(f"PASSED: {currency} -> {actual}")
            passed += 1
        else:
            print(f"FAILED: {currency} -> Expected {expected}, got {actual}")
            
    print(f"\n{passed}/{len(test_cases)} tests passed.")

if __name__ == "__main__":
    test()
