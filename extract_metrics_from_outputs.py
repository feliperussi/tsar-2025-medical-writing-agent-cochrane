#!/usr/bin/env python3
"""
Script to extract linguistic metrics from all output files using the API.
Processes baseline, agentic, and original outputs.
"""

import asyncio
import aiohttp
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
METRICS_ENDPOINT = "/tools/pls-evaluation"
OUTPUTS_BASE_DIR = Path("outputs")
RESULTS_DIR = Path("outputs/results")
ORIGINALS_DIR = Path("data/training_data/cochrane/test_jsons")

# Directories to process
OUTPUT_FOLDERS = [
    "agentic_gemini_2_5_pro",
    "agentic_gpt_oss_120b",
    "agentic_llama_3_3_70b",
    "agentic_llama_3_3_70b_evaluator_gemini_2_5_flash",
    "agentic_llama_3_2_3b",
    "agentic_gpt_oss_20b",
    "agentic_old_gemini_2_5_pro",
    "agentic_old_gpt_5",
    "agentic_old_gpt-oss-120B",
    "baseline_gemini_2_5_pro",
    "baseline_gpt_5",
    "baseline_gpt_oss_120b",
    "baseline_gpt_oss_20b",
    "baseline_llama_3_3_70b",
    "baseline_llama_3_2_3b",
    "original",
]

# Test mode: only process first N files
TEST_MODE = False
TEST_LIMIT = 3  # Process only 3 files per folder for testing


def extract_text_from_json(data: Dict[str, Any], folder_type: str) -> str:
    """Extract the relevant text from a JSON file based on folder type."""

    if folder_type == "original":
        # Original files have title + abstract
        title = data.get("title", "")
        abstract = data.get("abstract", "")
        return f"{title}\n\n{abstract}"

    elif "agentic" in folder_type or "baseline" in folder_type:
        # Both agentic and baseline files have 'response' -> 'output' field
        response = data.get("response", {})
        return response.get("output", "")

    return ""


async def get_metrics_from_api(session: aiohttp.ClientSession, text: str) -> Dict[str, Any]:
    """Call the API to get metrics for a given text."""
    url = f"{API_BASE_URL}{METRICS_ENDPOINT}"

    try:
        async with session.post(url, json={"text": text}) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                print(f"    ✗ API error (status {response.status}): {error_text[:100]}")
                return {"error": f"API returned status {response.status}"}
    except Exception as e:
        print(f"    ✗ Exception calling API: {str(e)}")
        return {"error": str(e)}


async def process_file(session: aiohttp.ClientSession, file_path: Path,
                       folder_name: str, output_dir: Path) -> bool:
    """Process a single file: extract text, get metrics, save results."""

    file_id = file_path.stem  # filename without extension

    try:
        # Load JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract text
        text = extract_text_from_json(data, folder_name)

        if not text or text.strip() == "":
            print(f"    ⚠ Skipping {file_id}: No text found")
            return False

        # Get metrics from API
        metrics = await get_metrics_from_api(session, text)

        if "error" in metrics:
            print(f"    ✗ Failed {file_id}: {metrics['error']}")
            return False

        # Prepare result structure
        result = {
            "file_id": file_id,
            "folder": folder_name,
            "text": text,
            "metrics": metrics,
            "processed_at": datetime.now().isoformat()
        }

        # Save to results directory
        output_file = output_dir / f"{file_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"    ✓ Processed {file_id}")
        return True

    except Exception as e:
        print(f"    ✗ Error processing {file_path}: {str(e)}")
        return False


async def process_folder(session: aiohttp.ClientSession, folder_name: str) -> Dict[str, Any]:
    """Process all files in a folder."""

    print(f"\n{'='*80}")
    print(f"Processing folder: {folder_name}")
    print(f"{'='*80}")

    # Determine input directory
    if folder_name == "original":
        input_dir = ORIGINALS_DIR
    else:
        input_dir = OUTPUTS_BASE_DIR / folder_name

    if not input_dir.exists():
        print(f"  ⚠ Directory not found: {input_dir}")
        return {"folder": folder_name, "processed": 0, "failed": 0, "skipped": True}

    # Create output directory
    output_dir = RESULTS_DIR / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all JSON files
    json_files = sorted(list(input_dir.glob("*.json")))

    if TEST_MODE:
        json_files = json_files[:TEST_LIMIT]
        print(f"  TEST MODE: Processing only {len(json_files)} files")

    print(f"  Found {len(json_files)} files to process")

    # Process files
    processed = 0
    failed = 0

    for file_path in json_files:
        success = await process_file(session, file_path, folder_name, output_dir)
        if success:
            processed += 1
        else:
            failed += 1

    print(f"\n  Summary: {processed} processed, {failed} failed")

    return {
        "folder": folder_name,
        "processed": processed,
        "failed": failed,
        "total": len(json_files),
        "skipped": False
    }


async def main():
    """Main execution function."""
    print("="*80)
    print("EXTRACTING METRICS FROM OUTPUT FILES")
    print("="*80)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Results Directory: {RESULTS_DIR}")
    print(f"Test Mode: {TEST_MODE}")
    if TEST_MODE:
        print(f"Test Limit: {TEST_LIMIT} files per folder")
    print(f"Folders to process: {len(OUTPUT_FOLDERS)}")

    # Create results directory
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Process all folders
    results = []

    async with aiohttp.ClientSession() as session:
        for folder_name in OUTPUT_FOLDERS:
            result = await process_folder(session, folder_name)
            results.append(result)

    # Print final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    total_processed = 0
    total_failed = 0

    for result in results:
        if result["skipped"]:
            print(f"{result['folder']}: SKIPPED (directory not found)")
        else:
            print(f"{result['folder']}: {result['processed']}/{result['total']} processed, {result['failed']} failed")
            total_processed += result['processed']
            total_failed += result['failed']

    print(f"\nTOTAL: {total_processed} files processed, {total_failed} failed")

    # Save summary
    summary_file = RESULTS_DIR / "processing_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "processed_at": datetime.now().isoformat(),
            "test_mode": TEST_MODE,
            "test_limit": TEST_LIMIT if TEST_MODE else None,
            "total_processed": total_processed,
            "total_failed": total_failed,
            "folders": results
        }, f, indent=2)

    print(f"\nSummary saved to: {summary_file}")
    print("\n✓ Processing complete!")


if __name__ == "__main__":
    asyncio.run(main())
