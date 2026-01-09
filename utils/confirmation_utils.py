
async def get_evm_confirmations(txid, rpc_urls):
    """Get confirmations for an EVM transaction."""
    from web3 import AsyncWeb3, AsyncHTTPProvider
    
    # Try each RPC until we get a result
    for rpc in rpc_urls:
        try:
            w3 = AsyncWeb3(AsyncHTTPProvider(rpc, request_kwargs={"timeout": 5}))
            if not await w3.is_connected(): continue
            
            # Get Transaction Receipt to find Block Number
            try:
                tx_receipt = await w3.eth.get_transaction_receipt(txid)
            except Exception:
                # Transaction might be pending or not found yet on this node
                continue
                
            if not tx_receipt: continue
            
            tx_block = tx_receipt['blockNumber']
            current_block = await w3.eth.block_number
            
            if tx_block and current_block:
                return max(0, current_block - tx_block + 1)
                
        except Exception:
            continue
            
    return 0

async def get_solana_confirmations(txid):
    """Get confirmations for a Solana transaction."""
    # For Solana, we typically check for 'confirmed' or 'finalized' status
    # But to map to 0/2, 1/2, 2/2 logic:
    # 0: Processed but not confirmed
    # 1: Confirmed (approx 1-31 confirmations)
    # 2: Finalized (32+ confirmations) or simply 'finalized' commitment
    
    # This matches the user's expected flow.
    from solders.signature import Signature
    
    session = await get_session()
    
    for rpc in SOLANA_RPC_URLS:
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignatureStatuses",
                "params": [[txid], {"searchTransactionHistory": True}]
            }
            async with session.post(rpc, json=payload, timeout=5) as r:
                if r.status == 200:
                    data = await r.json()
                    result = data.get("result", {})
                    if result and result.get("value"):
                        status_info = result["value"][0]
                        if not status_info: continue
                        
                        conf_status = status_info.get("confirmationStatus")
                        # finalized, confirmed, processed
                        
                        if conf_status == "finalized":
                            return 2
                        elif conf_status == "confirmed":
                            return 1
                        elif conf_status == "processed":
                            return 0
        except:
            continue
            
    return 0
