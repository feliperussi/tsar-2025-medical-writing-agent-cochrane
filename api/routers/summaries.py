"""
Router for PLS (Plain Language Summary) management
"""

import json
import os
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException
from api.schemas.pls_summary import PLSSummarySections, PLSSummaryResponse
from api.schemas.draft import DraftSubmission, DraftResponse

router = APIRouter(prefix="/summaries", tags=["summaries"])

# Get the api directory path
API_DIR = Path(__file__).parent.parent
SUMMARIES_DIR = API_DIR / "data" / "generated_summaries"


@router.post("", response_model=PLSSummaryResponse)
async def save_pls_summary(sections: PLSSummarySections):
    """
    Save a Plain Language Summary with all sections

    Args:
        sections: Complete PLS summary with all required sections

    Returns:
        Response with status and file path
    """
    try:
        # Create model/ID directory structure
        model_dir = SUMMARIES_DIR / sections.model
        id_dir = model_dir / sections.id
        id_dir.mkdir(parents=True, exist_ok=True)

        # Prepare the data structure (only sections, not the ID or model)
        sections_data = {
            "plain_title": sections.plain_title,
            "key_messages": sections.key_messages,
            "background": [section.dict() for section in sections.background],
            "methods": [section.dict() for section in sections.methods],
            "results": [section.dict() for section in sections.results],
            "limitations": sections.limitations,
            "currency": sections.currency
        }

        # Save to sections.json inside the model/ID folder
        file_path = id_dir / "sections.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sections_data, f, indent=2, ensure_ascii=False)

        return PLSSummaryResponse(
            status="success",
            message=f"Summary saved successfully",
            id=sections.id,
            file_path=str(file_path)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save summary: {str(e)}"
        )


@router.get("/{model}/{summary_id}", response_model=PLSSummarySections)
async def get_pls_summary(model: str, summary_id: str):
    """
    Retrieve a saved Plain Language Summary by model and ID

    Args:
        model: The model name
        summary_id: The ID of the summary to retrieve

    Returns:
        The complete PLS summary
    """
    try:
        # Look for sections.json inside the model/ID folder
        model_dir = SUMMARIES_DIR / model
        id_dir = model_dir / summary_id
        file_path = id_dir / "sections.json"

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Summary with model '{model}' and ID '{summary_id}' not found"
            )

        with open(file_path, 'r', encoding='utf-8') as f:
            sections_data = json.load(f)

        return PLSSummarySections(
            model=model,
            id=summary_id,
            plain_title=sections_data["plain_title"],
            key_messages=sections_data["key_messages"],
            background=sections_data["background"],
            methods=sections_data["methods"],
            results=sections_data["results"],
            limitations=sections_data["limitations"],
            currency=sections_data["currency"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve summary: {str(e)}"
        )


@router.get("")
async def list_summaries():
    """
    List all saved PLS summaries

    Returns:
        List of summary IDs
    """
    try:
        if not SUMMARIES_DIR.exists():
            return {"summaries": [], "count": 0}

        # Get all directories in the summaries folder
        summary_dirs = [d for d in SUMMARIES_DIR.iterdir() if d.is_dir()]
        summary_ids = [d.name for d in summary_dirs]

        return {
            "summaries": sorted(summary_ids),
            "count": len(summary_ids)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list summaries: {str(e)}"
        )


@router.delete("/{model}/{summary_id}")
async def delete_pls_summary(model: str, summary_id: str):
    """
    Delete a saved Plain Language Summary by model and ID (deletes entire folder)

    Args:
        model: The model name
        summary_id: The ID of the summary to delete

    Returns:
        Confirmation message
    """
    try:
        import shutil

        model_dir = SUMMARIES_DIR / model
        id_dir = model_dir / summary_id

        if not id_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Summary with model '{model}' and ID '{summary_id}' not found"
            )

        # Delete the entire directory
        shutil.rmtree(id_dir)

        return {
            "status": "success",
            "message": f"Summary '{summary_id}' from model '{model}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete summary: {str(e)}"
        )


