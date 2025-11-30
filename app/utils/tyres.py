"""Tyre compound utilities"""
from typing import Dict


def get_tyre_compound_int(compound: str) -> int:
    """
    Convert tyre compound string to integer representation.
    
    Args:
        compound: Tyre compound string (e.g., 'SOFT', 'MEDIUM', 'HARD', etc.)
    
    Returns:
        Integer representation of the compound
    """
    compound_mapping: Dict[str, int] = {
        'SOFT': 1,
        'MEDIUM': 2,
        'HARD': 3,
        'INTERMEDIATE': 4,
        'WET': 5,
        'UNKNOWN': 0,
    }
    
    if compound is None:
        return 0
    
    compound_upper = str(compound).upper()
    return compound_mapping.get(compound_upper, 0)

