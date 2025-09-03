from pydantic import BaseModel
from typing import Dict, List

class GlossaryRequest(BaseModel):
    text: str

class GlossaryDefinition(BaseModel):
    main_term: str
    plain_alternative: str
    source: str

class GlossaryResponse(BaseModel):
    found_phrases: Dict[str, List[GlossaryDefinition]]
    total_phrases_found: int


# Enhanced schemas for the improved API
class DefinitionInfo(BaseModel):
    plain_alternative: str
    source: str


class MatchLocation(BaseModel):
    alias_found: str
    location_start: int
    location_end: int


class FoundTerm(BaseModel):
    main_term: str
    definitions: List[DefinitionInfo]
    matches_in_text: List[MatchLocation]


class AnalysisSummary(BaseModel):
    total_unique_phrases_found: int
    text_character_length: int


class EnhancedGlossaryResponse(BaseModel):
    analysis_summary: AnalysisSummary
    found_terms: List[FoundTerm]