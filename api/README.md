# Medical Writing Tools API

A FastAPI-based API that provides various tools for medical writing, starting with a comprehensive glossary service that identifies and defines complex medical terms.

## Features

- **Glossary Tool**: Analyzes text to find medical terms and provides plain language alternatives
  - **Location Tracking**: Returns exact character positions where terms are found
  - **Alias Recognition**: Shows which specific text triggered each match
  - **Grouped Definitions**: Organizes results by main medical concept
- **Linguistic Analysis Tool**: Comprehensive text analysis for readability and linguistic features
  - **Readability Scores**: Flesch Reading Ease, Flesch-Kincaid Grade, ARI, Coleman-Liau, Gunning Fog, and more
  - **POS Analysis**: Part-of-speech distributions with detailed token information
  - **Voice Analysis**: Active vs passive voice detection with specific word identification
  - **Named Entity Recognition**: Identifies persons, organizations, dates, locations, and more
  - **Flexible Output**: Basic metrics or detailed token-level analysis based on user needs
- **PLS Evaluation Tool**: Evaluates text against Plain Language Summary compliance thresholds
  - **Percentile-Based Thresholds**: Uses data-driven thresholds from training corpus for evaluation
  - **Multi-Level Rating System**: Classifies metrics as EXCELLENT/GOOD/ACCEPTABLE/POOR/CRITICAL
  - **Word Count Validation**: Ensures compliance with 850-word limit for Plain Language Summaries
  - **Improvement Recommendations**: Provides specific numerical targets for poor/critical metrics
  - **Dual Output Formats**: Structured JSON for API integration or human-readable text for review
- **Multiple Glossary Sources**: Integrates 11+ medical glossaries from reputable sources
- **RESTful API**: Easy-to-use endpoints for tool execution
- **Extensible Architecture**: Designed to easily add new tools
- **Singleton Pattern**: Efficient memory usage with one-time glossary indexing

## Installation

1. Install dependencies using UV:

```bash
uv pip install -r requirements.txt
```

2. Install spaCy model for linguistic analysis:

```bash
python -m spacy download en_core_web_lg
```

## Running the API

```bash
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Root Endpoint

- `GET /` - Returns API information and available endpoints

### Tools Endpoints

- `GET /tools/list` - List all available tools and their parameters
- `POST /tools` - Execute any tool by name with parameters
- `POST /tools/glossary` - Direct endpoint for glossary tool
- `POST /tools/linguistic-analysis` - Comprehensive linguistic analysis (basic mode)
- `POST /tools/linguistic-analysis/detailed` - Linguistic analysis with detailed token information
- `POST /tools/linguistic-analysis/multiple` - Analyze multiple texts at once
- `POST /tools/pls-evaluation` - Evaluate text against Plain Language Summary thresholds (JSON format)
- `POST /tools/pls-evaluation/text` - Evaluate text against Plain Language Summary thresholds (text format)

## Using the Glossary Tool

### Via Direct Glossary Endpoint

```bash
curl -X POST "http://localhost:8000/tools/glossary" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The patient experienced adverse effects during the clinical trial."
  }'
```

### Via Generic Tools Endpoint

```bash
curl -X POST "http://localhost:8000/tools" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "glossary",
    "parameters": {
      "text": "The patient experienced adverse effects during the clinical trial."
    }
  }'
