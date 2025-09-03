from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import tools
from api.core.tool_registry import tool_registry
from api.tools.glossary_tool import GlossaryTool
from api.tools.linguistic_analysis_tool import LinguisticAnalysisTool
from api.tools.pls_evaluation_tool import PLSEvaluationTool


# Register tools
def register_tools():
    """Register all available tools"""
    glossary_tool = GlossaryTool()
    tool_registry.register(glossary_tool)
    
    linguistic_analysis_tool = LinguisticAnalysisTool()
    tool_registry.register(linguistic_analysis_tool)
    
    pls_evaluation_tool = PLSEvaluationTool()
    tool_registry.register(pls_evaluation_tool)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    register_tools()
    yield
    # Shutdown (if needed)


app = FastAPI(
    title="Medical Writing Tools API",
    description="API for various medical writing tools",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tools.router)

@app.get("/")
async def root():
    return {
        "message": "Medical Writing Tools API",
        "available_tools": [tool.name for tool in tool_registry.list_tools()],
        "endpoints": {
            "/tools": "Execute a tool with parameters",
            "/tools/list": "List all available tools",
            "/tools/glossary": "Find and define medical phrases with match locations and aliases",
            "/tools/linguistic-analysis": "Comprehensive linguistic analysis of text",
            "/tools/linguistic-analysis/detailed": "Linguistic analysis with detailed token information",
            "/tools/linguistic-analysis/multiple": "Linguistic analysis of multiple texts",
            "/tools/pls-evaluation": "Evaluate text against Plain Language Summary thresholds (JSON format)",
            "/tools/pls-evaluation/text": "Evaluate text against Plain Language Summary thresholds (text format)",
            "/docs": "Interactive API documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)