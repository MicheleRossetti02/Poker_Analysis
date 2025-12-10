"""
PokerEngine - Core Poker Hand Evaluation Module

A modular poker engine using the eval7 library for hand evaluation.
Provides Deck, Hand, and winner evaluation functionality.

Usage:
    from app.services.poker_engine import PokerEngine, Deck, Hand
    
    engine = PokerEngine()
    result = engine.evaluate_winner(
        hero_cards=["As", "Kh"],
        villain_cards=["Qc", "Qd"],
        board_cards=["Ah", "7c", "2d", "Js", "3h"]
    )
    print(result)  # {'winner': 'hero', 'hero_hand': 'Pair', 'villain_hand': 'Pair', ...}
"""
from typing import List, Tuple, Optional, Dict, Any, Literal
from dataclasses import dataclass, field
from enum import Enum
import random

try:
    import eval7
    EVAL7_AVAILABLE = True
except ImportError:
    EVAL7_AVAILABLE = False


class Suit(str, Enum):
    """Card suits enumeration."""
    SPADES = "s"
    HEARTS = "h"
    DIAMONDS = "d"
    CLUBS = "c"


class Rank(str, Enum):
    """Card ranks enumeration (2-A)."""
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "T"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


# Hand ranking names in order from highest to lowest
HAND_RANKS = [
    "Straight Flush",
    "Four of a Kind",
    "Full House",
    "Flush",
    "Straight",
    "Three of a Kind",
    "Two Pair",
    "Pair",
    "High Card"
]


@dataclass
class Card:
    """
    Represents a single playing card.
    
    Attributes:
        rank: The card rank (2-A)
        suit: The card suit (s/h/d/c)
        
    Examples:
        >>> card = Card(rank="A", suit="s")
        >>> str(card)
        'As'
    """
    rank: str
    suit: str
    
    def __post_init__(self) -> None:
        """Validate card rank and suit after initialization."""
        valid_ranks = set(r.value for r in Rank)
        valid_suits = set(s.value for s in Suit)
        
        if self.rank not in valid_ranks:
            raise ValueError(f"Invalid rank '{self.rank}'. Must be one of: {valid_ranks}")
        if self.suit not in valid_suits:
            raise ValueError(f"Invalid suit '{self.suit}'. Must be one of: {valid_suits}")
    
    def __str__(self) -> str:
        """Return string representation (e.g., 'As' for Ace of spades)."""
        return f"{self.rank}{self.suit}"
    
    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"Card(rank='{self.rank}', suit='{self.suit}')"
    
    def __hash__(self) -> int:
        """Make Card hashable for use in sets."""
        return hash((self.rank, self.suit))
    
    def __eq__(self, other: object) -> bool:
        """Check equality with another card."""
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    @classmethod
    def from_string(cls, card_str: str) -> "Card":
        """
        Create a Card from string notation.
        
        Args:
            card_str: Card in format "Rs" where R is rank and s is suit
            
        Returns:
            Card instance
            
        Raises:
            ValueError: If card_str is invalid format
            
        Examples:
            >>> Card.from_string("As")
            Card(rank='A', suit='s')
        """
        if len(card_str) != 2:
            raise ValueError(f"Card string must be 2 characters, got: '{card_str}'")
        return cls(rank=card_str[0], suit=card_str[1])
    
    def to_eval7(self) -> "eval7.Card":
        """
        Convert to eval7 Card object.
        
        Returns:
            eval7.Card instance
            
        Raises:
            RuntimeError: If eval7 is not available
        """
        if not EVAL7_AVAILABLE:
            raise RuntimeError("eval7 library is not installed")
        return eval7.Card(str(self))


