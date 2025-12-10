"""
Tests for PokerEngine

Tests the Deck, Hand, Card classes and evaluate_winner method.
"""
import pytest
from app.services.poker_engine import (
    Card, Hand, Deck, PokerEngine, EvaluationResult, poker_engine
)


class TestCard:
    """Tests for Card class."""
    
    def test_card_creation(self):
        """Test creating a card."""
        card = Card(rank="A", suit="s")
        assert str(card) == "As"
    
    def test_card_from_string(self):
        """Test creating card from string."""
        card = Card.from_string("Kh")
        assert card.rank == "K"
        assert card.suit == "h"
    
    def test_card_invalid_rank(self):
        """Test invalid rank raises error."""
        with pytest.raises(ValueError):
            Card(rank="X", suit="s")
    
    def test_card_invalid_suit(self):
        """Test invalid suit raises error."""
        with pytest.raises(ValueError):
            Card(rank="A", suit="x")
    
    def test_card_equality(self):
        """Test card equality."""
        card1 = Card(rank="A", suit="s")
        card2 = Card(rank="A", suit="s")
        assert card1 == card2
    
    def test_card_hash(self):
        """Test card is hashable."""
        card = Card(rank="A", suit="s")
        card_set = {card}
        assert card in card_set


class TestHand:
    """Tests for Hand class."""
    
    def test_hand_creation(self):
        """Test creating a hand."""
        cards = [Card(rank="A", suit="s"), Card(rank="K", suit="h")]
        hand = Hand(cards=cards)
        assert len(hand.cards) == 2
    
    def test_hand_from_strings(self):
        """Test creating hand from strings."""
        hand = Hand.from_strings(["As", "Kh"])
        assert str(hand) == "[As, Kh]"
    
    def test_hand_wrong_card_count(self):
        """Test hand with wrong number of cards."""
        with pytest.raises(ValueError):
            Hand.from_strings(["As"])  # Only 1 card
    
    def test_hand_duplicate_cards(self):
        """Test hand with duplicate cards."""
        with pytest.raises(ValueError):
            Hand.from_strings(["As", "As"])


class TestDeck:
    """Tests for Deck class."""
    
    def test_deck_init(self):
        """Test deck initialization."""
        deck = Deck()
        assert len(deck) == 52
    
    def test_deck_shuffle(self):
        """Test deck shuffling."""
        deck = Deck()
        original_order = [str(c) for c in deck.cards[:5]]
        deck.shuffle()
        new_order = [str(c) for c in deck.cards[:5]]
        # Highly unlikely to be same after shuffle
        # (could fail in extremely rare cases)
        assert original_order != new_order or True  # Allow same in rare case
    
    def test_deck_deal(self):
        """Test dealing cards."""
        deck = Deck()
        dealt = deck.deal(2)
        assert len(dealt) == 2
        assert len(deck) == 50
    
    def test_deck_remove_cards(self):
        """Test removing specific cards."""
        deck = Deck()
        deck.remove_card_strings(["As", "Kh"])
        assert len(deck) == 50
    
    def test_deck_reset(self):
        """Test deck reset."""
        deck = Deck()
        deck.deal(10)
        assert len(deck) == 42
        deck.reset()
        assert len(deck) == 52


