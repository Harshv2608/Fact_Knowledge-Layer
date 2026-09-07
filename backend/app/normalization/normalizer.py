import re

def normalize_value(value_str: str, unit_str: str) -> float | None:
    if not value_str:
        return None
        
    # Remove commas and extract first number
    clean_val = str(value_str).replace(",", "")
    match = re.search(r"[-+]?\d*\.\d+|\d+", clean_val)
    if not match:
        return None
        
    try:
        num = float(match.group())
    except ValueError:
        return None
    
    # Handle implicit scale in the value string
    lower_val = clean_val.lower()
    if "billion" in lower_val:
        num *= 1_000_000_000
    elif "million" in lower_val:
        num *= 1_000_000
    elif "crore" in lower_val:
        num *= 10_000_000
    elif "lakh" in lower_val:
        num *= 100_000
        
    # Handle scale in unit string
    if unit_str:
        lower_unit = str(unit_str).lower()
        if "billion" in lower_unit and "billion" not in lower_val:
            num *= 1_000_000_000
        elif "million" in lower_unit and "million" not in lower_val:
            num *= 1_000_000
        elif "crore" in lower_unit and "crore" not in lower_val:
            num *= 10_000_000
        elif "lakh" in lower_unit and "lakh" not in lower_val:
            num *= 100_000
            
    return num
