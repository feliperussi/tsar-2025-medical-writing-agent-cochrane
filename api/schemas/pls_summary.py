"""
Schemas for PLS (Plain Language Summary) sections
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class SectionWithSubheading(BaseModel):
    """A section with subheading and content"""
    subheading: str = Field(..., description="Section subheading")
    content: str = Field(..., description="Section content")


class PLSSummarySections(BaseModel):
    """Complete PLS summary with all sections"""
    model: str = Field(..., description="Model name (e.g., gemini_2_5_pro, llama_3_3_70b)")
    id: str = Field(..., description="Unique identifier for the summary (e.g., CD000259.PUB4)")
    plain_title: str = Field(..., description="Plain language title")
    key_messages: List[str] = Field(..., description="Array of key message strings")
    background: List[SectionWithSubheading] = Field(..., description="Background sections with subheadings")
    methods: List[SectionWithSubheading] = Field(..., description="Methods sections with subheadings")
    results: List[SectionWithSubheading] = Field(..., description="Results sections with subheadings")
    limitations: str = Field(..., description="Limitations text")
    currency: str = Field(..., description="Currency/date information")


class PLSSummaryResponse(BaseModel):
    """Response after saving PLS summary"""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Success or error message")
    id: str = Field(..., description="ID of the saved summary")
    file_path: Optional[str] = Field(None, description="Path where the file was saved")