```

## Response Format

The glossary tool returns an enhanced response with location information and organized by medical concepts:

```json
{
  "analysis_summary": {
    "total_unique_phrases_found": 2,
    "text_character_length": 66
  },
  "found_terms": [
    {
      "main_term": "Adverse effects",
      "definitions": [
        {
          "plain_alternative": "Unwanted or harmful effects of a treatment",
          "source": "cochrane_glossary"
        }
      ],
      "matches_in_text": [
        {
          "alias_found": "adverse effects",
          "location_start": 24,
          "location_end": 39
        }
      ]
    },
    {
      "main_term": "Clinical Trial",
      "definitions": [
        {
          "plain_alternative": "A research study that tests drugs, devices and treatments...",
          "source": "clinical_research_glossary"
        }
      ],
      "matches_in_text": [
        {
          "alias_found": "clinical trial",
          "location_start": 51,
          "location_end": 65
        }
      ]
    }
  ]
}
```

### Key Features of the Response:

- **`analysis_summary`**: Overview of the analysis including total phrases found and text length
- **`found_terms`**: List of medical terms found, grouped by main concept
- **`matches_in_text`**: Exact locations where each term was found, including:
  - `alias_found`: The exact text that was matched
  - `location_start`: Character position where the match starts
  - `location_end`: Character position where the match ends
- **`definitions`**: All available definitions from different sources for each concept

## Using the Linguistic Analysis Tool

The linguistic analysis tool provides comprehensive text analysis including readability scores, part-of-speech distributions, named entity recognition, and voice analysis.

### Basic Analysis

```bash
curl -X POST "http://localhost:8000/tools/linguistic-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The patient was treated by the doctor with a new medication.",
    "include_tokens": false
  }'
```

**Basic Response** (counts only):
```json
{
  "analysis": {
    "flesch_reading_ease": 45.76,
    "flesch_kincaid_grade": 8.3,
    "words": 11,
    "sentences": 1,
    "passive_voice": 1,
    "active_voice": 0,
    "nouns": 3,
    "verbs": 1,
    "adjectives": 1,
    "analysis_metadata": {
      "text_length": 60,
      "includes_detailed_tokens": false
    }
  }
}
```

### Detailed Analysis with Token Information

```bash
curl -X POST "http://localhost:8000/tools/linguistic-analysis/detailed" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The patient was treated by the doctor with a new medication."
  }'
```

**Detailed Response** (includes specific words):
```json
{
  "analysis": {
    "flesch_reading_ease": 45.76,
    "words": 11,
    "passive_voice": 1,
    "active_voice": 0,
    "detailed_tokens": {
      "passive_voice_tokens": [
        {
          "text": "treated",
          "lemma": "treat",
          "pos": "VERB",
          "dep": "ROOT"
        }
      ],
      "noun_tokens": [
        {
          "text": "patient",
          "lemma": "patient",
          "pos": "NOUN",
          "tag": "NN"
        },
        {
          "text": "doctor",
          "lemma": "doctor",
          "pos": "NOUN",
          "tag": "NN"
        },
        {
          "text": "medication",
          "lemma": "medication",
          "pos": "NOUN",
          "tag": "NN"
        }
      ]
    }
  }
}
```

### Multiple Text Analysis

```bash
curl -X POST "http://localhost:8000/tools/linguistic-analysis/multiple" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Simple sentence.",
      "The complex pharmacological intervention was successfully implemented."
    ],
    "text_ids": ["simple", "complex"],
    "include_tokens": false
  }'
```

### Key Metrics Provided:

**Readability Scores:**
- Flesch Reading Ease
- Flesch-Kincaid Grade Level
- Automated Readability Index (ARI)
- Coleman-Liau Index
- Gunning Fog Index
- LIX and RIX scores
- SMOG Index
- Dale-Chall Readability Score

**Linguistic Features:**
- Word, sentence, and character counts
- Part-of-speech distributions (nouns, verbs, adjectives, etc.)
- Voice analysis (active vs passive voice)
- Named entity recognition (persons, organizations, dates, etc.)
- Stopword analysis
- Type-token ratio
- Average syllables per word
- Complex word counts

**Token-Level Analysis** (when `include_tokens: true`):
- Specific words identified for each linguistic category
- Lemmas, POS tags, and dependency relations
- Character positions for named entities
- Complete token breakdown with linguistic annotations

## Using the PLS Evaluation Tool

The PLS (Plain Language Summary) evaluation tool assesses text compliance against Cochrane Plain Language Summary guidelines using data-driven thresholds and provides specific improvement recommendations.

### JSON Format Evaluation

```bash
curl -X POST "http://localhost:8000/tools/pls-evaluation" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This systematic review examined the effects of pharmacological interventions on cardiovascular outcomes in patients with diabetes mellitus type 2."
  }'
