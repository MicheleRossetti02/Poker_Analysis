"""
GTO Analyzer API Routes

Endpoints for GTO spot analysis using lookup tables.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.gto_service import gto_service, GTOSuggestion

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class AnalyzeSpotRequest(BaseModel):
    """Request schema for spot analysis."""
    hero_position: str = Field(
        ...,
        description="Hero's position (BTN, SB, BB, UTG, MP, CO)",
        examples=["BTN"]
    )
    villain_position: str = Field(
        ...,
        description="Villain's position",
        examples=["BB"]
    )
    stack: int = Field(
        ...,
        gt=0,
        le=500,
        description="Stack size in big blinds",
        examples=[100]
    )
    hand: List[str] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Hero's hole cards",
        examples=[["Ah", "Ks"]]
    )


class AnalyzeSpotResponse(BaseModel):
    """Response schema for spot analysis."""
    hand: str = Field(..., description="Hand notation (e.g., 'AKs')")
    scenario: str = Field(..., description="Scenario key (e.g., 'BTN_vs_BB')")
    requested_stack: str = Field(..., description="Stack size requested by user (e.g., '33bb')")
    matched_stack: str = Field(..., description="Nearest available stack in database (e.g., '20bb')")
    stack: str = Field(..., description="Stack depth used for lookup (backward compat)")
    action: str = Field(..., description="Recommended action")
    frequency: float = Field(..., description="Frequency of action (0-1)")
    ev: float = Field(..., description="Expected value in BB")
    alternative_action: Optional[str] = Field(None, description="Alternative action for mixed strategy")
    alternative_frequency: Optional[float] = Field(None, description="Frequency of alternative")
    found_in_database: bool = Field(..., description="Whether hand was found in GTO database")


# =============================================================================
# Endpoints
# =============================================================================

@router.post("", response_model=AnalyzeSpotResponse)
async def analyze_spot(request: AnalyzeSpotRequest) -> AnalyzeSpotResponse:
    """
    Analyze a poker spot and get GTO recommendation.
    
    This endpoint looks up pre-calculated GTO strategies to provide
    instant recommendations without solver computation.
    
    **Stack Size Handling:**
    The system uses "nearest neighbor" logic. If you request stack=33,
    it will match to the closest available stack (20bb or 50bb).
    
    **Example Request:**
    ```json
    {
        "hero_position": "BTN",
        "villain_position": "BB",
        "stack": 33,
        "hand": ["Ah", "Ks"]
    }
    ```
    
    **Example Response:**
    ```json
    {
        "hand": "AKs",
        "scenario": "BTN_vs_BB",
        "requested_stack": "33bb",
        "matched_stack": "20bb",
        "stack": "20bb",
        "action": "raise",
        "frequency": 1.0,
        "ev": 1.8,
        "found_in_database": true
    }
    ```
    
    Args:
        request: Position info, stack size, and hole cards
        
    Returns:
        GTO action recommendation
    """
    try:
        # Validate position format
        valid_positions = {"BTN", "SB", "BB", "UTG", "MP", "CO"}
        hero_pos = request.hero_position.upper()
        villain_pos = request.villain_position.upper()
        
        if hero_pos not in valid_positions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid hero position '{request.hero_position}'. Must be one of: {valid_positions}"
            )
        if villain_pos not in valid_positions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid villain position '{request.villain_position}'. Must be one of: {valid_positions}"
            )
        
        # Analyze the spot
        result = gto_service.analyze_spot(
            hero_position=hero_pos,
            villain_position=villain_pos,
            stack=request.stack,
            cards=request.hand
        )
        
        suggestion = result["suggestion"]
        
        return AnalyzeSpotResponse(
            hand=result["hand"],
            scenario=result["scenario"],
            requested_stack=result.get("requested_stack", f"{request.stack}bb"),
            matched_stack=result.get("matched_stack", result["stack"]),
            stack=result["stack"],
            action=suggestion["action"],
            frequency=suggestion["frequency"],
            ev=suggestion["ev"],
            alternative_action=suggestion.get("alternative_action"),
            alternative_frequency=suggestion.get("alternative_frequency"),
            found_in_database=result["found_in_database"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.get("/scenarios")
async def get_available_scenarios():
    """
    Get list of available scenarios in the GTO database.
    
    Returns:
        List of scenario keys
    """
    return {
        "scenarios": gto_service.get_available_scenarios()
    }


@router.get("/stacks/{scenario}")
async def get_available_stacks(scenario: str):
    """
    Get available stack depths for a scenario.
    
    Args:
        scenario: Scenario key (e.g., "BTN_vs_BB")
        
    Returns:
        List of stack depth keys
    """
    stacks = gto_service.get_available_stacks(scenario)
    if not stacks:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{scenario}' not found"
        )
    return {
        "scenario": scenario,
        "stacks": stacks
    }
