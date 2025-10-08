#!/usr/bin/env python3
"""
Script to generate a summary JSON with statistics for all metrics across all models.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Configuration
RESULTS_DIR = Path("outputs/results")
OUTPUT_FILE = Path("outputs/results/metrics_summary.json")

# All folders to analyze
FOLDERS = [
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

# Metrics to summarize
METRICS = [
    "words",
    "sentences",
    "words_per_sentence",
    "passive_voice",
    "active_voice",
    "pronouns",
    "nominalization",
    "nouns",
    "flesch_reading_ease",
    "flesch_kincaid_grade",
    "automated_readability_index",
    "coleman_liau_index",
    "gunning_fog_index",
    "lix",
    "rix",
    "smog_index",
    "dale_chall_readability",
    "complex_words_dc",
    "complex_words",
    "long_words",
]


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """Calculate statistics for a list of values."""
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "q25": None,
            "q75": None,
        }

    return {
        "count": len(values),
        "mean": round(float(np.mean(values)), 2),
        "median": round(float(np.median(values)), 2),
        "std": round(float(np.std(values)), 2),
        "min": round(float(np.min(values)), 2),
        "max": round(float(np.max(values)), 2),
        "q25": round(float(np.percentile(values, 25)), 2),
        "q75": round(float(np.percentile(values, 75)), 2),
    }


def collect_metrics_from_results() -> Dict[str, Dict[str, List[float]]]:
    """Collect all metric values from saved result files."""
    print("Collecting metrics from results...")

    all_metrics = {}

    for folder in FOLDERS:
        folder_dir = RESULTS_DIR / folder

        if not folder_dir.exists():
            print(f"  ⚠ Folder not found: {folder}")
            continue

        # Initialize metrics for this folder
        folder_metrics = defaultdict(list)

        # Read all JSON files
        json_files = list(folder_dir.glob("*.json"))

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Extract metrics from linguistic_evaluation
                linguistic_eval = data.get("metrics", {}).get("linguistic_evaluation", {})

                for metric_name in METRICS:
                    if metric_name in linguistic_eval:
                        value = linguistic_eval[metric_name].get("value")
                        if value is not None:
                            folder_metrics[metric_name].append(value)

            except Exception as e:
                print(f"    ✗ Error reading {json_file}: {e}")

        all_metrics[folder] = dict(folder_metrics)
        print(f"  ✓ {folder}: {len(json_files)} files processed")

    return all_metrics


def generate_summary(all_metrics: Dict[str, Dict[str, List[float]]]) -> Dict[str, Any]:
    """Generate summary statistics for all metrics across all folders."""
    print("\nGenerating summary statistics...")

    summary = {}

    for folder, metrics in all_metrics.items():
        folder_summary = {}

        for metric_name in METRICS:
            values = metrics.get(metric_name, [])
            folder_summary[metric_name] = calculate_statistics(values)

        summary[folder] = folder_summary
        print(f"  ✓ {folder}: {len([m for m in folder_summary.values() if m['count'] > 0])} metrics summarized")

    return summary


def main():
    """Main execution function."""
    print("="*80)
    print("GENERATING METRICS SUMMARY")
    print("="*80)
    print(f"Results Directory: {RESULTS_DIR}")
    print(f"Output File: {OUTPUT_FILE}")
    print(f"Folders to analyze: {len(FOLDERS)}")
    print(f"Metrics to summarize: {len(METRICS)}")

    # Collect metrics
    all_metrics = collect_metrics_from_results()

    if not all_metrics:
        print("\n✗ No metrics collected. Please run extract_metrics_from_outputs.py first.")
        return

    # Generate summary
    summary = generate_summary(all_metrics)

    # Save summary to JSON
    print(f"\nSaving summary to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Summary generated successfully!")
    print(f"  Total models: {len(summary)}")
    print(f"  Total metrics per model: {len(METRICS)}")
    print(f"  Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