```

**JSON Response Structure:**
```json
{
  "linguistic_evaluation": {
    "words": {
      "value": 19,
      "rating": "within_limit",
      "direction": null,
      "feedback": null
    },
    "flesch_reading_ease": {
      "value": 23.4,
      "rating": "critical",
      "direction": "higher_better",
      "feedback": "Increase from 23.4 to >40.5"
    },
    "gunning_fog_index": {
      "value": 22.1,
      "rating": "poor",
      "direction": "lower_better",
      "feedback": "Reduce from 22.1 to <17.8"
    },
    "active_voice": {
      "value": 0,
      "rating": "critical",
      "direction": "higher_better",
      "feedback": "Increase from 0.0 to >29.0"
    }
  },
  "word_count_status": {
    "word_count": 19,
    "limit": 850,
    "status": "within_limit",
    "message": "Word count: 19 ✓ WITHIN LIMIT (≤850 words)"
  },
  "summary": {
    "excellent_count": 1,
    "good_count": 0,
    "acceptable_count": 0,
    "poor_count": 1,
    "critical_count": 2,
    "total_evaluated": 4,
    "excellent_percentage": 25.0,
    "poor_percentage": 25.0,
    "critical_percentage": 50.0,
    "excellence_rate": 25.0,
    "overall_assessment": "NEEDS IMPROVEMENT"
  }
}
```

### Human-Readable Text Format

```bash
curl -X POST "http://localhost:8000/tools/pls-evaluation/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This systematic review examined the effects of pharmacological interventions on cardiovascular outcomes in patients with diabetes mellitus type 2."
  }'
```

**Text Response Example:**
```
Word count: 19 ✓ WITHIN LIMIT (≤850 words)
Sentences: 1

METRIC EVALUATION:

words                          = 19.00 → WITHIN_LIMIT
flesch_reading_ease        ↑   = 23.40 → CRITICAL
gunning_fog_index          ↓   = 22.10 → POOR
active_voice               ↑   =  0.00 → CRITICAL

SUMMARY:

  Excellent:   1 features (25.0%)
  Good:        0 features (0.0%)
  Acceptable:  0 features (0.0%)
  Poor:        1 features (25.0%)
  Critical:    2 features (50.0%)

Overall Rating: NEEDS IMPROVEMENT
Excellence Rate: 25.0%

IMPROVEMENT RECOMMENDATIONS
Priority Areas (3 features need attention):
   1. flesch_reading_ease: Increase from 23.4 to >40.5
   2. gunning_fog_index: Reduce from 22.1 to <17.8
   3. active_voice: Increase from 0.0 to >29.0
```

### Key Features of PLS Evaluation:

**Rating Categories:**
- **EXCELLENT**: Text exceeds best practices (top 20th percentile)
- **GOOD**: Text meets good standards (20th-40th percentile)
- **ACCEPTABLE**: Text is within acceptable range (40th-60th percentile)  
- **POOR**: Text needs improvement (60th-80th percentile)
- **CRITICAL**: Text requires significant revision (bottom 20th percentile)

**Evaluation Metrics:**
- **Readability Indices**: Flesch Reading Ease, Gunning Fog, SMOG, etc.
- **Sentence Structure**: Words per sentence, passive vs active voice
- **Vocabulary Complexity**: Complex words, long words, syllables per word
- **Plain Language Elements**: Pronouns usage, nominalization, verb usage
- **Word Count Compliance**: 850-word limit validation for PLS guidelines

**Improvement Recommendations:**
- Specific numerical targets for metrics rated as POOR or CRITICAL
- Direction indicators (↑ increase, ↓ decrease) for each metric
- Percentile-based thresholds derived from training data analysis

### Via Generic Tools Endpoint

```bash
# JSON format
curl -X POST "http://localhost:8000/tools" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "pls_evaluation",
    "parameters": {
      "text": "Your text here",
      "format": "json"
    }
  }'

# Text format  
curl -X POST "http://localhost:8000/tools" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "pls_evaluation",
    "parameters": {
      "text": "Your text here",
      "format": "text"
    }
  }'