@dataclass
class Hand:
    """
    Represents a poker hand (hole cards).
    
    A hand contains exactly 2 cards for Texas Hold'em.
    
    Attributes:
        cards: List of exactly 2 Card objects
        
    Examples:
        >>> hand = Hand.from_strings(["As", "Kh"])
        >>> print(hand)
        [As, Kh]
    """
    cards: List[Card] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate hand has exactly 2 cards."""
        if len(self.cards) != 2:
            raise ValueError(f"Hand must contain exactly 2 cards, got {len(self.cards)}")
        if self.cards[0] == self.cards[1]:
            raise ValueError("Hand cannot contain duplicate cards")
    
    def __str__(self) -> str:
        """Return string representation of hand."""
        return f"[{', '.join(str(c) for c in self.cards)}]"
    
    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"Hand(cards={self.cards})"
    
    @classmethod
    def from_strings(cls, card_strings: List[str]) -> "Hand":
        """
        Create a Hand from list of card strings.
        
        Args:
            card_strings: List of 2 card strings (e.g., ["As", "Kh"])
            
        Returns:
            Hand instance
            
        Examples:
            >>> Hand.from_strings(["As", "Kh"])
            Hand(cards=[Card(rank='A', suit='s'), Card(rank='K', suit='h')])
        """
        cards = [Card.from_string(cs) for cs in card_strings]
        return cls(cards=cards)
    
    def to_eval7(self) -> List["eval7.Card"]:
        """Convert hand to list of eval7 Cards."""
        return [card.to_eval7() for card in self.cards]
    
    def to_strings(self) -> List[str]:
        """Return cards as list of strings."""
        return [str(c) for c in self.cards]


@dataclass
class Deck:
    """
    Represents a standard 52-card deck.
    
    Supports shuffling, dealing, and removing specific cards.
    
    Attributes:
        cards: List of Card objects in the deck
        
    Examples:
        >>> deck = Deck()
        >>> deck.shuffle()
        >>> card = deck.deal()
    """
    cards: List[Card] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Initialize full deck if empty."""
        if not self.cards:
            self._init_full_deck()
    
    def _init_full_deck(self) -> None:
        """Create a standard 52-card deck."""
        self.cards = []
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(rank=rank.value, suit=suit.value))
    
    def __len__(self) -> int:
        """Return number of cards remaining in deck."""
        return len(self.cards)
    
    def __str__(self) -> str:
        """Return string representation."""
        return f"Deck({len(self.cards)} cards)"
    
    def shuffle(self) -> None:
        """Shuffle the deck in place."""
        random.shuffle(self.cards)
    
    def deal(self, count: int = 1) -> List[Card]:
        """
        Deal cards from the top of the deck.
        
        Args:
            count: Number of cards to deal (default: 1)
            
        Returns:
            List of dealt cards
            
        Raises:
            ValueError: If not enough cards in deck
        """
        if count > len(self.cards):
            raise ValueError(f"Cannot deal {count} cards, only {len(self.cards)} remaining")
        dealt = self.cards[:count]
        self.cards = self.cards[count:]
        return dealt
    
    def remove_cards(self, cards_to_remove: List[Card]) -> None:
        """
        Remove specific cards from the deck.
        
        Args:
            cards_to_remove: Cards to remove from deck
            
        Raises:
            ValueError: If card not found in deck
        """
        for card in cards_to_remove:
            if card in self.cards:
                self.cards.remove(card)
            else:
                raise ValueError(f"Card {card} not in deck")
    
    def remove_card_strings(self, card_strings: List[str]) -> None:
        """
        Remove cards by string notation.
        
        Args:
            card_strings: List of card strings to remove (e.g., ["As", "Kh"])
        """
        cards = [Card.from_string(cs) for cs in card_strings]
        self.remove_cards(cards)
    
    def reset(self) -> None:
        """Reset deck to full 52 cards."""
        self._init_full_deck()


@dataclass
class EvaluationResult:
    """
    Result of a hand evaluation/comparison.
    
    Attributes:
        winner: 'hero', 'villain', or 'tie'
        hero_hand: Name of hero's best hand
        villain_hand: Name of villain's best hand
        hero_score: Numeric score for hero (lower is better in eval7)
        villain_score: Numeric score for villain
        description: Human-readable description of result
    """
    winner: Literal["hero", "villain", "tie"]
    hero_hand: str
    villain_hand: str
    hero_score: int
    villain_score: int
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "winner": self.winner,
            "hero_hand": self.hero_hand,
            "villain_hand": self.villain_hand,
            "hero_score": self.hero_score,
            "villain_score": self.villain_score,
            "description": self.description
        }


