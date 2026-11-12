from backend.services.validation import validate_dataset

def test_generated_data_is_valid():
    result = validate_dataset()
    assert result["valid"], result["errors"]
