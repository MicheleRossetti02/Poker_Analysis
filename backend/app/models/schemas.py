"""
Pydantic Schemas for Poker SaaS API

Defines all request/response models including the Hand data structure.
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class Position(str, Enum):
    """Poker table positions."""
    BTN = "BTN"  # Button
    SB = "SB"    # Small Blind
    BB = "BB"    # Big Blind
    UTG = "UTG"  # Under the Gun
    MP = "MP"    # Middle Position
    CO = "CO"    # Cut Off


class Street(str, Enum):
    """Betting rounds."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


class Action(str, Enum):
    """Possible poker actions."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


# =============================================================================
# Card Schemas
# =============================================================================

class Card(BaseModel):
    """
    Single card representation.
    
    Format: rank + suit (e.g., "As" = Ace of spades, "Kh" = King of hearts)
    Ranks: 2-9, T (10), J, Q, K, A
    Suits: s (spades), h (hearts), d (diamonds), c (clubs)
    """
    card: str = Field(
        ..., 
        min_length=2, 
        max_length=2,
        pattern=r'^[2-9TJQKA][shdc]$',
        examples=["As", "Kh", "Qd", "Jc", "Ts"]
    )


# =============================================================================
# Equity Calculation Schemas
# =============================================================================

class PreflopEquityRequest(BaseModel):
    """Request schema for pre-flop equity calculation."""
    hero_cards: List[str] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Hero's hole cards (2 cards)",
        examples=[["As", "Kh"]]
    )
    villain_cards: List[str] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Villain's hole cards (2 cards)",
        examples=[["Qc", "Qd"]]
    )
    iterations: Optional[int] = Field(
        default=10000,
        ge=1000,
        le=100000,
        description="Monte Carlo simulation iterations"
    )


class EquityResult(BaseModel):
    """Response schema for equity calculation."""
    hero_cards: List[str]
    villain_cards: List[str]
    hero_equity: float = Field(..., description="Hero win percentage (0-100)")
    villain_equity: float = Field(..., description="Villain win percentage (0-100)")
    tie_percentage: float = Field(..., description="Tie percentage (0-100)")
    iterations: int
    hero_hand_name: str = Field(..., description="Name of hero's hand (e.g., 'Ace-King suited')")
    villain_hand_name: str = Field(..., description="Name of villain's hand (e.g., 'Pocket Queens')")


# =============================================================================
# Hand Analysis Schemas (Full Hand Representation)
# =============================================================================

class OptimalAction(BaseModel):
    """GTO optimal action recommendation."""
    action: Action
    fold_pct: float = Field(..., ge=0, le=100)
    call_pct: float = Field(..., ge=0, le=100)
    raise_pct: float = Field(..., ge=0, le=100)
    ev: float = Field(..., description="Expected Value of the action")


class PlayerState(BaseModel):
    """State of a player in a hand."""
    position: Position
    cards: Optional[List[str]] = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Player's hole cards (null if unknown)"
    )
    stack_size: float = Field(..., gt=0, description="Stack size in big blinds")
    range: Optional[List[str]] = Field(
        default=None,
        description="Player's estimated range (e.g., ['AA', 'KK', 'QQ', 'AKs'])"
    )


class HandAnalysis(BaseModel):
    """
    Complete Hand representation for analysis.
    
    This is the core JSON model that represents a poker hand
    with all necessary information for GTO analysis.
    """
    hand_id: Optional[str] = Field(default=None, description="Unique hand identifier")
    street: Street
    pot_size: float = Field(..., gt=0, description="Current pot size in big blinds")
    pot_odds: Optional[float] = Field(default=None, description="Pot odds ratio")
    hero: PlayerState
    villain: PlayerState
    board: Optional[List[str]] = Field(
        default=None,
        max_length=5,
        description="Community cards (empty for preflop, 3 for flop, 4 for turn, 5 for river)"
    )
    optimal_action: Optional[OptimalAction] = None
    advice: Optional[str] = Field(
        default=None,
        description="Human-readable advice for the situation"
    )


# =============================================================================
# Scenario Simulator Schemas
# =============================================================================

class ScenarioRequest(BaseModel):
    """Request schema for the Tavolo Reale (Scenario Simulator)."""
    dealer_position: Position
    hero_position: Position
    villain_position: Position
    hero_cards: List[str] = Field(..., min_length=2, max_length=2)
    villain_cards: Optional[List[str]] = Field(default=None, min_length=2, max_length=2)
    board: Optional[List[str]] = Field(default=None, max_length=5)
    hero_stack: float = Field(..., gt=0, description="Hero stack in BB")
    villain_stack: float = Field(..., gt=0, description="Villain stack in BB")
    pot_size: float = Field(..., gt=0, description="Current pot in BB")


class ScenarioResponse(BaseModel):
    """Response schema for scenario analysis."""
    optimal_action: OptimalAction
    ev: float
    advice: str
    equity: float = Field(..., description="Hero's equity percentage")
