def test_route_optimizer_imports():
    from backend.services.route_optimizer import build_greedy_plan
    assert callable(build_greedy_plan)
