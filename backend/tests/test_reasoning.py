from app.reasoning.comparator import deterministic_compare

def test_deterministic_compare_values_match():
    fact_a = {"normalized_numeric_value": 8.5}
    fact_b = {"normalized_numeric_value": 8.5}
    res = deterministic_compare(fact_a, fact_b)
    assert res["value_match"] is True

def test_deterministic_compare_values_mismatch():
    fact_a = {"normalized_numeric_value": 1.0}
    fact_b = {"normalized_numeric_value": -1.0}
    res = deterministic_compare(fact_a, fact_b)
    assert res["value_match"] is False

def test_deterministic_compare_time_match():
    fact_a = {"time_context": "FY2024/25"}
    fact_b = {"time_context": "FY2024/25"}
    res = deterministic_compare(fact_a, fact_b)
    assert res["time_match"] is True

def test_deterministic_compare_time_mismatch():
    fact_a = {"time_context": "FY24"}
    fact_b = {"time_context": "April - December 2024"}
    res = deterministic_compare(fact_a, fact_b)
    assert res["time_match"] is False
