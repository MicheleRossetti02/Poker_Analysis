"""
GTO Lookup Service

Provides pre-calculated GTO strategies via lookup tables.
This is much faster than real-time solver calculations.

The service uses a nested dictionary structure:
- Scenario (e.g., "BTN_vs_BB")
- Stack Depth (e.g., "100bb")
- Hand (e.g., "AA", "AKs", "72o")
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class GTOAction(str, Enum):
    """Possible GTO actions."""
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"
    CHECK = "check"
    BET = "bet"


@dataclass
class GTOSuggestion:
    """
    GTO suggestion for a specific spot.
    
    Attributes:
        action: Recommended action
        frequency: How often this action should be taken (0.0-1.0)
        ev: Expected value in big blinds
        alternative_action: Secondary action for mixed strategy
        alternative_frequency: Frequency of alternative action
    """
    action: str
    frequency: float
    ev: float
    alternative_action: Optional[str] = None
    alternative_frequency: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "action": self.action,
            "frequency": self.frequency,
            "ev": self.ev
        }
        if self.alternative_action:
            result["alternative_action"] = self.alternative_action
            result["alternative_frequency"] = self.alternative_frequency
        return result


# =============================================================================
# GTO DATABASE LOADER
# Loads pre-calculated strategies from JSON file
# =============================================================================

def load_gto_database() -> Dict[str, Dict[str, Dict[str, Dict]]]:
    """
    Load GTO database from JSON file.
    
    Returns:
        Complete GTO database dictionary
    """
    # Find the JSON file
    current_dir = Path(__file__).parent
    json_path = current_dir.parent / "data" / "gto_ranges.json"
    
    if json_path.exists():
        with open(json_path, 'r') as f:
            return json.load(f)
    else:
        # Return empty database if file not found
        print(f"Warning: GTO database not found at {json_path}")
        return {}


# Load database on module import
GTO_DATABASE = load_gto_database()

# Default suggestion for unknown hands
DEFAULT_SUGGESTION = GTOSuggestion(
    action="fold",
    frequency=1.0,
    ev=0.0
)


class GTOService:
    """
    GTO Lookup Service for pre-calculated poker strategies.
    
    This service provides GTO recommendations by looking up pre-calculated
    strategies in a database, rather than computing them in real-time.
    
    Usage:
        service = GTOService()
        suggestion = service.get_suggestion(
            scenario="BTN_vs_BB",
            stack="100bb",
            hand="AKs"
        )
    """
    
    def __init__(self, database: Dict = None):
        """
        Initialize GTO Service.
        
        Args:
            database: Optional custom database. Uses GTO_DATABASE if None.
        """
        self.database = database or GTO_DATABASE
    
    @staticmethod
    def cards_to_hand_notation(cards: List[str]) -> str:
        """
        Convert card list to standard hand notation.
        
        Converts ["Ah", "Ks"] -> "AKs" (suited)
        Converts ["Ah", "Kd"] -> "AKo" (offsuit)
        Converts ["Ah", "As"] -> "AA" (pair)
        
        Args:
            cards: List of 2 card strings (e.g., ["Ah", "Ks"])
            
        Returns:
            Hand notation string (e.g., "AKs", "AA", "72o")
            
        Raises:
            ValueError: If cards list is invalid
        """
        if len(cards) != 2:
            raise ValueError(f"Expected 2 cards, got {len(cards)}")
        
        # Extract ranks and suits
        rank1, suit1 = cards[0][0], cards[0][1]
        rank2, suit2 = cards[1][0], cards[1][1]
        
        # Rank ordering for sorting (higher ranks first)
        rank_order = "AKQJT98765432"
        
        # Sort ranks so higher rank comes first
        if rank_order.index(rank1) > rank_order.index(rank2):
            rank1, rank2 = rank2, rank1
            suit1, suit2 = suit2, suit1
        
        # Pocket pair
        if rank1 == rank2:
            return f"{rank1}{rank2}"
        
        # Suited or offsuit
        suited = "s" if suit1 == suit2 else "o"
        return f"{rank1}{rank2}{suited}"
    
    @staticmethod
    def build_scenario_key(hero_position: str, villain_position: str) -> str:
        """
        Build scenario key from positions.
        
        Args:
            hero_position: Hero's position (e.g., "BTN")
            villain_position: Villain's position (e.g., "BB")
            
        Returns:
            Scenario key (e.g., "BTN_vs_BB")
        """
        return f"{hero_position.upper()}_vs_{villain_position.upper()}"
    
    def stack_to_key(self, stack: int, scenario: str = None) -> str:
        """
        Convert stack size to nearest available lookup key.
        
        Uses "nearest neighbor" logic to find the closest available
        stack depth in the database.
        
        Args:
            stack: Stack size in big blinds (any integer)
            scenario: Optional scenario to check available stacks
            
        Returns:
            Stack key (e.g., "100bb", "50bb", "20bb")
        """
        # Standard stack depths
        standard_stacks = [20, 50, 100]
        
        # If scenario provided, get actual available stacks
        if scenario and scenario in self.database:
            available_keys = list(self.database[scenario].keys())
            # Parse "100bb" -> 100
            available_stacks = []
            for key in available_keys:
                try:
                    val = int(key.replace("bb", ""))
                    available_stacks.append(val)
                except ValueError:
                    pass
            if available_stacks:
                standard_stacks = available_stacks
        
        # Find nearest stack using minimum distance
        # If equidistant, prefer the smaller (more conservative) stack
        nearest_stack = min(standard_stacks, key=lambda x: (abs(x - stack), x))
        
        return f"{nearest_stack}bb"
    
    def get_suggestion(
        self,
        scenario: str,
        stack: str,
        hand: str
    ) -> GTOSuggestion:
        """
        Get GTO suggestion for a specific spot.
        
        Args:
            scenario: Scenario key (e.g., "BTN_vs_BB")
            stack: Stack depth key (e.g., "100bb")
            hand: Hand notation (e.g., "AKs")
            
        Returns:
            GTOSuggestion with recommended action
        """
        try:
            data = self.database[scenario][stack][hand]
            return GTOSuggestion(
                action=data["action"],
                frequency=data["frequency"],
                ev=data["ev"],
                alternative_action=data.get("alternative_action"),
                alternative_frequency=data.get("alternative_frequency")
            )
        except KeyError:
            # Hand not found - return default fold
            return DEFAULT_SUGGESTION
    
    def analyze_spot(
        self,
        hero_position: str,
        villain_position: str,
        stack: int,
        cards: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze a poker spot and return GTO recommendation.
        
        This is the main entry point for spot analysis.
        
        Args:
            hero_position: Hero's position (e.g., "BTN")
            villain_position: Villain's position (e.g., "BB")
            stack: Stack size in big blinds
            cards: Hero's hole cards (e.g., ["Ah", "Ks"])
            
        Returns:
            Dictionary with suggestion and metadata
        """
        # Convert cards to hand notation
        hand_notation = self.cards_to_hand_notation(cards)
        
        # Build scenario key
        scenario = self.build_scenario_key(hero_position, villain_position)
        
        # Convert stack to key (uses nearest neighbor logic)
        stack_key = self.stack_to_key(stack, scenario)
        
        # Get suggestion
        suggestion = self.get_suggestion(scenario, stack_key, hand_notation)
        
        return {
            "hand": hand_notation,
            "scenario": scenario,
            "stack": stack_key,
            "suggestion": suggestion.to_dict(),
            "found_in_database": suggestion != DEFAULT_SUGGESTION
        }
    
    def get_available_scenarios(self) -> List[str]:
        """Get list of available scenarios in database."""
        return list(self.database.keys())
    
    def get_available_stacks(self, scenario: str) -> List[str]:
        """Get available stack depths for a scenario."""
        if scenario in self.database:
            return list(self.database[scenario].keys())
        return []


# Singleton instance
gto_service = GTOService()
