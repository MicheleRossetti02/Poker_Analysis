#!/usr/bin/env python3
"""
GTO Ranges Generator

Generates a comprehensive GTO pre-flop ranges database based on
standard poker opening percentages for 6-max tables.

The script:
1. Defines all 169 starting hands ordered by strength (equity-based ranking)
2. Assigns opening/folding actions based on position percentages
3. Saves the complete database to data/gto_ranges.json

Usage:
    python scripts/generate_ranges.py
"""
import json
import os
from typing import Dict, List, Tuple
from pathlib import Path


# =============================================================================
# HAND RANKING
# All 169 unique starting hands ordered from strongest to weakest
# Based on preflop equity and playability (Sklansky-Malmuth adjusted)
# =============================================================================

def generate_all_hands() -> List[str]:
    """
    Generate all 169 unique starting hands in poker.
    
    Returns:
        List of all hands in format: AA, AKs, AKo, KK, etc.
    """
    ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    hands = []
    
    for i, r1 in enumerate(ranks):
        for j, r2 in enumerate(ranks):
            if i == j:
                # Pocket pair
                hands.append(f"{r1}{r2}")
            elif i < j:
                # Suited (higher rank first)
                hands.append(f"{r1}{r2}s")
            else:
                # Offsuit (higher rank first)
                hands.append(f"{r2}{r1}o")
    
    return hands


# Hand ranking based on pre-flop equity and playability
# This is a commonly accepted ordering based on Sklansky groups + equity
HAND_RANKING: List[str] = [
    # Tier 1 - Premium (Top 3%)
    "AA", "KK", "QQ", "AKs", "JJ",
    
    # Tier 2 - Strong (Top 6%)
    "AQs", "TT", "AKo", "AJs", "KQs", "99",
    
    # Tier 3 - Good (Top 10%)
    "ATs", "AQo", "KJs", "88", "QJs", "KTs", "A9s", "AJo",
    
    # Tier 4 - Playable (Top 15%)
    "77", "KQo", "QTs", "A8s", "K9s", "JTs", "A5s", "A7s",
    "KJo", "A4s", "A6s", "66", "QJo", "A3s",
    
    # Tier 5 - Marginal (Top 20%)
    "T9s", "55", "A2s", "KTo", "J9s", "Q9s", "ATo", "K8s",
    "QTo", "44", "98s", "JTo", "K7s",
    
    # Tier 6 - Speculative (Top 30%)
    "33", "87s", "Q8s", "T8s", "K6s", "76s", "J8s", "22",
    "K5s", "97s", "K4s", "65s", "K9o", "K3s", "86s", "T7s",
    "Q7s", "K2s", "54s", "Q9o", "75s", "J9o", "96s",
    
    # Tier 7 - Weak Suited (Top 40%)
    "64s", "J7s", "T9o", "Q6s", "85s", "53s", "A9o", "Q5s",
    "T6s", "74s", "98o", "Q4s", "43s", "J6s", "95s", "Q3s",
    "87o", "A8o", "63s", "Q2s", "J5s", "84s", "52s", "T8o",
    
    # Tier 8 - Weak (Top 50%)
    "76o", "97o", "J4s", "J8o", "A7o", "J3s", "73s", "T5s",
    "42s", "65o", "J2s", "A5o", "A6o", "86o", "54o", "T4s",
    "32s", "T3s", "75o", "96o", "A4o", "T2s", "Q8o",
    
    # Tier 9 - Very Weak (Top 60%)
    "64o", "A3o", "K8o", "85o", "Q7o", "T7o", "J7o", "53o",
    "A2o", "74o", "K7o", "95o", "Q6o", "43o", "K6o", "63o",
    "94s", "84o", "J6o", "T6o",
    
    # Tier 10 - Trash (Bottom 40%)
    "K5o", "52o", "93s", "Q5o", "K4o", "83s", "73o", "Q4o",
    "92s", "K3o", "42o", "82s", "Q3o", "K2o", "62s", "72s",
    "32o", "Q2o", "94o", "J5o", "93o", "J4o", "83o", "92o",
    "J3o", "82o", "J2o", "72o", "62o", "T5o", "T4o", "T3o",
    "T2o"
]


# =============================================================================
# POSITION RANGES
# Define opening/defending ranges for each position in 6-max
# =============================================================================

