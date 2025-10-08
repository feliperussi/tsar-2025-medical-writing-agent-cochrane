#!/usr/bin/env python3
"""
Script to extract linguistic metrics from original files, separating abstract and PLS.
Creates two folders: 'original' (title+abstract) and 'reference' (title+pls).
"""

import asyncio
import aiohttp
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
METRICS_ENDPOINT = "/tools/pls-evaluation"
ORIGINALS_DIR = Path("data/training_data/cochrane/test_jsons")
RESULTS_DIR = Path("outputs/results")

# Output folders to create
OUTPUT_CONFIGS = [
    {
        "name": "original",
        "description": "Title + Abstract",
        "fields": ["title", "abstract"]
    },
    {
        "name": "reference",
        "description": "PLS (already includes title)",
        "fields": ["pls"]
    }
]


def extract_text_from_json(data: Dict[str, Any], fields: list) -> str:
    """Extract text from specified fields."""
    texts = []
    for field in fields:
        value = data.get(field, "")
        if value:
            texts.append(value)
    return "\n\n".join(texts)


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
                       config: Dict[str, Any], output_dir: Path) -> bool:
    """Process a single file: extract text, get metrics, save results."""

    file_id = file_path.stem  # filename without extension

    try:
        # Load JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract text based on configuration
        text = extract_text_from_json(data, config["fields"])

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
            "folder": config["name"],
            "source_fields": config["fields"],
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


async def process_config(session: aiohttp.ClientSession, config: Dict[str, Any]) -> Dict[str, Any]:
    """Process all files for a given configuration."""

    print(f"\n{'='*80}")
    print(f"Processing: {config['name']} ({config['description']})")
    print(f"Fields: {', '.join(config['fields'])}")
    print(f"{'='*80}")

    if not ORIGINALS_DIR.exists():
        print(f"  ⚠ Directory not found: {ORIGINALS_DIR}")
        return {"config": config["name"], "processed": 0, "failed": 0, "skipped": True}

    # Create output directory
    output_dir = RESULTS_DIR / config["name"]
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all JSON files
    json_files = sorted(list(ORIGINALS_DIR.glob("*.json")))

    print(f"  Found {len(json_files)} files to process")

    # Process files
    processed = 0
    failed = 0

    for file_path in json_files:
        success = await process_file(session, file_path, config, output_dir)
        if success:
            processed += 1
        else:
            failed += 1

    print(f"\n  Summary: {processed} processed, {failed} failed")

    return {
        "config": config["name"],
        "description": config["description"],
        "processed": processed,
        "failed": failed,
        "total": len(json_files),
        "skipped": False
    }


async def main():
    """Main execution function."""
    print("="*80)
    print("EXTRACTING METRICS FROM ORIGINAL FILES (SEPARATED)")
    print("="*80)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Input Directory: {ORIGINALS_DIR}")
    print(f"Results Directory: {RESULTS_DIR}")
    print(f"Configurations: {len(OUTPUT_CONFIGS)}")
    for config in OUTPUT_CONFIGS:
        print(f"  - {config['name']}: {config['description']}")

    # Create results directory
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Process all configurations
    results = []

    async with aiohttp.ClientSession() as session:
        for config in OUTPUT_CONFIGS:
            result = await process_config(session, config)
            results.append(result)

    # Print final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    total_processed = 0
    total_failed = 0

    for result in results:
        if result["skipped"]:
            print(f"{result['config']}: SKIPPED (directory not found)")
        else:
            print(f"{result['config']} ({result['description']}): {result['processed']}/{result['total']} processed, {result['failed']} failed")
            total_processed += result['processed']
            total_failed += result['failed']

    print(f"\nTOTAL: {total_processed} files processed, {total_failed} failed")

    # Save summary
    summary_file = RESULTS_DIR / "original_separated_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "processed_at": datetime.now().isoformat(),
            "total_processed": total_processed,
            "total_failed": total_failed,
            "configurations": results
        }, f, indent=2)

    print(f"\nSummary saved to: {summary_file}")
    print("\n✓ Processing complete!")


if __name__ == "__main__":
    asyncio.run(main())
