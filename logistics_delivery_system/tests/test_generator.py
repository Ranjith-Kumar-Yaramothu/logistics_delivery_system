from backend.services.data_generator import generate_dataset

def test_starter_generator_returns_expected_counts():
    result = generate_dataset("starter", 20261022)
    assert result["counts"]["customer_sites"] == 30
    assert result["counts"]["deliveries"] == 100
