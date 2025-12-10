"""
Tests for Equity Calculator

Tests pre-flop equity calculations against known poker odds.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.equity_calculator import equity_calculator


client = TestClient(app)


class TestEquityCalculator:
    """Unit tests for the equity calculator service."""
    
    def test_parse_card(self):
        """Test card parsing to treys format."""
        # Should not raise
        equity_calculator.parse_card("As")
        equity_calculator.parse_card("Kh")
        equity_calculator.parse_card("2c")
        equity_calculator.parse_card("Td")
    
    def test_get_hand_name_pocket_pair(self):
        """Test hand naming for pocket pairs."""
        assert "Pocket Ace" in equity_calculator.get_hand_name(["As", "Ah"])
        assert "Pocket King" in equity_calculator.get_hand_name(["Ks", "Kd"])
    
    def test_get_hand_name_suited(self):
        """Test hand naming for suited hands."""
        name = equity_calculator.get_hand_name(["As", "Ks"])
        assert "suited" in name
        assert "Ace" in name
        assert "King" in name
    
    def test_get_hand_name_offsuit(self):
        """Test hand naming for offsuit hands."""
        name = equity_calculator.get_hand_name(["As", "Kh"])
        assert "offsuit" in name
    
    def test_preflop_equity_aa_vs_kk(self):
        """AA vs KK should be approximately 82% vs 18%."""
        result = equity_calculator.calculate_preflop_equity(
            ["As", "Ah"],
            ["Ks", "Kh"],
            iterations=5000
        )
        
        # AA should win roughly 80-84%
        assert 78 <= result["hero_equity"] <= 86
        assert 14 <= result["villain_equity"] <= 22
    
    def test_preflop_equity_aks_vs_qq(self):
        """AKs vs QQ should be approximately 46% vs 54%."""
        result = equity_calculator.calculate_preflop_equity(
            ["As", "Ks"],
            ["Qc", "Qd"],
            iterations=5000
        )
        
        # AKs vs QQ is a classic race, approximately 43-47% for AK
        assert 40 <= result["hero_equity"] <= 50
        assert 50 <= result["villain_equity"] <= 60
    
    def test_preflop_equity_coinflip(self):
        """22 vs AKo is a classic coinflip (~52% vs 48%)."""
        result = equity_calculator.calculate_preflop_equity(
            ["2s", "2h"],
            ["As", "Kh"],
            iterations=5000
        )
        
        # Small pair vs two overcards is close to 50-50
        assert 48 <= result["hero_equity"] <= 56
        assert 44 <= result["villain_equity"] <= 52


class TestEquityEndpoint:
    """API endpoint tests."""
    
    def test_health_check(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Poker SaaS API" in response.json()["message"]
    
    def test_preflop_equity_endpoint(self):
        """Test pre-flop equity API endpoint."""
        response = client.post(
            "/api/equity/preflop",
            json={
                "hero_cards": ["As", "Kh"],
                "villain_cards": ["Qc", "Qd"],
                "iterations": 1000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "hero_equity" in data
        assert "villain_equity" in data
        assert "tie_percentage" in data
        assert "hero_hand_name" in data
        assert "villain_hand_name" in data
        
        # Equity should sum to approximately 100
        total = data["hero_equity"] + data["villain_equity"] + data["tie_percentage"]
        assert 99 <= total <= 101
    
    def test_preflop_duplicate_cards_error(self):
        """Test error when same card appears twice."""
        response = client.post(
            "/api/equity/preflop",
            json={
                "hero_cards": ["As", "Kh"],
                "villain_cards": ["As", "Qd"]  # As is duplicated
            }
        )
        
        assert response.status_code == 400
        assert "unique" in response.json()["detail"].lower()
    
    def test_preflop_invalid_card_format(self):
        """Test error for invalid card format."""
        response = client.post(
            "/api/equity/preflop",
            json={
                "hero_cards": ["XX", "Kh"],  # Invalid card
                "villain_cards": ["Qc", "Qd"]
            }
        )
        
        # Should fail validation (422) or bad request (400)
        assert response.status_code in [400, 422]
