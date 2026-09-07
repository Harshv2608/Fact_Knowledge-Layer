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

def parse_time_context(time_str: str) -> dict | None:
    """
    Parses a time string into a structured representation (start_year, end_year) 
    for temporal overlap reasoning. Returns dict if parseable, None otherwise.
    """
    if not time_str:
        return None
        
    lower_time = time_str.lower()
    
    # Handle explicitly hyphenated years like "2024-25" or "2024/25"
    range_match = re.search(r'20(\d{2})[-/](\d{2})', lower_time)
    if range_match:
        start = 2000 + int(range_match.group(1))
        return {"type": "fiscal_year", "start_year": start, "end_year": start + 1}
        
    # Handle "FY24", "FY 2024" -> In India, FY24 = April 2023 to March 2024
    fy_match = re.search(r'(fy|fiscal year)\s*(?:20)?(\d{2})', lower_time)
    if fy_match:
        end_year = 2000 + int(fy_match.group(2))
        start_year = end_year - 1
        return {"type": "fiscal_year", "start_year": start_year, "end_year": end_year}
        
    year_match = re.search(r'20\d{2}', lower_time)
    if year_match:
        year = int(year_match.group())
        return {"type": "calendar_year", "start_year": year, "end_year": year}
        
    return None
