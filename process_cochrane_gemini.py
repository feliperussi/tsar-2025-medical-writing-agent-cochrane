#!/usr/bin/env python3
"""
Script to process Cochrane JSON files and send them to the gemini webhook for PLS generation.
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
WEBHOOK_URL = "http://localhost:5678/webhook/852bfcf1-f053-4c69-bbba-8b8757f13c44/chat"  # Update this URL to the correct one
CONCURRENT_REQUESTS = 15
INPUT_DIR = "data/training_data/cochrane/test_jsons"
OUTPUT_DIR = "outputs/gemini"
PROGRESS_FILE = "outputs/gemini/progress.json"

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

def create_chat_input(data: Dict[str, Any]) -> str:
    """Create chat input by concatenating title and abstract."""
    title = data.get("title", "")
    abstract = data.get("abstract", "")
    return f"{title}\n\n{abstract}"

async def save_result(result: Dict[str, Any]) -> None:
    """Save individual result immediately to file."""
    output_file = os.path.join(OUTPUT_DIR, f"{result['filename']}.json")
    
    # Count words if output exists
    output_text = result.get("response", {}).get("output", "")
    word_count = len(output_text.split()) if output_text else 0
    result["word_count"] = word_count
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    status = "✓" if 50 <= word_count <= 850 else "⚠"
    print(f"{status} Saved: {result['filename']} ({word_count} words, {result['processing_time']:.2f}s)")

async def process_single_file(session: aiohttp.ClientSession, file_path: str, progress: Dict[str, Any]) -> None:
    """Process a single file and save result immediately."""
    filename = os.path.basename(file_path).replace(".json", "")
    
    # Remove from failed_files if present
    progress["failed_files"] = [
        f for f in progress.get("failed_files", [])
        if not (isinstance(f, dict) and f.get("filename") == filename + ".json") and f != filename + ".json"
    ]
    
    try:
        # Load data
        data = load_cochrane_json(file_path)
        cochrane_id = data.get("cochrane_review_id", filename)
        
        # Prepare request
        chat_input = create_chat_input(data)
        payload = {"chatInput": chat_input}
        
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
    """Process a batch of files concurrently.
    
    Args:
        file_batch: List of file paths
    """
    tasks = []
    
    for file_path in file_batch:
        task = process_single_file(session, file_path, progress)
        tasks.append(task)
    
    # Execute batch concurrently
    await asyncio.gather(*tasks, return_exceptions=True)

def load_reprocess_list() -> List[str]:
    """Load list of files to reprocess from reprocess_list.json."""
    reprocess_file = "outputs/gemini/reprocess_list.json"
    if os.path.exists(reprocess_file):
        with open(reprocess_file, 'r') as f:
            data = json.load(f)
        return data.get("files_to_reprocess", [])
    return []

def verify_processed_files(progress: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    """Verify that processed files actually exist and return missing ones."""
    verified_processed = []
    missing_files = []
    
    for filename in progress["processed_files"]:
        output_file = os.path.join(OUTPUT_DIR, filename)
        if not filename.endswith('.json'):
            output_file = os.path.join(OUTPUT_DIR, f"{filename}.json")
        
        if os.path.exists(output_file):
            verified_processed.append(filename)
        else:
            missing_files.append(filename)
    
    progress["processed_files"] = verified_processed
    progress["total_processed"] = len(verified_processed)
    
    return progress, missing_files

async def main(retry_failed=True):
    """Main processing function.
    
    Args:
        retry_failed: If True, retry previously failed files. If False, skip them.
    """
    print("="*60)
    print("GEMINI PROCESSING SCRIPT")
    print("="*60)
    
    # Load progress
    progress = load_progress()
    
    # Verify processed files exist
    progress, missing_files = verify_processed_files(progress)
    if missing_files:
        print(f"⚠ Found {len(missing_files)} missing output files, will reprocess")
    
    print(f"Verified processed: {progress['total_processed']} files")
    
    # Load reprocess list
    reprocess_list = load_reprocess_list()
    if reprocess_list:
        print(f"Found {len(reprocess_list)} files in reprocess_list.json")
    
    # Get all JSON files
    all_input_files = {f.name for f in Path(INPUT_DIR).glob("*.json")}
    processed_set = set(progress["processed_files"])
    
    # Build list of files to process
    files_to_process = []  # List of file paths
    
    # 1. Add missing output files
    for filename in missing_files:
        base_name = filename.replace('.json', '')
        if f"{base_name}.json" in all_input_files:
            file_path = str(Path(INPUT_DIR) / f"{base_name}.json")
            files_to_process.append(file_path)
    
    # 2. Add failed files if retrying
    if retry_failed and progress['failed_files']:
        print(f"Will retry {len(progress['failed_files'])} failed files")
        for item in progress['failed_files']:
            if isinstance(item, dict):
                filename = item.get('filename', '')
            else:
                filename = str(item)
            
            base_name = filename.replace('.json', '')
            if f"{base_name}.json" in all_input_files:
                file_path = str(Path(INPUT_DIR) / f"{base_name}.json")
                if file_path not in files_to_process:
                    files_to_process.append(file_path)
    
    # 3. Add files from reprocess_list.json
    for filename in reprocess_list:
        base_name = filename.replace('.json', '')
        if f"{base_name}.json" in all_input_files:
            file_path = str(Path(INPUT_DIR) / f"{base_name}.json")
            if file_path not in files_to_process:
                files_to_process.append(file_path)
    
    # 4. Add new unprocessed files
    for file_path in Path(INPUT_DIR).glob("*.json"):
        if file_path.name not in processed_set:
            full_path = str(file_path)
            if full_path not in files_to_process:
                files_to_process.append(full_path)
    
    if not files_to_process:
        print("No files to process! All files are already successfully processed.")
        return
    
    print(f"\nFiles to process: {len(files_to_process)}")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Process files in batches
    connector = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS)
    timeout = aiohttp.ClientTimeout(total=1200)  # 20 minutes default timeout
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i in range(0, len(files_to_process), CONCURRENT_REQUESTS):
            batch = files_to_process[i:i + CONCURRENT_REQUESTS]
            batch_num = i // CONCURRENT_REQUESTS + 1
            total_batches = (len(files_to_process) + CONCURRENT_REQUESTS - 1) // CONCURRENT_REQUESTS
            
            print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} files)...")
            await process_batch(session, batch, progress)
            
            # Small delay between batches to be respectful
            if i + CONCURRENT_REQUESTS < len(files_to_process):
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
            print("Usage: python process_cochrane_gpt_oss_120b.py [--skip-failed]")
            print("  --skip-failed: Skip previously failed files instead of retrying them")
            print("  By default, the script will retry previously failed files")
            sys.exit(0)
    
    asyncio.run(main(retry_failed=retry_failed))