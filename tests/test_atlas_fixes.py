"""
ATLAS AI — Backend Test Suite
Fix #14 & #15: Pytest coverage for critical code paths.
Run: pytest tests/ -v
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Fix #2: Simulation Input Validation Tests ─────────────────────────────────

class TestSimulateRequestValidation:
    """Test that the SimulateRequest Pydantic model rejects invalid inputs."""

    def test_iterations_must_be_positive(self):
        from pydantic import ValidationError
        from src.api.main import SimulateRequest

        with pytest.raises(ValidationError, match="iterations must be greater than 0"):
            SimulateRequest(source="A", target="B", iterations=0)

    def test_iterations_negative(self):
        from pydantic import ValidationError
        from src.api.main import SimulateRequest

        with pytest.raises(ValidationError, match="iterations must be greater than 0"):
            SimulateRequest(source="A", target="B", iterations=-10)

    def test_iterations_exceeds_max(self):
        from pydantic import ValidationError
        from src.api.main import SimulateRequest

        with pytest.raises(ValidationError, match="iterations must not exceed 100000"):
            SimulateRequest(source="A", target="B", iterations=200000)

    def test_valid_request(self):
        from src.api.main import SimulateRequest
        req = SimulateRequest(source="NODE_A", target="NODE_B", iterations=1000)
        assert req.iterations == 1000
        assert req.source == "NODE_A"
        assert req.target == "NODE_B"

    def test_empty_source_rejected(self):
        from pydantic import ValidationError
        from src.api.main import SimulateRequest

        with pytest.raises(ValidationError, match="node ID must not be empty"):
            SimulateRequest(source="", target="B")

    def test_whitespace_source_rejected(self):
        from pydantic import ValidationError
        from src.api.main import SimulateRequest

        with pytest.raises(ValidationError, match="node ID must not be empty"):
            SimulateRequest(source="   ", target="B")

    def test_default_iterations(self):
        from src.api.main import SimulateRequest
        req = SimulateRequest(source="A", target="B")
        assert req.iterations == 5000


# ─── Fix #5: Feedback Contract Tests ────────────────────────────────────────────

class TestFeedbackRequestValidation:
    """Test the feedback rating contract enforcement."""

    def test_valid_helpful(self):
        from src.api.main import FeedbackRequest
        fb = FeedbackRequest(recommendation_id="abc-123", rating=1)
        assert fb.rating == 1

    def test_valid_unhelpful(self):
        from src.api.main import FeedbackRequest
        fb = FeedbackRequest(recommendation_id="abc-123", rating=-1)
        assert fb.rating == -1

    def test_invalid_rating_5(self):
        from pydantic import ValidationError
        from src.api.main import FeedbackRequest

        with pytest.raises(ValidationError, match="rating must be 1"):
            FeedbackRequest(recommendation_id="abc-123", rating=5)

    def test_invalid_rating_0(self):
        from pydantic import ValidationError
        from src.api.main import FeedbackRequest

        with pytest.raises(ValidationError, match="rating must be 1"):
            FeedbackRequest(recommendation_id="abc-123", rating=0)


# ─── Fix #4: Zip Slip Protection Tests ──────────────────────────────────────────

class TestGDELTZipSlipProtection:
    """Test the path traversal protection in GDELT client."""

    def test_safe_path(self):
        from src.ingestion.gdelt_client import GDELTClient
        assert GDELTClient._is_safe_path("data.csv", "/tmp/output") is True

    def test_safe_nested_path(self):
        from src.ingestion.gdelt_client import GDELTClient
        assert GDELTClient._is_safe_path("subdir/data.csv", "/tmp/output") is True

    def test_traversal_blocked(self):
        from src.ingestion.gdelt_client import GDELTClient
        assert GDELTClient._is_safe_path("../../etc/passwd", "/tmp/output") is False

    def test_absolute_path_outside_blocked(self):
        from src.ingestion.gdelt_client import GDELTClient
        assert GDELTClient._is_safe_path("/etc/passwd", "/tmp/output") is False


# ─── Fix #9: Resilience Score Normalization Tests ─────────────────────────────────

class TestResilienceScoreNormalization:
    """Test that resilience scores are in 0..1 range (Fix #9)."""

    def test_unknown_node_returns_zero(self):
        from src.prediction.network_model import SupplyChainNetwork
        sc = SupplyChainNetwork()
        assert sc.calculate_resilience_score("NONEXISTENT") == 0.0

    def test_isolated_node_has_floor(self):
        from src.prediction.network_model import SupplyChainNetwork
        sc = SupplyChainNetwork()
        sc.graph.add_node("ISOLATED")
        score = sc.calculate_resilience_score("ISOLATED")
        assert score == 0.1  # floor of 10%

    def test_connected_node_in_range(self):
        from src.prediction.network_model import SupplyChainNetwork
        sc = SupplyChainNetwork()
        sc.graph.add_node("A")
        sc.graph.add_node("B")
        sc.graph.add_node("C")
        sc.graph.add_edge("A", "B", weight=1.0)
        sc.graph.add_edge("C", "A", weight=1.0)
        score = sc.calculate_resilience_score("A")
        assert 0.0 <= score <= 1.0, f"Score {score} out of 0..1 range"

    def test_highly_connected_capped_at_one(self):
        from src.prediction.network_model import SupplyChainNetwork
        sc = SupplyChainNetwork()
        # Create a hub with 10 connections
        sc.graph.add_node("HUB")
        for i in range(10):
            sc.graph.add_node(f"N{i}")
            sc.graph.add_edge("HUB", f"N{i}", weight=1.0)
            sc.graph.add_edge(f"N{i}", "HUB", weight=1.0)
        score = sc.calculate_resilience_score("HUB")
        assert score == 1.0  # capped at 1.0


# ─── Fix #2: Monte Carlo Guard Tests ────────────────────────────────────────────

class TestMonteCarloGuards:
    """Test Monte Carlo simulator edge-case handling."""

    def test_zero_iterations_returns_error(self):
        from src.prediction.monte_carlo import RiskSimulator
        from src.prediction.network_model import SupplyChainNetwork
        sc = SupplyChainNetwork()
        sim = RiskSimulator(sc)
        result = sim.simulate_route_risk([], iterations=0)
        assert "error" in result

    def test_invalid_edge_returns_error(self):
        from src.prediction.monte_carlo import RiskSimulator
        from src.prediction.network_model import SupplyChainNetwork
        sc = SupplyChainNetwork()
        sc.graph.add_node("A")
        sc.graph.add_node("B")
        # No edge between A and B
        sim = RiskSimulator(sc)
        result = sim.simulate_route_risk([("A", "B")], iterations=100)
        assert "error" in result

    def test_valid_simulation(self):
        from src.prediction.monte_carlo import RiskSimulator
        from src.prediction.network_model import SupplyChainNetwork
        sc = SupplyChainNetwork()
        sc.graph.add_node("A")
        sc.graph.add_node("B")
        sc.graph.add_edge("A", "B", weight=5.0)
        sim = RiskSimulator(sc)
        result = sim.simulate_route_risk([("A", "B")], iterations=100)
        assert "error" not in result
        assert result["iterations"] == 100
        assert result["mean_days"] > 0


# ─── Fix #3: Config Security Tests ──────────────────────────────────────────────

class TestConfigSecurity:
    """Verify config doesn't leak insecure defaults in production mode."""

    def test_dev_mode_has_password_fallback(self):
        # In dev mode (default), password fallback is allowed
        from src.config import NEO4J_PASSWORD
        # This should not raise — dev mode allows fallback
        assert NEO4J_PASSWORD is not None


# ─── Fix #10: API Response Source Metadata ───────────────────────────────────────

class TestAPIResponseMetadata:
    """Test that API responses include source metadata."""

    def test_events_endpoint_returns_unavailable_without_demo_fallback(self, monkeypatch):
        import src.api.main as api_main

        monkeypatch.setattr(api_main, "get_neo4j_client", lambda: (None, "neo4j offline"))
        response = api_main.get_events()

        assert response["events"] == []
        assert response["count"] == 0
        assert response["source"] == "unavailable"

    def test_graph_nodes_endpoint_returns_unavailable_without_demo_fallback(self, monkeypatch):
        import src.api.main as api_main

        monkeypatch.setattr(api_main, "get_neo4j_client", lambda: (None, "neo4j offline"))
        response = api_main.get_graph_nodes()

        assert response["nodes"] == []
        assert response["count"] == 0
        assert response["source"] == "unavailable"

    def test_metrics_endpoint_returns_zeroed_unavailable_state(self, monkeypatch):
        import src.api.main as api_main

        monkeypatch.setattr(api_main, "get_neo4j_client", lambda: (None, "neo4j offline"))
        response = api_main.get_dashboard_metrics()

        assert response["total_active_events"] == 0
        assert response["high_risk_nodes"] == 0
        assert response["monitored_nodes"] == 0
        assert response["weather_alerts"] == 0
        assert response["source"] == "unavailable"

    def test_demo_mode_returns_demo_events_only_when_selected(self, monkeypatch):
        import src.api.main as api_main

        monkeypatch.setattr(api_main, "_runtime_mode", "demo")
        monkeypatch.setattr(api_main, "get_neo4j_client", lambda: (None, "neo4j offline"))

        response = api_main.get_events()

        assert response["count"] == len(api_main.DEMO_EVENTS)
        assert response["source"] == "demo"

    def test_mode_endpoint_switches_runtime_mode(self, monkeypatch):
        import src.api.main as api_main

        monkeypatch.setattr(api_main, "_runtime_mode", "live")

        response = api_main.set_mode(api_main.ModeRequest(mode="demo"))

        assert response["mode"] == "demo"
        assert api_main.current_mode() == "demo"
