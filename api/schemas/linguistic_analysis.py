"""
Pydantic schemas for linguistic analysis endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union


class LinguisticAnalysisRequest(BaseModel):
    """Request schema for single text analysis"""
    text: str = Field(..., description="Text to analyze", min_length=1)
    include_tokens: bool = Field(False, description="Whether to include detailed token information")
    simplify_tokens: bool = Field(False, description="If true, include only word lists (simplified tokens) and omit detailed token objects")


class MultipleLinguisticAnalysisRequest(BaseModel):
    """Request schema for multiple text analysis"""
    texts: List[str] = Field(..., description="Array of texts to analyze", min_items=1)
    text_ids: Optional[List[str]] = Field(None, description="Optional IDs for each text")
    include_tokens: bool = Field(False, description="Whether to include detailed token information")
    simplify_tokens: bool = Field(False, description="If true, include only word lists (simplified tokens) and omit detailed token objects")


class TokenInfo(BaseModel):
    """Schema for individual token information"""
    text: str
    lemma: str
    pos: Optional[str] = None
    tag: Optional[str] = None
    dep: Optional[str] = None
    is_stop: Optional[bool] = None


class EntityInfo(BaseModel):
    """Schema for named entity information"""
    text: str
    label: str
    start: int
    end: int


class DetailedTokens(BaseModel):
    """Schema for detailed token breakdown by category"""
    # Voice analysis tokens
    passive_voice_tokens: List[TokenInfo] = []
    active_voice_tokens: List[TokenInfo] = []
    passive_subject_tokens: List[TokenInfo] = []
    active_subject_tokens: List[TokenInfo] = []
    
    # POS tokens
    verb_tokens: List[TokenInfo] = []
    noun_tokens: List[TokenInfo] = []
    adjective_tokens: List[TokenInfo] = []
    adverb_tokens: List[TokenInfo] = []
    preposition_tokens: List[TokenInfo] = []
    auxiliary_tokens: List[TokenInfo] = []
    coord_conjunction_tokens: List[TokenInfo] = []
    subordinating_conjunction_tokens: List[TokenInfo] = []
    determiner_tokens: List[TokenInfo] = []
    interjection_tokens: List[TokenInfo] = []
    number_tokens: List[TokenInfo] = []
    particle_tokens: List[TokenInfo] = []
    pronoun_tokens: List[TokenInfo] = []
    proper_noun_tokens: List[TokenInfo] = []
    punctuation_tokens: List[TokenInfo] = []
    symbol_tokens: List[TokenInfo] = []
    other_tokens: List[TokenInfo] = []
    
    # Named entity tokens
    money_entity_tokens: List[EntityInfo] = []
    person_entity_tokens: List[EntityInfo] = []
    norp_entity_tokens: List[EntityInfo] = []
    facility_entity_tokens: List[EntityInfo] = []
    organization_entity_tokens: List[EntityInfo] = []
    gpe_entity_tokens: List[EntityInfo] = []
    product_entity_tokens: List[EntityInfo] = []
    event_entity_tokens: List[EntityInfo] = []
    work_of_art_entity_tokens: List[EntityInfo] = []
    language_entity_tokens: List[EntityInfo] = []
    date_entity_tokens: List[EntityInfo] = []
    time_entity_tokens: List[EntityInfo] = []
    quantity_entity_tokens: List[EntityInfo] = []
    ordinal_entity_tokens: List[EntityInfo] = []
    cardinal_entity_tokens: List[EntityInfo] = []
    percent_entity_tokens: List[EntityInfo] = []
    location_entity_tokens: List[EntityInfo] = []
    law_entity_tokens: List[EntityInfo] = []
    
    # Special categories
    stopword_tokens: List[TokenInfo] = []
    all_tokens: List[TokenInfo] = []


class AnalysisMetadata(BaseModel):
    """Schema for analysis metadata"""
    text_length: int
    text_preview: str
    analysis_timestamp: str
    includes_detailed_tokens: bool


class LinguisticAnalysisResult(BaseModel):
    """Schema for linguistic analysis results"""
    # Readability scores
    flesch_reading_ease: Optional[float] = None
    flesch_kincaid_grade: Optional[float] = None
    automated_readability_index: Optional[float] = None
    coleman_liau_index: Optional[float] = None
    gunning_fog_index: Optional[float] = None
    lix: Optional[float] = None
    smog_index: Optional[float] = None
    rix: Optional[float] = None
    dale_chall_readability: Optional[float] = None
    
    # Basic counts
    words: int
    sentences: int
    characters: int
    
    # Voice analysis
    passive_voice: int
    active_voice: int
    passive_subjects: int
    active_subjects: int
    
    # Parts of speech
    verbs: int
    nouns: int
    adjectives: int
    adverbs: int
    prepositions: int
    auxiliaries: int
    conjunctions: int
    coord_conjunctions: int
    subordinating_conjunctions: int
    determiners: int
    interjections: int
    numbers: int
    particles: int
    pronouns: int
    proper_nouns: int
    punctuation: int
    symbols: int
    other: int
    
    # Named entities
    money_entities: int = 0
    person_entities: int = 0
    norp_entities: int = 0
    facility_entities: int = 0
    organization_entities: int = 0
    gpe_entities: int = 0
    product_entities: int = 0
    event_entities: int = 0
    work_of_art_entities: int = 0
    language_entities: int = 0
    date_entities: int = 0
    time_entities: int = 0
    quantity_entities: int = 0
    ordinal_entities: int = 0
    cardinal_entities: int = 0
    percent_entities: int = 0
    location_entities: int = 0
    law_entities: int = 0
    
    # Additional metrics
    stopwords: int
    characters_per_word: Optional[float] = None
    syllables_per_word: Optional[float] = None
    words_per_sentence: Optional[float] = None
    sentences_per_paragraph: Optional[float] = None
    type_token_ratio: Optional[float] = None
    syllables: Optional[int] = None
    paragraphs: Optional[int] = None
    long_words: Optional[int] = None
    polysyllables: Optional[int] = None
    complex_words: Optional[int] = None
    complex_words_dc: Optional[int] = None
    
    # Library-specific metrics
    tobeverb: Optional[int] = None
    auxverb: Optional[int] = None
    conjunction: Optional[int] = None
    nominalization: Optional[int] = None
    wordtypes: Optional[int] = None
    
    # Optional detailed token information
    detailed_tokens: Optional[DetailedTokens] = None
    # Optional simplified token lists (category -> unique words)
    simplified_tokens: Optional[Dict[str, List[str]]] = None
    
    # Metadata
    analysis_metadata: Optional[AnalysisMetadata] = None
    text_id: Optional[str] = None


class LinguisticAnalysisResponse(BaseModel):
    """Response schema for single text analysis"""
    analysis: LinguisticAnalysisResult


class MultipleLinguisticAnalysisResponse(BaseModel):
    """Response schema for multiple text analysis"""
    analyses: List[LinguisticAnalysisResult]
    summary: Dict[str, Any] = Field(default_factory=dict)