@router.post("/{model}/{summary_id}/drafts", response_model=DraftResponse)
async def save_draft(model: str, summary_id: str, draft_data: DraftSubmission):
    """
    Save a new draft with its evaluation for a given model and summary ID

    Drafts are automatically numbered sequentially (draft_1.json, draft_2.json, etc.)

    Args:
        model: The model name
        summary_id: The ID of the summary this draft belongs to
        draft_data: The draft text, metrics, and evaluation

    Returns:
        Response with status, draft number, and file path
    """
    try:
        # Verify the model/summary ID directory exists
        model_dir = SUMMARIES_DIR / model
        id_dir = model_dir / summary_id

        if not id_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Summary with model '{model}' and ID '{summary_id}' not found. Please create the summary first."
            )

        # Find existing draft files and determine the next number
        existing_drafts = list(id_dir.glob("draft_*.json"))

        if existing_drafts:
            # Extract numbers from existing draft filenames
            numbers = []
            for draft_file in existing_drafts:
                match = re.search(r'draft_(\d+)\.json', draft_file.name)
                if match:
                    numbers.append(int(match.group(1)))

            # Get the next number
            next_number = max(numbers) + 1 if numbers else 1
        else:
            next_number = 1

        # Prepare the draft data structure
        draft_content = {
            "id": summary_id,
            "draft": draft_data.draft,
            "metrics": draft_data.metrics,
            "evaluation": draft_data.evaluation
        }

        # Save to draft_{number}.json
        file_path = id_dir / f"draft_{next_number}.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(draft_content, f, indent=2, ensure_ascii=False)

        return DraftResponse(
            status="success",
            message=f"Draft {next_number} saved successfully",
            id=summary_id,
            draft_number=next_number,
            file_path=str(file_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save draft: {str(e)}"
        )


@router.get("/{model}/{summary_id}/drafts/last")
async def get_last_draft(model: str, summary_id: str):
    """
    Retrieve the latest draft for a given model and summary ID

    Args:
        model: The model name
        summary_id: The ID of the summary

    Returns:
        The latest draft content with metrics and evaluation
    """
    try:
        model_dir = SUMMARIES_DIR / model
        id_dir = model_dir / summary_id

        if not id_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Summary with model '{model}' and ID '{summary_id}' not found"
            )

        # Find all draft files
        existing_drafts = list(id_dir.glob("draft_*.json"))

        if not existing_drafts:
            raise HTTPException(
                status_code=404,
                detail=f"No drafts found for model '{model}' and summary '{summary_id}'"
            )

        # Extract numbers and find the maximum
        numbers = []
        for draft_file in existing_drafts:
            match = re.search(r'draft_(\d+)\.json', draft_file.name)
            if match:
                numbers.append(int(match.group(1)))

        if not numbers:
            raise HTTPException(
                status_code=404,
                detail=f"No valid draft files found for model '{model}' and summary '{summary_id}'"
            )

        # Get the latest draft number
        last_number = max(numbers)
        last_draft_path = id_dir / f"draft_{last_number}.json"

        # Read and return the draft
        with open(last_draft_path, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)

        return {
            "draft_number": last_number,
            "file_path": str(last_draft_path),
            **draft_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve last draft: {str(e)}"
        )


@router.get("/{model}/{summary_id}/drafts/best")
async def get_best_draft(model: str, summary_id: str):
    """
    Retrieve the best draft based on the highest best_quartile_rate that meets word count requirement (≤850 words)

    The endpoint:
    1. Reads all drafts
    2. Sorts them by best_quartile_rate (highest first)
    3. Returns the first one with word_count ≤ 850
    4. If none meet the word requirement, returns the best by best_quartile_rate regardless

    Args:
        model: The model name
        summary_id: The ID of the summary

    Returns:
        The best draft that meets word count requirements
    """
    try:
        model_dir = SUMMARIES_DIR / model
        id_dir = model_dir / summary_id

        if not id_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Summary with model '{model}' and ID '{summary_id}' not found"
            )

        # Find all draft files
        existing_drafts = list(id_dir.glob("draft_*.json"))

        if not existing_drafts:
            raise HTTPException(
                status_code=404,
                detail=f"No drafts found for model '{model}' and summary '{summary_id}'"
            )

        # Read all drafts and extract metrics
        drafts_info = []

        for draft_file in existing_drafts:
            match = re.search(r'draft_(\d+)\.json', draft_file.name)
            if not match:
                continue

            draft_number = int(match.group(1))

            with open(draft_file, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)

            # Extract best_quartile_rate and word_count from metrics
            if 'metrics' in draft_data and len(draft_data['metrics']) > 0:
                metrics = draft_data['metrics'][0]

                best_quartile_rate = None
                word_count = None

                if 'summary' in metrics and 'best_quartile_rate' in metrics['summary']:
                    best_quartile_rate = metrics['summary']['best_quartile_rate']

                if 'word_count_status' in metrics and 'word_count' in metrics['word_count_status']:
                    word_count = metrics['word_count_status']['word_count']

                if best_quartile_rate is not None:
                    drafts_info.append({
                        'number': draft_number,
                        'data': draft_data,
                        'best_quartile_rate': best_quartile_rate,
                        'word_count': word_count
                    })

        if not drafts_info:
            raise HTTPException(
                status_code=404,
                detail=f"No drafts with valid metrics found for model '{model}' and summary '{summary_id}'"
            )

        # Sort by best_quartile_rate (highest first)
        drafts_info.sort(key=lambda x: x['best_quartile_rate'], reverse=True)

        # Find the first one that meets word count requirement (≤850)
        selected_draft = None
        for draft_info in drafts_info:
            if draft_info['word_count'] is not None and draft_info['word_count'] <= 850:
                selected_draft = draft_info
                break

        # If none meet the requirement, pick the best one regardless
        if selected_draft is None:
            selected_draft = drafts_info[0]

        return {
            "draft_number": selected_draft['number'],
            "best_quartile_rate": selected_draft['best_quartile_rate'],
            "word_count": selected_draft['word_count'],
            "file_path": str(id_dir / f"draft_{selected_draft['number']}.json"),
            **selected_draft['data']
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve best draft: {str(e)}"
        )