# Opening ranges by position (percentage of top hands to raise)
OPENING_RANGES: Dict[str, float] = {
    "UTG": 0.15,    # 15% - Very tight, ~25 hands
    "MP": 0.20,     # 20% - Tight, ~34 hands
    "CO": 0.30,     # 30% - Loose, ~50 hands
    "BTN": 0.50,    # 50% - Very loose, ~85 hands
    "SB": 0.40,     # 40% - Loose (steals), ~68 hands
}

# BB Defense ranges (vs different positions)
BB_DEFENSE_RANGES: Dict[str, Dict[str, float]] = {
    "vs_UTG": {"call": 0.10, "3bet": 0.05},      # Tight defense
    "vs_MP": {"call": 0.12, "3bet": 0.06},
    "vs_CO": {"call": 0.18, "3bet": 0.08},
    "vs_BTN": {"call": 0.25, "3bet": 0.12},      # Wider defense
    "vs_SB": {"call": 0.30, "3bet": 0.15},       # Widest defense vs SB
}

# Stack depth adjustments
STACK_DEPTHS = ["100bb", "50bb", "20bb"]


def get_hand_index(hand: str) -> int:
    """Get the index of a hand in the ranking (0 = best)."""
    try:
        return HAND_RANKING.index(hand)
    except ValueError:
        return len(HAND_RANKING)  # Unknown hand = worst


def get_ev_estimate(hand: str, position_strength: float) -> float:
    """
    Estimate EV for a hand based on ranking and position.
    
    Args:
        hand: Hand notation
        position_strength: Position multiplier (1.0 = BTN, 0.5 = UTG)
    
    Returns:
        Estimated EV in big blinds
    """
    index = get_hand_index(hand)
    total_hands = len(HAND_RANKING)
    
    # Base EV calculation (linear from +3 for AA to -1 for trash)
    percentile = 1 - (index / total_hands)
    base_ev = (percentile * 4) - 1  # Range: -1 to +3
    
    # Position adjustment
    ev = base_ev * position_strength
    
    return round(ev, 2)


def generate_opening_range(position: str, stack: str = "100bb") -> Dict[str, Dict]:
    """
    Generate opening range for a position.
    
    Args:
        position: Position name (UTG, MP, CO, BTN, SB)
        stack: Stack depth
        
    Returns:
        Dictionary of hands with actions
    """
    range_pct = OPENING_RANGES.get(position, 0.20)
    num_hands = int(len(HAND_RANKING) * range_pct)
    
    # Position strength for EV calculation
    position_strength = {
        "UTG": 0.6, "MP": 0.7, "CO": 0.85, "BTN": 1.0, "SB": 0.9
    }.get(position, 0.7)
    
    # Stack depth adjustments
    if stack == "20bb":
        # Short stack: tighter but more all-ins
        num_hands = int(num_hands * 0.7)
        action_type = "all_in" if position in ["BTN", "SB"] else "raise"
    elif stack == "50bb":
        num_hands = int(num_hands * 0.9)
        action_type = "raise"
    else:
        action_type = "raise"
    
    result = {}
    
    for i, hand in enumerate(HAND_RANKING):
        ev = get_ev_estimate(hand, position_strength)
        
        if i < num_hands:
            # In range - raise/all-in
            # Premium hands are pure raise, marginal hands might be mixed
            if i < num_hands * 0.5:
                # Strong hands - pure raise
                result[hand] = {
                    "action": action_type,
                    "frequency": 1.0,
                    "ev": max(ev, 0.1)
                }
            else:
                # Marginal hands - might be mixed
                freq = max(0.5, 1.0 - (i - num_hands * 0.5) / (num_hands * 0.5) * 0.5)
                result[hand] = {
                    "action": action_type,
                    "frequency": round(freq, 2),
                    "ev": max(ev, 0.0),
                    "alternative_action": "fold",
                    "alternative_frequency": round(1 - freq, 2)
                }
        else:
            # Out of range - fold
            result[hand] = {
                "action": "fold",
                "frequency": 1.0,
                "ev": round(min(ev, -0.1), 2)
            }
    
    return result


