#!/usr/bin/env python3
"""
Script to generate a CSV table with mean values for all metrics across all models.
Rows = models, Columns = metrics, Values = mean
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

# Configuration
RESULTS_DIR = Path("outputs/results")
OUTPUT_FILE = Path("outputs/results/metrics_means_table.csv")

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
    "reference",
]

# Metrics to include
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
        print(f"  ✓ {folder}: {len(json_files)} files")

    return all_metrics


def generate_means_table(all_metrics: Dict[str, Dict[str, List[float]]]) -> pd.DataFrame:
    """Generate a DataFrame with mean values for each metric and model."""
    print("\nGenerating means table...")

    # Create dictionary to build DataFrame
    table_data = {}

    for folder in FOLDERS:
        metrics = all_metrics.get(folder, {})
        row_data = {}

        for metric_name in METRICS:
            values = metrics.get(metric_name, [])
            if values:
                row_data[metric_name] = round(float(np.mean(values)), 2)
            else:
                row_data[metric_name] = None

        table_data[folder] = row_data

    # Create DataFrame (transpose so folders are rows, metrics are columns)
    df = pd.DataFrame.from_dict(table_data, orient='index')
    df.index.name = 'model'

    print(f"  ✓ Table created: {len(df)} models x {len(df.columns)} metrics")

    return df


def main():
    """Main execution function."""
    print("="*80)
    print("GENERATING METRICS MEANS TABLE")
    print("="*80)
    print(f"Results Directory: {RESULTS_DIR}")
    print(f"Output File: {OUTPUT_FILE}")
    print(f"Models: {len(FOLDERS)}")
    print(f"Metrics: {len(METRICS)}")

    # Collect metrics
    all_metrics = collect_metrics_from_results()

    if not all_metrics:
        print("\n✗ No metrics collected. Please run extract_metrics_from_outputs.py first.")
        return

    # Generate table
    df = generate_means_table(all_metrics)

    # Save to CSV
    print(f"\nSaving table to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE)

    print(f"\n✓ Table generated successfully!")
    print(f"  Output file: {OUTPUT_FILE}")
    print(f"\nPreview:")
    print(df.head())


if __name__ == "__main__":
    main()
