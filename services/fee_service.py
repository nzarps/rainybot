"""
Fee Service Module

Handles fee calculation and deduction for the escrow bot.
Fees are deducted during release operations and sent to configured fee addresses.
"""

import config
import logging

logger = logging.getLogger(__name__)


def is_fees_enabled() -> bool:
    """Check if fee deduction is enabled."""
    return config.FEES_ENABLED


def get_fee_percentage(currency: str = None) -> float:
    """
    Get the configured fee percentage.
    If currency is provided, checks specific CRYPTO_FEES first.
    """
    if currency and hasattr(config, 'CRYPTO_FEES'):
        normalized_currency = currency.lower()
        if normalized_currency in config.CRYPTO_FEES:
             val = config.CRYPTO_FEES[normalized_currency]
             if val is not None and val > 0:
                 return val
    
    return config.FEES_PERCENTAGE


def get_fee_address(currency: str) -> str | None:
    """
    Get the fee address for a given currency.
    Returns None if no fee address is configured.
    """
    return config.FEE_ADDRESSES.get(currency)


def calculate_fee(amount: float, currency: str) -> tuple[float, float]:
    """
    Calculate the fee amount and remaining amount after fee deduction.
    
    Args:
        amount: The total amount in crypto units
        currency: The currency type (ltc, usdt_bep20, usdt_polygon, solana, ethereum)
    
    Returns:
        tuple: (fee_amount, remaining_amount)
               If fees are disabled or no fee address is configured, returns (0, amount)
    """
    if not is_fees_enabled():
        return (0.0, amount)
    
    fee_address = get_fee_address(currency)
    if not fee_address:
        # logger.info(f"[FEE] No fee address configured for {currency}, skipping fee deduction")
        # Keep it silent on production unless debug
        logger.debug(f"[FEE] No fee address configured for {currency}, skipping fee deduction")
        return (0.0, amount)
    
    # Pass currency to get dynamic fee
    fee_percentage = get_fee_percentage(currency)
    
    fee_amount = amount * (fee_percentage / 100.0)
    remaining_amount = amount - fee_amount
    
    logger.info(f"[FEE] Calculated {fee_percentage}% fee for {currency}: {fee_amount:.8f}")
    logger.info(f"[FEE] Remaining after fee: {remaining_amount:.8f} {currency}")
    
    return (fee_amount, remaining_amount)


def calculate_fee_from_usdt(amount_usdt: float, currency: str = None) -> tuple[float, float]:
    """
    Calculate the fee amount in USD terms.
    
    Args:
        amount_usdt: The total amount in USD
    
    Returns:
        tuple: (fee_amount_usd, remaining_amount_usd)
    """
    if not is_fees_enabled():
        return (0.0, amount_usdt)
    
    fee_percentage = get_fee_percentage(currency)
    fee_amount = amount_usdt * (fee_percentage / 100.0)
    remaining_amount = amount_usdt - fee_amount
    
    return (fee_amount, remaining_amount)


def should_deduct_fee(currency: str) -> bool:
    """
    Check if fee should be deducted for a given currency.
    Fees are only deducted if enabled AND a fee address is configured.
    """
    if not is_fees_enabled():
        return False
    
    fee_address = get_fee_address(currency)
    return fee_address is not None and fee_address.strip() != ""
