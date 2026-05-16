"""
API endpoints for Zeus AI Agent - ANSI O5.1-2022 Expert
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

from backend.zeus_agent import ZeusAgent, ZeusResponse, QueryType


router = APIRouter(prefix="/api/zeus", tags=["Zeus AI Agent"])


# Pydantic models for API
class ZeusQueryRequest(BaseModel):
    """Request model for Zeus query"""
    question: str = Field(..., description="Question to ask Zeus")
    context: Optional[Dict] = Field(None, description="Optional context (pole data, measurements, etc.)")


class ZeusQueryResponse(BaseModel):
    """Response model for Zeus query"""
    query_type: str
    answer: str
    data: Optional[Dict] = None
    suggestions: Optional[List[str]] = None
    confidence: float


class ZeusCapabilitiesResponse(BaseModel):
    """Response model for Zeus capabilities"""
    capabilities: Dict[str, List[str]]
    description: str


# Initialize Zeus agent
zeus = ZeusAgent()


@router.post("/ask", response_model=ZeusQueryResponse)
async def ask_zeus(request: ZeusQueryRequest):
    """
    Ask Zeus a question about ANSI O5.1-2022
    
    Zeus can help with:
    - Pole specifications and dimensions
    - Load capacity calculations
    - Pole class comparisons
    - Recommendations for requirements
    - Compliance checking
    - Engineering calculations
    - Concept explanations
    
    Examples:
    - "What are the specifications for H1 40ft?"
    - "Recommend a pole for 12,000 lbs at 45ft"
    - "Compare poles at 40ft"
    - "Explain fiber stress"
    - "Calculate bending moment for 10,000 lbs at 30ft"
    """
    try:
        response = zeus.ask(request.question, request.context)
        
        return ZeusQueryResponse(
            query_type=response.query_type.value,
            answer=response.answer,
            data=response.data,
            suggestions=response.suggestions,
            confidence=response.confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zeus query failed: {str(e)}")


@router.get("/capabilities", response_model=ZeusCapabilitiesResponse)
async def get_capabilities():
    """
    Get Zeus's capabilities and what he can help with
    """
    capabilities = zeus.get_capabilities()
    
    return ZeusCapabilitiesResponse(
        capabilities=capabilities,
        description="Zeus is an AI expert on ANSI O5.1-2022 Wood Poles specifications. "
                   "He can answer questions, provide recommendations, perform calculations, "
                   "and explain concepts related to utility pole standards."
    )


@router.post("/specification")
async def get_specification(
    pole_class: str = Field(..., description="Pole class (e.g., H1, 1, 2)"),
    length_ft: float = Field(..., description="Pole length in feet")
):
    """
    Quick specification lookup via Zeus
    """
    question = f"What are the specifications for {pole_class} {length_ft}ft?"
    response = zeus.ask(question, {"pole_class": pole_class, "length_ft": length_ft})
    
    return {
        "answer": response.answer,
        "data": response.data
    }


@router.post("/recommend")
async def get_recommendation(
    required_load_lbs: float = Field(..., description="Required horizontal load in pounds"),
    length_ft: float = Field(..., description="Desired pole length in feet")
):
    """
    Get pole recommendation via Zeus
    """
    question = f"Recommend a pole for {required_load_lbs} lbs at {length_ft}ft"
    response = zeus.ask(
        question,
        {"required_load_lbs": required_load_lbs, "length_ft": length_ft}
    )
    
    return {
        "answer": response.answer,
        "data": response.data,
        "suggestions": response.suggestions
    }


@router.post("/compare")
async def compare_poles(
    length_ft: float = Field(..., description="Pole length in feet for comparison")
):
    """
    Compare pole classes via Zeus
    """
    question = f"Compare poles at {length_ft}ft"
    response = zeus.ask(question, {"length_ft": length_ft})
    
    return {
        "answer": response.answer,
        "data": response.data
    }


@router.post("/calculate/bending-moment")
async def calculate_bending_moment(
    load_lbs: float = Field(..., description="Horizontal load in pounds"),
    height_ft: float = Field(..., description="Height from groundline in feet")
):
    """
    Calculate bending moment via Zeus
    """
    question = f"Calculate bending moment for {load_lbs} lbs at {height_ft}ft"
    response = zeus.ask(
        question,
        {"load_lbs": load_lbs, "height_ft": height_ft}
    )
    
    return {
        "answer": response.answer,
        "data": response.data
    }


@router.post("/calculate/decay-strength")
async def calculate_decay_strength(
    diameter_inches: float = Field(..., description="Original diameter in inches"),
    decay_depth_inches: float = Field(..., description="Decay depth in inches")
):
    """
    Calculate strength reduction from decay via Zeus
    """
    question = f"Calculate strength loss from {decay_depth_inches} inches of decay on {diameter_inches} inch diameter"
    response = zeus.ask(
        question,
        {"diameter_inches": diameter_inches, "decay_depth_inches": decay_depth_inches}
    )
    
    return {
        "answer": response.answer,
        "data": response.data
    }


@router.post("/explain")
async def explain_concept(
    topic: str = Field(..., description="Topic to explain (e.g., 'fiber stress', 'pole classes', 'groundline')")
):
    """
    Get explanation of ANSI O5.1-2022 concepts via Zeus
    """
    question = f"Explain {topic}"
    response = zeus.ask(question)
    
    return {
        "answer": response.answer,
        "suggestions": response.suggestions
    }


@router.get("/health")
async def health_check():
    """Health check endpoint for Zeus"""
    return {
        "status": "healthy",
        "agent": "Zeus - ANSI O5.1-2022 Expert",
        "version": "1.0",
        "capabilities": len(zeus.get_capabilities())
    }


@router.get("/examples")
async def get_examples():
    """Get example questions to ask Zeus"""
    return {
        "examples": [
            {
                "category": "Specifications",
                "questions": [
                    "What are the specifications for H1 40ft?",
                    "Show me Class 2 45ft dimensions",
                    "What is the load capacity of H3 50ft?",
                    "List all available pole classes"
                ]
            },
            {
                "category": "Comparisons",
                "questions": [
                    "Compare poles at 40ft",
                    "What's the difference between H1 and H2?",
                    "Compare Class 1 and Class 2 at 45ft"
                ]
            },
            {
                "category": "Recommendations",
                "questions": [
                    "Recommend a pole for 12,000 lbs at 45ft",
                    "What pole do I need for 15,000 lbs at 40ft?",
                    "Suggest the best pole for my application"
                ]
            },
            {
                "category": "Calculations",
                "questions": [
                    "Calculate bending moment for 10,000 lbs at 30ft",
                    "Calculate strength loss from 1.5 inches of decay on 11 inch diameter",
                    "What is the fiber stress for my pole?"
                ]
            },
            {
                "category": "Explanations",
                "questions": [
                    "What is ANSI O5.1-2022?",
                    "Explain fiber stress",
                    "What are pole classes?",
                    "Tell me about groundline",
                    "Explain safety factors"
                ]
            }
        ]
    }


@router.post("/conversation")
async def conversation(
    messages: List[Dict[str, str]] = Field(..., description="Conversation history")
):
    """
    Have a conversation with Zeus (maintains context)
    
    Format: [{"role": "user", "content": "question"}, {"role": "zeus", "content": "answer"}, ...]
    """
    if not messages or messages[-1]["role"] != "user":
        raise HTTPException(status_code=400, detail="Last message must be from user")
    
    # Extract context from conversation history
    context = {}
    for msg in messages[:-1]:
        if msg["role"] == "zeus" and "data" in msg:
            context.update(msg.get("data", {}))
    
    # Get response from Zeus
    question = messages[-1]["content"]
    response = zeus.ask(question, context if context else None)
    
    return {
        "role": "zeus",
        "content": response.answer,
        "data": response.data,
        "suggestions": response.suggestions,
        "confidence": response.confidence
    }

# Made with Bob
