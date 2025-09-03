from fastapi import APIRouter, HTTPException
from typing import List
from api.schemas.base import ToolRequest, ToolResponse, ToolInfo
from api.schemas.glossary import GlossaryRequest, GlossaryResponse, EnhancedGlossaryResponse
from api.schemas.linguistic_analysis import (
    LinguisticAnalysisRequest, 
    MultipleLinguisticAnalysisRequest,
    LinguisticAnalysisResponse,
    MultipleLinguisticAnalysisResponse
)
from api.schemas.pls_evaluation import (
    PLSEvaluationRequest,
    PLSEvaluationResponse,
    PLSEvaluationTextResponse
)
from pydantic import BaseModel
from api.core.tool_registry import tool_registry

router = APIRouter(prefix="/tools", tags=["tools"])

@router.get("/list", response_model=List[ToolInfo])
async def list_tools():
    """List all available tools"""
    return tool_registry.list_tools()

@router.post("", response_model=ToolResponse)
async def execute_tool(request: ToolRequest):
    """Execute a tool by name with parameters"""
    tool = tool_registry.get_tool(request.tool_name)
    
    if not tool:
        return ToolResponse(
            tool_name=request.tool_name,
            status="error",
            error=f"Unknown tool: {request.tool_name}"
        )
    
    return await tool.execute(request.parameters)

@router.post("/glossary", response_model=EnhancedGlossaryResponse)
async def glossary_tool(request: GlossaryRequest):
    """Find and define medical phrases with match locations and aliases"""
    tool = tool_registry.get_tool("glossary")
    
    if not tool:
        raise HTTPException(status_code=503, detail="Glossary tool is not available")
    
    response = await tool.execute({"text": request.text})
    
    if response.status == "error":
        raise HTTPException(status_code=500, detail=response.error)
    
    return EnhancedGlossaryResponse(**response.result)

@router.post("/linguistic-analysis", response_model=LinguisticAnalysisResponse)
async def analyze_text(request: LinguisticAnalysisRequest):
    """Perform comprehensive linguistic analysis on a single text"""
    tool = tool_registry.get_tool("linguistic_analysis")
    
    if not tool:
        raise HTTPException(status_code=503, detail="Linguistic analysis tool is not available")
    
    response = await tool.execute({
        "text": request.text,
        "include_tokens": request.include_tokens,
        "simplify_tokens": request.simplify_tokens
    })
    
    if response.status == "error":
        raise HTTPException(status_code=500, detail=response.error)
    
    return LinguisticAnalysisResponse(analysis=response.result)

@router.post("/linguistic-analysis/detailed", response_model=LinguisticAnalysisResponse)
async def analyze_text_detailed(request: LinguisticAnalysisRequest):
    """Perform comprehensive linguistic analysis with detailed token information"""
    tool = tool_registry.get_tool("linguistic_analysis")
    
    if not tool:
        raise HTTPException(status_code=503, detail="Linguistic analysis tool is not available")
    
    response = await tool.execute({
        "text": request.text,
        "include_tokens": True,  # Force detailed analysis
        "simplify_tokens": request.simplify_tokens
    })
    
    if response.status == "error":
        raise HTTPException(status_code=500, detail=response.error)
    
    return LinguisticAnalysisResponse(analysis=response.result)

@router.post("/linguistic-analysis/multiple", response_model=MultipleLinguisticAnalysisResponse)
async def analyze_multiple_texts(request: MultipleLinguisticAnalysisRequest):
    """Perform linguistic analysis on multiple texts"""
    tool = tool_registry.get_tool("linguistic_analysis")
    
    if not tool:
        raise HTTPException(status_code=503, detail="Linguistic analysis tool is not available")
    
    response = await tool.execute({
        "texts": request.texts,
        "text_ids": request.text_ids,
        "include_tokens": request.include_tokens,
        "simplify_tokens": request.simplify_tokens
    })
    
    if response.status == "error":
        raise HTTPException(status_code=500, detail=response.error)
    
    return MultipleLinguisticAnalysisResponse(**response.result)

@router.post("/pls-evaluation", response_model=PLSEvaluationResponse)
async def evaluate_pls(request: PLSEvaluationRequest):
    """Evaluate text against Plain Language Summary thresholds (JSON format)"""
    tool = tool_registry.get_tool("pls_evaluation")
    
    if not tool:
        raise HTTPException(status_code=503, detail="PLS evaluation tool is not available")
    
    response = await tool.execute({
        "text": request.text,
        "format": "json"
    })
    
    if response.status == "error":
        raise HTTPException(status_code=500, detail=response.error)
    
    return PLSEvaluationResponse(**response.result)

@router.post("/pls-evaluation/text", response_model=PLSEvaluationTextResponse)
async def evaluate_pls_text(request: PLSEvaluationRequest):
    """Evaluate text against Plain Language Summary thresholds (text format)"""
    tool = tool_registry.get_tool("pls_evaluation")
    
    if not tool:
        raise HTTPException(status_code=503, detail="PLS evaluation tool is not available")
    
    response = await tool.execute({
        "text": request.text,
        "format": "text"
    })
    
    if response.status == "error":
        raise HTTPException(status_code=500, detail=response.error)
    
    return PLSEvaluationTextResponse(evaluation=response.result)