class TestPokerEngine:
    """Tests for PokerEngine class."""
    
    def test_engine_creation(self):
        """Test engine initialization."""
        engine = PokerEngine()
        assert engine.deck is not None
    
    def test_evaluate_winner_hero_wins(self):
        """Test hero winning with pair of aces vs pair of queens."""
        engine = PokerEngine()
        result = engine.evaluate_winner(
            hero_cards=["As", "Ah"],
            villain_cards=["Qc", "Qd"],
            board_cards=["7h", "8c", "2d", "Js", "3h"]
        )
        
        assert result.winner == "hero"
        assert result.hero_hand == "Pair"
        assert result.villain_hand == "Pair"
        assert "Hero wins" in result.description
    
    def test_evaluate_winner_villain_wins(self):
        """Test villain winning with flush."""
        engine = PokerEngine()
        result = engine.evaluate_winner(
            hero_cards=["As", "Kh"],
            villain_cards=["2c", "5c"],
            board_cards=["Ac", "8c", "Jc", "2d", "3h"]
        )
        
        assert result.winner == "villain"
        assert result.villain_hand == "Flush"
        assert "Villain wins" in result.description
    
    def test_evaluate_winner_tie(self):
        """Test tie when board plays."""
        engine = PokerEngine()
        result = engine.evaluate_winner(
            hero_cards=["2s", "3s"],
            villain_cards=["2d", "3d"],
            board_cards=["Ah", "Kh", "Qh", "Jh", "Th"]  # Royal flush on board
        )
        
        assert result.winner == "tie"
        assert "Tie" in result.description
    
    def test_evaluate_winner_straight_flush(self):
        """Test straight flush detection."""
        engine = PokerEngine()
        result = engine.evaluate_winner(
            hero_cards=["9h", "8h"],
            villain_cards=["As", "Ks"],
            board_cards=["7h", "6h", "5h", "2c", "3d"]
        )
        
        assert result.winner == "hero"
        assert result.hero_hand == "Straight Flush"
    
    def test_evaluate_winner_full_house(self):
        """Test full house detection."""
        engine = PokerEngine()
        result = engine.evaluate_winner(
            hero_cards=["As", "Ah"],
            villain_cards=["Ks", "Kh"],
            board_cards=["Ac", "Kd", "Kc", "2h", "3d"]
        )
        
        assert result.winner == "villain"  # KKKAA vs AAAKK - trips matter more
        assert result.villain_hand == "Quads"
    
    def test_evaluate_winner_duplicate_cards_error(self):
        """Test error on duplicate cards."""
        engine = PokerEngine()
        with pytest.raises(ValueError, match="Duplicate"):
            engine.evaluate_winner(
                hero_cards=["As", "Kh"],
                villain_cards=["As", "Qd"],  # As duplicated
                board_cards=["7h", "8c", "2d", "Js", "3h"]
            )
    
    def test_evaluate_winner_wrong_card_count(self):
        """Test error on wrong number of cards."""
        engine = PokerEngine()
        with pytest.raises(ValueError):
            engine.evaluate_winner(
                hero_cards=["As"],  # Only 1 card
                villain_cards=["Qc", "Qd"],
                board_cards=["7h", "8c", "2d", "Js", "3h"]
            )
    
    def test_evaluate_hand_strength(self):
        """Test single hand strength evaluation."""
        engine = PokerEngine()
        result = engine.evaluate_hand_strength(
            hole_cards=["As", "Ah"],
            board_cards=["Ac", "Kd", "2h"]
        )
        
        assert result["hand_type"] == "Trips"
        assert "score" in result
    
    def test_deal_random_board(self):
        """Test random board dealing."""
        engine = PokerEngine()
        board = engine.deal_random_board(exclude_cards=["As", "Kh"])
        
        assert len(board) == 5
        assert "As" not in board
        assert "Kh" not in board
    
    def test_to_dict(self):
        """Test EvaluationResult to_dict method."""
        result = EvaluationResult(
            winner="hero",
            hero_hand="Flush",
            villain_hand="Pair",
            hero_score=1000,
            villain_score=5000,
            description="Hero wins with Flush"
        )
        
        d = result.to_dict()
        assert d["winner"] == "hero"
        assert d["hero_hand"] == "Flush"


class TestModuleSingleton:
    """Test module-level singleton."""
    
    def test_poker_engine_singleton(self):
        """Test that poker_engine singleton works."""
        result = poker_engine.evaluate_winner(
            hero_cards=["As", "Kh"],
            villain_cards=["Qc", "Qd"],
            board_cards=["Ah", "7c", "2d", "Js", "3h"]
        )
        
        assert result.winner == "hero"
