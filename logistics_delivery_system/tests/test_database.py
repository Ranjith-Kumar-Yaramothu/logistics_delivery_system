def test_database_configuration_imports():
    from backend.database import Base, engine
    assert Base is not None
    assert engine is not None
