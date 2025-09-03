"""
Pydantic schemas for PLS evaluation endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class PLSEvaluationRequest(BaseModel):
    """Request schema for PLS evaluation"""
    text: str = Field(..., description="Text to evaluate for PLS compliance")
    format: Optional[str] = Field("json", description="Output format: 'json' or 'text'")

class PLSEvaluationResponse(BaseModel):
    """Response schema for PLS evaluation"""
    linguistic_evaluation: Dict[str, Any] = Field(..., description="Detailed linguistic metric evaluations")
    word_count_status: Dict[str, Any] = Field(..., description="Word count evaluation against PLS limits") 
    summary: Dict[str, Any] = Field(..., description="Overall evaluation summary and statistics")

class PLSEvaluationTextResponse(BaseModel):
    """Response schema for PLS evaluation in text format"""
    evaluation: str = Field(..., description="Human-readable evaluation text")