```

## Configuration

Set the glossaries directory path using the environment variable:

```bash
export GLOSSARIES_DIR="/path/to/glossaries"
```

Default: `./glossary_service/glossaries`

## Glossary Sources

The glossary data comes from multiple authoritative medical sources. See [glossary_service/SOURCES.md](glossary_service/SOURCES.md) for the complete list of sources.

## API Documentation

When running, visit:

- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## Project Structure

```
api/
├── core/                    # Core functionality
│   ├── base_tool.py        # Abstract base class for tools
│   └── tool_registry.py    # Tool registration and management
├── routers/                # API route handlers
│   └── tools.py           # Tools endpoints
├── schemas/               # Pydantic models
│   ├── base.py           # Common schemas
│   ├── glossary.py       # Glossary-specific schemas
│   ├── linguistic_analysis.py  # Linguistic analysis schemas
│   └── pls_evaluation.py # PLS evaluation schemas
├── tools/                # Tool implementations
│   ├── glossary_tool.py  # Glossary tool
│   ├── linguistic_analysis_tool.py  # Linguistic analysis tool
│   ├── pls_evaluation_tool.py  # PLS evaluation tool
│   └── example_tool.py.example  # Template for new tools
├── data/                 # Configuration and threshold data
│   └── pls_evaluation_thresholds_from_data.json  # PLS evaluation thresholds
└── main.py              # FastAPI application entry point
```

## Adding New Tools

To add a new tool:

1. **Create a new tool class** in `api/tools/` that inherits from `BaseTool`:
   ```python
   from api.core.base_tool import BaseTool
   
   class MyTool(BaseTool):
       @property
       def info(self) -> ToolInfo:
           return ToolInfo(name="my_tool", ...)
       
       async def execute(self, parameters: Dict[str, Any]) -> ToolResponse:
           # Implement tool logic
           pass
   ```

2. **Register the tool** in `main.py`:
   ```python
   def register_tools():
       tool_registry.register(GlossaryTool())
       tool_registry.register(LinguisticAnalysisTool())
       tool_registry.register(PLSEvaluationTool())
       tool_registry.register(MyTool())  # Add your tool here
   ```

3. **Create specific schemas** (optional) in `api/schemas/` if needed

4. **Add a dedicated endpoint** (optional) in `api/routers/tools.py`

See `api/tools/example_tool.py.example` for a complete template

## Testing

The API includes comprehensive test coverage using pytest. The test suite covers:
- API endpoints functionality
- Individual tool implementations
- Tool registry operations
- Error handling and edge cases

### Running Tests

```bash
# Run all tests with verbose output
python -m pytest api/tests/ -v

# Run only the API tests (excluding the legacy glossary service test)
python -m pytest api/tests/test_api_endpoints.py api/tests/glossary_tool/ api/tests/linguistic_analysis_tool/ api/tests/core/ -v

# Run tests with coverage report
python -m pytest api/tests/ --cov=api --cov-report=html

# Run a specific test file
python -m pytest api/tests/test_api_endpoints.py -v

# Run a specific test function
python -m pytest api/tests/test_api_endpoints.py::test_glossary_endpoint_success -v
```

### Test Structure

```
api/tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_api_endpoints.py       # Tests for all API endpoints
├── glossary_tool/              # Glossary tool tests
│   ├── test_glossary_tool.py   # Tool implementation tests
│   └── test_phrases_glossary.py # Legacy glossary service tests
├── linguistic_analysis_tool/   # Linguistic analysis tool tests
│   ├── test_tool_unit.py       # Unit tests for the tool
│   └── test_linguistic_analysis.py # API endpoint tests
└── core/                       # Core functionality tests
    └── test_tool_registry.py   # Tool registry system tests
```

All tests use the FastAPI test client and run without requiring the actual server to be running.

### Running Specific Test Suites

```bash
# Run glossary tool tests only
python -m pytest api/tests/glossary_tool/ -v

# Run linguistic analysis tool tests only
python -m pytest api/tests/linguistic_analysis_tool/ -v

# Run core functionality tests only
python -m pytest api/tests/core/ -v

# Run a specific test file
python -m pytest api/tests/linguistic_analysis_tool/test_tool_unit.py -v
```