def generate_bb_defense_range(vs_position: str, stack: str = "100bb") -> Dict[str, Dict]:
    """
    Generate Big Blind defense range against a specific position.
    
    Args:
        vs_position: Attacking position
        stack: Stack depth
        
    Returns:
        Dictionary of hands with call/3bet/fold actions
    """
    defense = BB_DEFENSE_RANGES.get(f"vs_{vs_position}", {"call": 0.15, "3bet": 0.07})
    
    call_pct = defense["call"]
    three_bet_pct = defense["3bet"]
    
    num_3bet = int(len(HAND_RANKING) * three_bet_pct)
    num_call = int(len(HAND_RANKING) * call_pct)
    
    result = {}
    
    for i, hand in enumerate(HAND_RANKING):
        ev = get_ev_estimate(hand, 0.5)  # OOP penalty
        
        if i < num_3bet:
            # 3-bet range (polarized: value + some bluffs)
            result[hand] = {
                "action": "raise",  # 3-bet
                "frequency": 1.0 if i < num_3bet * 0.6 else 0.7,
                "ev": max(ev + 0.5, 0.2)
            }
        elif i < num_3bet + num_call:
            # Calling range
            result[hand] = {
                "action": "call",
                "frequency": 1.0 if i < num_3bet + num_call * 0.5 else 0.8,
                "ev": max(ev, -0.2)
            }
        else:
            # Fold
            result[hand] = {
                "action": "fold",
                "frequency": 1.0,
                "ev": round(min(ev, -0.3), 2)
            }
    
    return result


def generate_facing_raise_range(defender_pos: str, attacker_pos: str, stack: str = "100bb") -> Dict[str, Dict]:
    """
    Generate range for a player facing a raise (not BB specific).
    
    Args:
        defender_pos: Position facing the raise
        attacker_pos: Position who raised
        stack: Stack depth
        
    Returns:
        Dictionary of hands with call/3bet/fold actions
    """
    # Position strength affects calling/3bet range
    # Later positions can defend wider
    position_order = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
    
    defender_idx = position_order.index(defender_pos) if defender_pos in position_order else 3
    attacker_idx = position_order.index(attacker_pos) if attacker_pos in position_order else 2
    
    # Tighter ranges vs earlier position raises
    tightness = 1.0 - (attacker_idx * 0.12)  # UTG raise = tighter defense
    
    # Base defense percentages
    base_3bet = 0.06
    base_call = 0.10
    
    # Adjust based on position difference
    if defender_idx > attacker_idx:
        # IP vs raiser - can defend wider
        base_3bet *= 1.3
        base_call *= 1.4
    else:
        # OOP vs raiser - tighter
        base_3bet *= 0.8
        base_call *= 0.7
    
    # Apply tightness
    three_bet_pct = base_3bet * tightness
    call_pct = base_call * tightness
    
    num_3bet = int(len(HAND_RANKING) * three_bet_pct)
    num_call = int(len(HAND_RANKING) * call_pct)
    
    # Stack adjustments
    if stack == "20bb":
        num_3bet = int(num_3bet * 1.5)  # More 3bet/fold at short stacks
        num_call = int(num_call * 0.5)
    elif stack == "50bb":
        num_3bet = int(num_3bet * 1.2)
        num_call = int(num_call * 0.8)
    
    result = {}
    
    for i, hand in enumerate(HAND_RANKING):
        ev = get_ev_estimate(hand, 0.6)
        
        if i < num_3bet:
            result[hand] = {
                "action": "raise",
                "frequency": 1.0 if i < num_3bet * 0.5 else 0.7,
                "ev": max(ev + 0.3, 0.1)
            }
        elif i < num_3bet + num_call:
            result[hand] = {
                "action": "call",
                "frequency": 1.0 if i < num_3bet + num_call * 0.6 else 0.75,
                "ev": max(ev, -0.3)
            }
        else:
            result[hand] = {
                "action": "fold",
                "frequency": 1.0,
                "ev": round(min(ev, -0.2), 2)
            }
    
    return result


