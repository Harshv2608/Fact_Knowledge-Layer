from app.normalization.normalizer import normalize_value

def test_normalize_value_basic():
    assert normalize_value("8.5", None) == 8.5
    assert normalize_value("100", "%") == 100.0

def test_normalize_value_commas():
    assert normalize_value("8,142", None) == 8142.0

def test_normalize_value_implicit_scale():
    assert normalize_value("81.42 billion", None) == 81420000000.0
    assert normalize_value("1.5 million", None) == 1500000.0
    assert normalize_value("8,142 crore", None) == 81420000000.0

def test_normalize_value_explicit_scale_in_unit():
    assert normalize_value("81.42", "billion USD") == 81420000000.0
    assert normalize_value("8,142", "crore INR") == 81420000000.0

def test_normalize_value_negative():
    assert normalize_value("-1.0", "US$ billion") == -1000000000.0
