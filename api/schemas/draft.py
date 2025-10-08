"""
Schemas for Draft submissions with evaluations
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class DraftEvaluation(BaseModel):
    """Evaluation of a draft"""
    grade: str = Field(..., description="Evaluation grade (e.g., APPROVED, NOT_APPROVED)")
    feedback: str = Field(..., description="Detailed feedback text")
    pls_evaluation_summary: str = Field(..., description="Summary of PLS evaluation")


class DraftSubmission(BaseModel):
    """Draft text submission with metrics and evaluation"""
    model: str = Field(..., description="Model name (e.g., gemini_2_5_pro, llama_3_3_70b)")
    id: str = Field(..., description="ID of the summary this draft belongs to")
    draft: str = Field(..., description="The draft text content")
    metrics: List[Dict[str, Any]] = Field(..., description="Array of evaluation metrics")
    evaluation: List[Dict[str, Any]] = Field(..., description="Array containing evaluation object with grade, feedback, and pls_evaluation_summary")


class DraftResponse(BaseModel):
    """Response after saving a draft"""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Success or error message")
    id: str = Field(..., description="ID of the summary")
    draft_number: int = Field(..., description="Number assigned to this draft")
    file_path: str = Field(..., description="Path where the draft was saved")
