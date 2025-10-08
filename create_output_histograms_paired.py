#!/usr/bin/env python3
"""
Script to create paired histograms comparing agentic vs baseline models.
Each subplot shows the agentic model overlaid with its baseline.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# Configuration
RESULTS_DIR = Path("outputs/results")
FIGURES_DIR = Path("figures/output_metrics_paired")
FIGURE_DPI = 300
FIGURE_FORMAT = 'png'

# Metrics to plot
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

# Pairs of (agentic_folder, baseline_folder, display_name)
MODEL_PAIRS = [
    ("original", None, "Original"),  # Original has no baseline pair, shown first
    ("agentic_gemini_2_5_pro", "baseline_gemini_2_5_pro", "Gemini 2.5 Pro"),
    ("agentic_old_gemini_2_5_pro", "baseline_gemini_2_5_pro", "Old Gemini 2.5 Pro"),
    ("agentic_gpt_oss_120b", "baseline_gpt_oss_120b", "GPT-OSS 120B"),
    ("agentic_old_gpt-oss-120B", "baseline_gpt_oss_120b", "Old GPT-OSS 120B"),
    ("agentic_llama_3_3_70b", "baseline_llama_3_3_70b", "Llama 3.3 70B"),
    ("agentic_llama_3_3_70b_evaluator_gemini_2_5_flash", "baseline_llama_3_3_70b", "Llama 3.3 70B\n(Evaluator Gemini Flash)"),
    ("agentic_old_gpt_5", "baseline_gpt_5", "Old GPT-5"),
]

# Readable names for metrics
METRIC_NAMES = {
    "words": "Word Count",
    "sentences": "Sentence Count",
    "words_per_sentence": "Words per Sentence",
    "passive_voice": "Passive Voice",
    "active_voice": "Active Voice",
    "pronouns": "Pronouns",
    "nominalization": "Nominalization",
    "nouns": "Nouns",
    "flesch_reading_ease": "Flesch Reading Ease",
    "flesch_kincaid_grade": "Flesch-Kincaid Grade",
    "automated_readability_index": "Automated Readability Index",
    "coleman_liau_index": "Coleman-Liau Index",
    "gunning_fog_index": "Gunning Fog Index",
    "lix": "LIX",
    "rix": "RIX",
    "smog_index": "SMOG Index",
    "dale_chall_readability": "Dale-Chall Readability",
    "complex_words_dc": "Complex Words (Dale-Chall)",
    "complex_words": "Complex Words",
    "long_words": "Long Words",
}


def collect_metrics_from_results() -> Dict[str, Dict[str, List[float]]]:
    """Collect all metric values from saved result files."""
    print("Collecting metrics from results...")

    all_metrics = {}

    # Get all unique folders from pairs
    folders = set()
    for agentic, baseline, _ in MODEL_PAIRS:
        folders.add(agentic)
        if baseline:
            folders.add(baseline)

    for folder in folders:
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
        print(f"  ✓ {folder}: {len(json_files)} files, {len(folder_metrics)} metrics")

    return all_metrics


def create_paired_histogram(all_metrics: Dict[str, Dict[str, List[float]]],
                            metric_name: str, output_dir: Path):
    """Create a 4x2 grid of paired histograms (agentic vs baseline) with shared scales."""

    # First pass: collect all values to determine global scales
    all_values_global = []
    for agentic_folder, baseline_folder, _ in MODEL_PAIRS:
        agentic_values = all_metrics.get(agentic_folder, {}).get(metric_name, [])
        all_values_global.extend(agentic_values)

        if baseline_folder:
            baseline_values = all_metrics.get(baseline_folder, {}).get(metric_name, [])
            all_values_global.extend(baseline_values)

    if not all_values_global:
        print(f"  ⚠ No data for metric '{metric_name}'")
        return

    # Calculate global bin edges
    bins = 30
    global_min = min(all_values_global)
    global_max = max(all_values_global)
    bin_edges = np.linspace(global_min, global_max, bins + 1)

    # Calculate all histograms to find max frequency
    max_frequency = 0
    for agentic_folder, baseline_folder, _ in MODEL_PAIRS:
        agentic_values = all_metrics.get(agentic_folder, {}).get(metric_name, [])
        if agentic_values:
            hist, _ = np.histogram(agentic_values, bins=bin_edges)
            max_frequency = max(max_frequency, hist.max())

        if baseline_folder:
            baseline_values = all_metrics.get(baseline_folder, {}).get(metric_name, [])
            if baseline_values:
                hist, _ = np.histogram(baseline_values, bins=bin_edges)
                max_frequency = max(max_frequency, hist.max())

    # Add 10% padding to max frequency for visual clarity
    y_max = max_frequency * 1.1

    # Create figure with 4x2 subplots
    fig, axes = plt.subplots(4, 2, figsize=(14, 16), dpi=FIGURE_DPI)
    axes = axes.flatten()

    # Second pass: create plots with shared scales
    for idx, (agentic_folder, baseline_folder, display_name) in enumerate(MODEL_PAIRS):
        if idx >= 8:  # Safety check
            break

        ax = axes[idx]

        # Get metric values for agentic
        agentic_values = all_metrics.get(agentic_folder, {}).get(metric_name, [])

        if not agentic_values:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(display_name, fontsize=11, fontweight='bold')
            ax.axis('off')
            continue

        # Get baseline values if exists
        baseline_values = []
        if baseline_folder:
            baseline_values = all_metrics.get(baseline_folder, {}).get(metric_name, [])

        # Plot agentic histogram with shared bins
        agentic_label = 'Agentic' if baseline_folder else None
        ax.hist(agentic_values, bins=bin_edges, alpha=0.7, color='#1f77b4',
               label=agentic_label)

        # Plot baseline histogram if exists
        if baseline_values:
            ax.hist(baseline_values, bins=bin_edges, alpha=0.7, color='#ff7f0e',
                   label='Baseline')

        # Set shared scales
        ax.set_xlim(global_min, global_max)
        ax.set_ylim(0, y_max)

        ax.set_xlabel(METRIC_NAMES.get(metric_name, metric_name), fontsize=10)
        ax.set_ylabel('Frequency', fontsize=10)
        ax.set_title(display_name, fontsize=11, fontweight='bold')

        # Only show legend if there are labels
        if baseline_folder or agentic_label:
            ax.legend(loc='upper right', fontsize=7, framealpha=0.9)

        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.tick_params(labelsize=9)

    # Add main title
    fig.suptitle(f'Distribution of {METRIC_NAMES.get(metric_name, metric_name)} - Agentic vs Baseline',
                fontsize=16, fontweight='bold', y=0.995)

    plt.tight_layout()

    # Save figure
    output_file = output_dir / f"{metric_name}_paired_distribution.{FIGURE_FORMAT}"
    plt.savefig(output_file, dpi=FIGURE_DPI, bbox_inches='tight')
    print(f"  ✓ Saved: {output_file.name}")
    plt.close()


def main():
    """Main execution function."""
    print("="*80)
    print("CREATING PAIRED OUTPUT HISTOGRAMS")
    print("="*80)
    print(f"Results Directory: {RESULTS_DIR}")
    print(f"Figures Directory: {FIGURES_DIR}")
    print(f"Metrics to plot: {len(METRICS)}")
    print(f"Model pairs: {len(MODEL_PAIRS)}")

    # Create output directory
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Collect metrics
    all_metrics = collect_metrics_from_results()

    if not all_metrics:
        print("\n✗ No metrics collected. Please run extract_metrics_from_outputs.py first.")
        return

    # Create histograms for each metric
    print(f"\nCreating paired histograms...")

    for metric_name in METRICS:
        create_paired_histogram(all_metrics, metric_name, FIGURES_DIR)

    print(f"\n✓ All paired histograms created successfully!")
    print(f"  Location: {FIGURES_DIR}")
    print(f"  Total figures: {len(METRICS)}")


if __name__ == "__main__":
    main()
