#!/usr/bin/env python3
"""
Script to process Cochrane JSON files and send them to the agentic webhook for PLS generation.
Processes files asynchronously and saves results immediately as they complete.
"""

import asyncio
import aiohttp
import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Configuration
WEBHOOK_URL = "http://localhost:5678/webhook/b38ce007-17ed-4b4a-b8a8-f1bf8bd71262"  # Update this URL to the correct one
CONCURRENT_REQUESTS = 30
INPUT_DIR = "data/training_data/cochrane/test_jsons"
OUTPUT_DIR = "outputs/baseline_gpt_oss_20b"
PROGRESS_FILE = "outputs/baseline_gpt_oss_20b/progress.json"
MODEL_NAME = "baseline-gpt-oss-20b"

def load_progress() -> Dict[str, Any]:
    """Load processing progress from file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        "processed_files": [],
        "failed_files": [],
        "total_processed": 0,
        "last_updated": None
    }

def save_progress(progress: Dict[str, Any]) -> None:
    """Save processing progress to file."""
    progress["last_updated"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def load_cochrane_json(file_path: str) -> Dict[str, Any]:
    """Load and parse a Cochrane JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_payload(data: Dict[str, Any], cochrane_id: str, model_name: str) -> Dict[str, Any]:
    """Create request payload with model, cochrane_review_id, title, and abstract."""
    return {
        "model": model_name,
        "cochrane_review_id": cochrane_id,
        "title": data.get("title", ""),
        "abstract": data.get("abstract", "")
    }

async def save_result(result: Dict[str, Any]) -> None:
    """Save individual result immediately to file."""
    output_file = os.path.join(OUTPUT_DIR, f"{result['filename']}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {result['filename']} ({result['processing_time']:.2f}s)")

async def process_single_file(session: aiohttp.ClientSession, file_path: str, progress: Dict[str, Any]) -> None:
    """Process a single file and save result immediately."""
    filename = os.path.basename(file_path).replace(".json", "")
    
    try:
        # Load data
        data = load_cochrane_json(file_path)
        cochrane_id = data.get("cochrane_review_id", filename)

        # Prepare request payload with model name
        payload = create_payload(data, cochrane_id, MODEL_NAME)
        
        start_time = time.time()
        
        # Send request with timeout
        timeout = aiohttp.ClientTimeout(total=1200)  # 20 minutes timeout
        async with session.post(WEBHOOK_URL, json=payload, timeout=timeout) as response:
            processing_time = time.time() - start_time
            response_data = await response.json()
            
            result = {
                "cochrane_id": cochrane_id,
                "filename": filename,
                "title": data.get("title", ""),
                "year": str(data.get("year", "")),
                "authors": data.get("authors", ""),
                "processing_time": processing_time,
                "status_code": response.status,
                "response": response_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Check for failure conditions
            response_output = response_data.get("output", "")
            
            if response.status == 500:
                error_msg = f"Server error (status_code: 500)"
                print(f"✗ Failed: {filename} - {error_msg}")
                progress["failed_files"].append({
                    "filename": filename + ".json",
                    "error": error_msg,
                    "processing_time": processing_time
                })
                save_progress(progress)
            elif not response_output or response_output.strip() == "":
                error_msg = f"Empty response output (status_code: {response.status})"
                print(f"✗ Failed: {filename} - {error_msg}")
                progress["failed_files"].append({
                    "filename": filename + ".json",
                    "error": error_msg,
                    "processing_time": processing_time
                })
                save_progress(progress)
            else:
                # Save immediately only if truly successful
                await save_result(result)
                
                # Update progress
                progress["processed_files"].append(filename + ".json")
                progress["total_processed"] += 1
                save_progress(progress)
            
    except asyncio.TimeoutError:
        processing_time = time.time() - start_time
        error_msg = f"Timeout after {processing_time:.2f}s"
        print(f"✗ Failed: {filename} - {error_msg}")
        progress["failed_files"].append({
            "filename": filename + ".json",
            "error": error_msg,
            "processing_time": processing_time
        })
        save_progress(progress)
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        print(f"✗ Failed: {filename} - {error_msg}")
        progress["failed_files"].append({
            "filename": filename + ".json",
            "error": error_msg,
            "processing_time": processing_time
        })
        save_progress(progress)

async def process_batch(session: aiohttp.ClientSession, file_batch: List[str], progress: Dict[str, Any]) -> None:
    """Process a batch of files concurrently."""
    tasks = []
    
    for file_path in file_batch:
        task = process_single_file(session, file_path, progress)
        tasks.append(task)
    
    # Execute batch concurrently
    await asyncio.gather(*tasks, return_exceptions=True)

async def main(retry_failed=True):
    """Main processing function.
    
    Args:
        retry_failed: If True, retry previously failed files. If False, skip them.
    """
    print("Starting Cochrane PLS generation with agentic...")
    
    # Load progress
    progress = load_progress()
    print(f"Loaded progress: {progress['total_processed']} files already processed")
    if progress['failed_files']:
        print(f"Found {len(progress['failed_files'])} previously failed files")
    
    # Get all JSON files
    json_files = []
    processed_set = set(progress["processed_files"])
    
    # If not retrying failed, add them to the processed set to skip them
    if not retry_failed:
        # Handle both old format (list of strings) and new format (list of dicts)
        if progress['failed_files']:
            if isinstance(progress['failed_files'][0], dict):
                failed_set = set([f['filename'] for f in progress['failed_files']])
            else:
                failed_set = set(progress['failed_files'])
            processed_set = processed_set.union(failed_set)
            print("Skipping previously failed files")
    else:
        if progress['failed_files']:
            print("Will retry previously failed files")
            # Clear failed files list since we're retrying them
            progress['failed_files'] = []
            save_progress(progress)
    
    for file_path in Path(INPUT_DIR).glob("*.json"):
        if file_path.name not in processed_set:
            json_files.append(str(file_path))
    
    if not json_files:
        print("No new files to process!")
        return
    
    print(f"Found {len(json_files)} files to process")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Process files in batches
    connector = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS)
    timeout = aiohttp.ClientTimeout(total=1200)  # 20 minutes default timeout
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i in range(0, len(json_files), CONCURRENT_REQUESTS):
            batch = json_files[i:i + CONCURRENT_REQUESTS]
            batch_num = i // CONCURRENT_REQUESTS + 1
            total_batches = (len(json_files) + CONCURRENT_REQUESTS - 1) // CONCURRENT_REQUESTS
            
            print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} files)...")
            await process_batch(session, batch, progress)
            
            # Small delay between batches to be respectful
            if i + CONCURRENT_REQUESTS < len(json_files):
                await asyncio.sleep(1)
    
    # Final summary
    print(f"\n=== Processing Complete ===")
    print(f"Total processed: {progress['total_processed']}")
    print(f"Failed: {len(progress['failed_files'])}")
    
    if progress['failed_files']:
        print("\nFailed files:")
        for failed in progress['failed_files']:
            print(f"  - {failed['filename']}: {failed['error']}")

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    retry_failed = True  # Default to retrying failed files
    if len(sys.argv) > 1:
        if sys.argv[1] == "--skip-failed":
            retry_failed = False
        elif sys.argv[1] == "--help":
            print("Usage: python baseline_gpt_oss_20b.py [--skip-failed]")
            print("  --skip-failed: Skip previously failed files instead of retrying them")
            print("  By default, the script will retry previously failed files")
            sys.exit(0)
    
    asyncio.run(main(retry_failed=retry_failed))