class PokerEngine:
    """
    Core poker engine for hand evaluation and winner determination.
    
    Uses the eval7 library for accurate poker hand evaluation.
    Provides methods for evaluating hands and determining winners.
    
    Attributes:
        deck: Internal deck instance for dealing cards
        
    Examples:
        >>> engine = PokerEngine()
        >>> result = engine.evaluate_winner(
        ...     hero_cards=["As", "Kh"],
        ...     villain_cards=["Qc", "Qd"],
        ...     board_cards=["Ah", "7c", "2d", "Js", "3h"]
        ... )
        >>> print(result.winner)
        'hero'
    """
    
    def __init__(self) -> None:
        """Initialize the poker engine."""
        self.deck = Deck()
    
    @staticmethod
    def _get_hand_type(score: int) -> str:
        """
        Get the hand type name from eval7 score.
        
        Args:
            score: eval7 hand score (lower is better)
            
        Returns:
            Hand type name (e.g., "Flush", "Pair")
        """
        if not EVAL7_AVAILABLE:
            return "Unknown"
        
        # Use eval7's built-in handtype function
        return eval7.handtype(score)
    
    @staticmethod
    def _parse_cards_to_eval7(card_strings: List[str]) -> List["eval7.Card"]:
        """
        Parse card strings to eval7 Card objects.
        
        Args:
            card_strings: List of card strings (e.g., ["As", "Kh"])
            
        Returns:
            List of eval7.Card objects
            
        Raises:
            RuntimeError: If eval7 is not available
            ValueError: If card format is invalid
        """
        if not EVAL7_AVAILABLE:
            raise RuntimeError("eval7 library is not installed. Install with: pip install eval7")
        
        try:
            return [eval7.Card(cs) for cs in card_strings]
        except Exception as e:
            raise ValueError(f"Invalid card format: {e}")
    
    def evaluate_winner(
        self,
        hero_cards: List[str],
        villain_cards: List[str],
        board_cards: List[str]
    ) -> EvaluationResult:
        """
        Evaluate and determine the winner between hero and villain.
        
        Compares the best 5-card hand each player can make using their
        hole cards and the community board cards.
        
        Args:
            hero_cards: Hero's hole cards (2 cards, e.g., ["As", "Kh"])
            villain_cards: Villain's hole cards (2 cards, e.g., ["Qc", "Qd"])
            board_cards: Community cards (5 cards, e.g., ["Ah", "7c", "2d", "Js", "3h"])
            
        Returns:
            EvaluationResult containing winner, hand types, and description
            
        Raises:
            ValueError: If card format is invalid or wrong number of cards
            RuntimeError: If eval7 is not available
            
        Examples:
            >>> engine = PokerEngine()
            >>> result = engine.evaluate_winner(
            ...     hero_cards=["As", "Kh"],
            ...     villain_cards=["Qc", "Qd"],
            ...     board_cards=["Ah", "7c", "2d", "Js", "3h"]
            ... )
            >>> result.winner
            'hero'
            >>> result.description
            'Hero wins with Pair'
        """
        # Validate input lengths
        if len(hero_cards) != 2:
            raise ValueError(f"Hero must have exactly 2 cards, got {len(hero_cards)}")
        if len(villain_cards) != 2:
            raise ValueError(f"Villain must have exactly 2 cards, got {len(villain_cards)}")
        if len(board_cards) != 5:
            raise ValueError(f"Board must have exactly 5 cards, got {len(board_cards)}")
        
        # Check for duplicate cards
        all_cards = hero_cards + villain_cards + board_cards
        if len(set(all_cards)) != len(all_cards):
            raise ValueError("Duplicate cards detected. All cards must be unique.")
        
        # Parse cards to eval7 format
        hero_eval7 = self._parse_cards_to_eval7(hero_cards)
        villain_eval7 = self._parse_cards_to_eval7(villain_cards)
        board_eval7 = self._parse_cards_to_eval7(board_cards)
        
        # Evaluate hands (HIGHER score is better in eval7)
        hero_score = eval7.evaluate(hero_eval7 + board_eval7)
        villain_score = eval7.evaluate(villain_eval7 + board_eval7)
        
        # Get hand type names
        hero_hand_type = self._get_hand_type(hero_score)
        villain_hand_type = self._get_hand_type(villain_score)
        
        # Determine winner (HIGHER score wins in eval7)
        if hero_score > villain_score:
            winner = "hero"
            description = f"Hero wins with {hero_hand_type}"
        elif villain_score > hero_score:
            winner = "villain"
            description = f"Villain wins with {villain_hand_type}"
        else:
            winner = "tie"
            description = f"Tie with {hero_hand_type}"
        
        return EvaluationResult(
            winner=winner,
            hero_hand=hero_hand_type,
            villain_hand=villain_hand_type,
            hero_score=hero_score,
            villain_score=villain_score,
            description=description
        )
    
    def evaluate_hand_strength(
        self,
        hole_cards: List[str],
        board_cards: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate the strength of a single hand.
        
        Args:
            hole_cards: Player's hole cards (2 cards)
            board_cards: Community cards (3-5 cards)
            
        Returns:
            Dictionary with hand type and score
        """
        if len(hole_cards) != 2:
            raise ValueError(f"Must have exactly 2 hole cards, got {len(hole_cards)}")
        if not 3 <= len(board_cards) <= 5:
            raise ValueError(f"Board must have 3-5 cards, got {len(board_cards)}")
        
        hole_eval7 = self._parse_cards_to_eval7(hole_cards)
        board_eval7 = self._parse_cards_to_eval7(board_cards)
        
        score = eval7.evaluate(hole_eval7 + board_eval7)
        hand_type = self._get_hand_type(score)
        
        return {
            "hole_cards": hole_cards,
            "board": board_cards,
            "hand_type": hand_type,
            "score": score
        }
    
    def deal_random_board(self, exclude_cards: Optional[List[str]] = None) -> List[str]:
        """
        Deal a random 5-card board.
        
        Args:
            exclude_cards: Cards to exclude from dealing (e.g., player hands)
            
        Returns:
            List of 5 card strings
        """
        self.deck.reset()
        if exclude_cards:
            self.deck.remove_card_strings(exclude_cards)
        self.deck.shuffle()
        dealt = self.deck.deal(5)
        return [str(card) for card in dealt]


# Module-level singleton for easy import
poker_engine = PokerEngine()