def generate_full_database() -> Dict:
    """
    Generate the complete GTO database for ALL scenarios.
    
    Returns:
        Complete database dictionary
    """
    database = {}
    positions = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
    
    # =============================================================================
    # 1. Opening ranges (RFI - Raise First In)
    # =============================================================================
    print("Generating RFI (opening) ranges...")
    for position in ["UTG", "MP", "CO", "BTN", "SB"]:
        scenario_key = f"{position}_open"
        database[scenario_key] = {}
        
        for stack in STACK_DEPTHS:
            database[scenario_key][stack] = generate_opening_range(position, stack)
            count = sum(1 for h in database[scenario_key][stack] 
                       if database[scenario_key][stack][h]['action'] != 'fold')
            print(f"  {scenario_key} @ {stack}: {count} hands")
    
    # =============================================================================
    # 2. ALL position vs position scenarios
    # =============================================================================
    print("\nGenerating ALL position vs position scenarios...")
    
    # Generate all possible combinations where attacker is earlier or same as defender
    for attacker in positions:
        for defender in positions:
            if attacker == defender:
                continue  # Can't face yourself
            
            scenario_key = f"{attacker}_vs_{defender}"
            database[scenario_key] = {}
            
            for stack in STACK_DEPTHS:
                if defender == "BB":
                    # BB has special defense ranges
                    database[scenario_key][stack] = generate_bb_defense_range(attacker, stack)
                else:
                    # Use facing raise logic for non-BB defenders
                    # But for RFI scenarios, use opening range
                    database[scenario_key][stack] = generate_opening_range(attacker, stack)
            
            range_data = database[scenario_key]["100bb"]
            actions = {
                "raise": sum(1 for h in range_data if range_data[h]['action'] == 'raise'),
                "call": sum(1 for h in range_data if range_data[h]['action'] == 'call'),
                "all_in": sum(1 for h in range_data if range_data[h]['action'] == 'all_in'),
            }
            print(f"  {scenario_key}: {actions.get('raise', 0) + actions.get('all_in', 0)} raise, "
                  f"{actions.get('call', 0)} call")
    
    # =============================================================================
    # 3. Facing raise scenarios (position faces another position's open)
    # =============================================================================
    print("\nGenerating facing raise defense ranges...")
    
    for defender in ["MP", "CO", "BTN", "SB"]:  # BB already covered above
        for attacker in positions:
            # Defender must be after attacker in position order (or SB facing BB)
            if defender == attacker:
                continue
            
            # Check if this is a valid "facing raise" scenario
            pos_order = {"UTG": 0, "MP": 1, "CO": 2, "BTN": 3, "SB": 4, "BB": 5}
            
            # Only create facing_raise if defender is after attacker
            if pos_order.get(defender, 0) > pos_order.get(attacker, 0):
                scenario_key = f"{defender}_faces_{attacker}"
                
                if scenario_key not in database:
                    database[scenario_key] = {}
                    
                    for stack in STACK_DEPTHS:
                        database[scenario_key][stack] = generate_facing_raise_range(
                            defender, attacker, stack
                        )
                    
                    range_data = database[scenario_key]["100bb"]
                    actions = {
                        "raise": sum(1 for h in range_data if range_data[h]['action'] == 'raise'),
                        "call": sum(1 for h in range_data if range_data[h]['action'] == 'call'),
                    }
                    print(f"  {scenario_key}: {actions['raise']} 3bet, {actions['call']} call")
    
    return database


def main():
    """Main function to generate and save the GTO database."""
    print("=" * 70)
    print("GTO RANGES GENERATOR - COMPREHENSIVE EDITION")
    print("=" * 70)
    print(f"\nTotal unique hands: {len(HAND_RANKING)}")
    print(f"Stack depths: {STACK_DEPTHS}")
    print(f"Positions: UTG, MP, CO, BTN, SB, BB")
    print()
    
    # Generate database
    database = generate_full_database()
    
    # Calculate statistics
    total_entries = sum(
        len(database[scenario][stack])
        for scenario in database
        for stack in database[scenario]
    )
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total scenarios: {len(database)}")
    print(f"Total entries: {total_entries:,}")
    print(f"Entries per scenario: ~{total_entries // len(database)}")
    
    # List all scenarios
    print("\nAll scenarios generated:")
    for i, scenario in enumerate(sorted(database.keys()), 1):
        stacks = list(database[scenario].keys())
        print(f"  {i:2}. {scenario} ({len(stacks)} stacks)")
    
    # Save to file
    output_dir = Path(__file__).parent.parent / "app" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "gto_ranges.json"
    
    with open(output_file, 'w') as f:
        json.dump(database, f, indent=2)
    
    print(f"\nDatabase saved to: {output_file}")
    print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")
    
    # Verify
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    print(f"Loaded {len(loaded)} scenarios")
    
    # Test some specific scenarios
    test_scenarios = ["CO_vs_SB", "CO_vs_BB", "BTN_vs_SB", "UTG_vs_BB", "SB_vs_BB"]
    print("\nSample scenarios:")
    for scenario in test_scenarios:
        if scenario in loaded:
            sample = loaded[scenario]["100bb"]
            aa_action = sample.get('AA', {}).get('action', 'N/A')
            print(f"  {scenario}: AA -> {aa_action}")
        else:
            print(f"  {scenario}: NOT FOUND")


if __name__ == "__main__":
    main()

