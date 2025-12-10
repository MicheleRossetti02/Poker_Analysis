"""
Equity Calculation API Routes

Endpoints for calculating poker hand equity.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.models.schemas import PreflopEquityRequest, EquityResult
from app.services.equity_calculator import equity_calculator

router = APIRouter()


# =============================================================================
# Request/Response Models for Monte Carlo Endpoint
# =============================================================================

class MonteCarloEquityRequest(BaseModel):
    """Request schema for Monte Carlo equity calculation."""
    hero_hand: List[str] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Hero's hole cards (2 cards)",
        examples=[["As", "Kd"]]
    )
    villain_hand: List[str] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Villain's hole cards (2 cards)",
        examples=[["Qh", "Qc"]]
    )
    board: Optional[List[str]] = Field(
        default=[],
        max_length=5,
        description="Community cards (0-5 cards). Empty for pre-flop.",
        examples=[["Ah", "7c", "2d"]]
    )
    iterations: Optional[int] = Field(
        default=5000,
        ge=100,
        le=50000,
        description="Number of Monte Carlo iterations"
    )


class MonteCarloEquityResponse(BaseModel):
    """Response schema for Monte Carlo equity calculation."""
    hero_equity: float = Field(..., description="Hero win probability (0.0-1.0)")
    villain_equity: float = Field(..., description="Villain win probability (0.0-1.0)")
    tie_percentage: float = Field(default=0.0, description="Tie probability (0.0-1.0)")
    hero_wins: int = Field(..., description="Number of hero wins in simulation")
    villain_wins: int = Field(..., description="Number of villain wins in simulation")
    ties: int = Field(default=0, description="Number of ties in simulation")
    iterations: int = Field(..., description="Total iterations performed")
    hero_hand: List[str]
    villain_hand: List[str]
    board: List[str]


# =============================================================================
# Endpoints
# =============================================================================

@router.post("", response_model=MonteCarloEquityResponse)
async def calculate_equity(request: MonteCarloEquityRequest) -> MonteCarloEquityResponse:
    """
    Calculate equity between two poker hands using Monte Carlo simulation.
    
    This is the main equity calculation endpoint. It handles both pre-flop
    (empty board) and post-flop scenarios automatically.
    
    **Examples:**
    - Pre-flop: `{"hero_hand": ["As", "Kd"], "villain_hand": ["Qh", "Qc"], "board": []}`
    - Flop: `{"hero_hand": ["As", "Kd"], "villain_hand": ["Qh", "Qc"], "board": ["Ah", "7c", "2d"]}`
    
    **Returns:**
    - `hero_equity`: Probability hero wins (0.0 to 1.0)
    - `villain_equity`: Probability villain wins (0.0 to 1.0)
    
    Args:
        request: Hero hand, villain hand, board (optional), iterations
        
    Returns:
        Equity percentages and simulation statistics
    """
    try:
        result = equity_calculator.calculate_monte_carlo(
            hero_hand=request.hero_hand,
            villain_hand=request.villain_hand,
            board=request.board if request.board else [],
            iterations=request.iterations
        )
        
        return MonteCarloEquityResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/preflop", response_model=EquityResult)
async def calculate_preflop_equity(request: PreflopEquityRequest) -> EquityResult:
    """
    Calculate pre-flop equity between two poker hands.
    
    This endpoint uses Monte Carlo simulation to determine the winning
    probability of each hand when all 5 community cards are dealt.
    
    **Example:**
    - AKs vs QQ: ~43% vs ~57%
    - AA vs KK: ~82% vs ~18%
    - AKo vs 22: ~48% vs ~52%
    
    Args:
        request: Hero and villain cards with optional iteration count
        
    Returns:
        Equity percentages for both players and hand names
    """
    try:
        # Validate cards are different
        all_cards = request.hero_cards + request.villain_cards
        if len(set(all_cards)) != 4:
            raise HTTPException(
                status_code=400,
                detail="All cards must be unique. Same card cannot appear twice."
            )
        
        # Calculate equity
        result = equity_calculator.calculate_preflop_equity(
            hero_cards=request.hero_cards,
            villain_cards=request.villain_cards,
            iterations=request.iterations
        )
        
        return EquityResult(**result)
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid card format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/postflop")
async def calculate_postflop_equity(
    hero_cards: list[str],
    villain_cards: list[str],
    board: list[str],
    iterations: int = 10000
):
    """
    Calculate post-flop equity with known board cards.
    
    Args:
        hero_cards: Hero's hole cards (2 cards)
        villain_cards: Villain's hole cards (2 cards)
        board: Community cards (3-5 cards)
        iterations: Monte Carlo iterations
        
    Returns:
        Equity percentages with current board
    """
    try:
        # Validate card uniqueness
        all_cards = hero_cards + villain_cards + board
        if len(set(all_cards)) != len(all_cards):
            raise HTTPException(
                status_code=400,
                detail="All cards must be unique."
            )
        
        result = equity_calculator.calculate_postflop_equity(
            hero_cards=hero_cards,
            villain_cards=villain_cards,
            board=board,
            iterations=iterations
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid card format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

