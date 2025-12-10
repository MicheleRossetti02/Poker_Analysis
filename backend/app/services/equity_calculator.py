"""
Poker Equity Calculator Service

Uses the treys library for hand evaluation and Monte Carlo simulation
for equity calculation between two poker hands.
"""
from typing import List, Tuple, Dict
from treys import Card, Evaluator, Deck
import random


class EquityCalculator:
    """
    Calculates equity between poker hands using Monte Carlo simulation.
    """
    
    def __init__(self):
        self.evaluator = Evaluator()
    
    @staticmethod
    def parse_card(card_str: str) -> int:
        """
        Convert card string to treys Card integer.
        
        Args:
            card_str: Card in format "As" (Ace of spades)
            
        Returns:
            Treys card integer representation
        """
        return Card.new(card_str)
    
    @staticmethod
    def parse_cards(cards: List[str]) -> List[int]:
        """Convert list of card strings to treys format."""
        return [EquityCalculator.parse_card(c) for c in cards]
    
    @staticmethod
    def get_hand_name(cards: List[str]) -> str:
        """
        Get human-readable name for a starting hand.
        
        Args:
            cards: Two hole cards in string format
            
        Returns:
            Hand name like "Pocket Aces" or "Ace-King suited"
        """
        rank_names = {
            'A': 'Ace', 'K': 'King', 'Q': 'Queen', 'J': 'Jack', 'T': 'Ten',
            '9': 'Nine', '8': 'Eight', '7': 'Seven', '6': 'Six', '5': 'Five',
            '4': 'Four', '3': 'Three', '2': 'Two'
        }
        
        rank1, suit1 = cards[0][0], cards[0][1]
        rank2, suit2 = cards[1][0], cards[1][1]
        
        # Pocket pair
        if rank1 == rank2:
            return f"Pocket {rank_names[rank1]}s"
        
        # Sort by rank (higher first)
        rank_order = 'AKQJT98765432'
        if rank_order.index(rank1) > rank_order.index(rank2):
            rank1, rank2 = rank2, rank1
            suit1, suit2 = suit2, suit1
        
        suited = "suited" if suit1 == suit2 else "offsuit"
        return f"{rank_names[rank1]}-{rank_names[rank2]} {suited}"
    
    def calculate_preflop_equity(
        self,
        hero_cards: List[str],
        villain_cards: List[str],
        iterations: int = 10000
    ) -> Dict:
        """
        Calculate pre-flop equity between two hands using Monte Carlo simulation.
        
        Args:
            hero_cards: Hero's two hole cards
            villain_cards: Villain's two hole cards
            iterations: Number of simulations to run
            
        Returns:
            Dict with equity percentages for both players
        """
        hero_wins = 0
        villain_wins = 0
        ties = 0
        
        # Parse cards
        hero_hand = self.parse_cards(hero_cards)
        villain_hand = self.parse_cards(villain_cards)
        
        # Cards that cannot appear on the board
        dead_cards = set(hero_hand + villain_hand)
        
        for _ in range(iterations):
            # Create a fresh deck and remove known cards
            deck = Deck()
            deck.cards = [c for c in deck.cards if c not in dead_cards]
            
            # Draw 5 community cards
            random.shuffle(deck.cards)
            board = deck.cards[:5]
            
            # Evaluate hands
            hero_score = self.evaluator.evaluate(board, hero_hand)
            villain_score = self.evaluator.evaluate(board, villain_hand)
            
            # Lower score is better in treys
            if hero_score < villain_score:
                hero_wins += 1
            elif villain_score < hero_score:
                villain_wins += 1
            else:
                ties += 1
        
        # Calculate percentages
        hero_equity = (hero_wins / iterations) * 100
        villain_equity = (villain_wins / iterations) * 100
        tie_percentage = (ties / iterations) * 100
        
        return {
            "hero_cards": hero_cards,
            "villain_cards": villain_cards,
            "hero_equity": round(hero_equity, 2),
            "villain_equity": round(villain_equity, 2),
            "tie_percentage": round(tie_percentage, 2),
            "iterations": iterations,
            "hero_hand_name": self.get_hand_name(hero_cards),
            "villain_hand_name": self.get_hand_name(villain_cards)
        }
    
    def calculate_postflop_equity(
        self,
        hero_cards: List[str],
        villain_cards: List[str],
        board: List[str],
        iterations: int = 10000
    ) -> Dict:
        """
        Calculate post-flop equity with known board cards.
        
        Args:
            hero_cards: Hero's two hole cards
            villain_cards: Villain's two hole cards
            board: Current board cards (3-5 cards)
            iterations: Number of simulations to run
            
        Returns:
            Dict with equity percentages
        """
        hero_wins = 0
        villain_wins = 0
        ties = 0
        
        # Parse cards
        hero_hand = self.parse_cards(hero_cards)
        villain_hand = self.parse_cards(villain_cards)
        board_cards = self.parse_cards(board)
        
        # Cards that cannot appear on the board
        dead_cards = set(hero_hand + villain_hand + board_cards)
        remaining_board_cards = 5 - len(board_cards)
        
        for _ in range(iterations):
            # Create deck without known cards
            deck = Deck()
            deck.cards = [c for c in deck.cards if c not in dead_cards]
            
            # Draw remaining community cards
            random.shuffle(deck.cards)
            full_board = board_cards + deck.cards[:remaining_board_cards]
            
            # Evaluate hands
            hero_score = self.evaluator.evaluate(full_board, hero_hand)
            villain_score = self.evaluator.evaluate(full_board, villain_hand)
            
            if hero_score < villain_score:
                hero_wins += 1
            elif villain_score < hero_score:
                villain_wins += 1
            else:
                ties += 1
        
        hero_equity = (hero_wins / iterations) * 100
        villain_equity = (villain_wins / iterations) * 100
        tie_percentage = (ties / iterations) * 100
        
        return {
            "hero_cards": hero_cards,
            "villain_cards": villain_cards,
            "board": board,
            "hero_equity": round(hero_equity, 2),
            "villain_equity": round(villain_equity, 2),
            "tie_percentage": round(tie_percentage, 2),
            "iterations": iterations,
            "hero_hand_name": self.get_hand_name(hero_cards),
            "villain_hand_name": self.get_hand_name(villain_cards)
        }
    
    def calculate_monte_carlo(
        self,
        hero_hand: List[str],
        villain_hand: List[str],
        board: List[str] = None,
        iterations: int = 5000
    ) -> Dict:
        """
        Calculate equity using Monte Carlo simulation.
        
        This is the main method for equity calculation. It handles both
        pre-flop (empty board) and post-flop scenarios automatically.
        
        Args:
            hero_hand: Hero's hole cards as strings (e.g., ["As", "Kd"])
            villain_hand: Villain's hole cards as strings (e.g., ["Qh", "Qc"])
            board: Community cards (0-5 cards). Empty list or None for pre-flop.
            iterations: Number of Monte Carlo iterations (default: 5000)
            
        Returns:
            Dict containing:
                - hero_equity: Hero's winning percentage (0.0-1.0)
                - villain_equity: Villain's winning percentage (0.0-1.0)
                - tie_percentage: Tie percentage (0.0-1.0)
                - hero_wins: Number of hero wins
                - villain_wins: Number of villain wins
                - ties: Number of ties
                - iterations: Total iterations run
                
        Raises:
            ValueError: If card format is invalid or cards overlap
            
        Example:
            >>> calc = EquityCalculator()
            >>> result = calc.calculate_monte_carlo(
            ...     hero_hand=["As", "Kd"],
            ...     villain_hand=["Qh", "Qc"],
            ...     board=["Ah", "7c", "2d"]
            ... )
            >>> print(f"Hero equity: {result['hero_equity']:.2%}")
        """
        # Normalize board input
        if board is None:
            board = []
        
        # Validate inputs
        if len(hero_hand) != 2:
            raise ValueError(f"Hero must have exactly 2 cards, got {len(hero_hand)}")
        if len(villain_hand) != 2:
            raise ValueError(f"Villain must have exactly 2 cards, got {len(villain_hand)}")
        if len(board) > 5:
            raise ValueError(f"Board cannot have more than 5 cards, got {len(board)}")
        
        # Check for duplicate cards
        all_cards = hero_hand + villain_hand + board
        if len(set(all_cards)) != len(all_cards):
            raise ValueError("Duplicate cards detected. All cards must be unique.")
        
        # Parse cards to treys format
        try:
            hero_cards_int = self.parse_cards(hero_hand)
            villain_cards_int = self.parse_cards(villain_hand)
            board_cards_int = self.parse_cards(board) if board else []
        except KeyError as e:
            raise ValueError(f"Invalid card format: {e}")
        
        # Dead cards (cannot appear on board)
        dead_cards = set(hero_cards_int + villain_cards_int + board_cards_int)
        
        # Number of cards to deal to complete the board
        cards_to_deal = 5 - len(board_cards_int)
        
        # Pre-calculate deck without dead cards for efficiency
        full_deck = Deck()
        available_cards = [c for c in full_deck.cards if c not in dead_cards]
        
        # Counters
        hero_wins = 0
        villain_wins = 0
        ties = 0
        
        # Monte Carlo simulation
        for _ in range(iterations):
            # Shuffle and deal remaining board cards
            random.shuffle(available_cards)
            complete_board = board_cards_int + available_cards[:cards_to_deal]
            
            # Evaluate hands (lower score is better in treys)
            hero_score = self.evaluator.evaluate(complete_board, hero_cards_int)
            villain_score = self.evaluator.evaluate(complete_board, villain_cards_int)
            
            # Compare scores
            if hero_score < villain_score:
                hero_wins += 1
            elif villain_score < hero_score:
                villain_wins += 1
            else:
                ties += 1
        
        # Calculate equity as decimal (0.0 - 1.0)
        hero_equity = hero_wins / iterations
        villain_equity = villain_wins / iterations
        tie_pct = ties / iterations
        
        return {
            "hero_equity": round(hero_equity, 4),
            "villain_equity": round(villain_equity, 4),
            "tie_percentage": round(tie_pct, 4),
            "hero_wins": hero_wins,
            "villain_wins": villain_wins,
            "ties": ties,
            "iterations": iterations,
            "hero_hand": hero_hand,
            "villain_hand": villain_hand,
            "board": board
        }


# Singleton instance
equity_calculator = EquityCalculator()

