#!/usr/bin/env python3
"""
Performance Analysis: Localized Wake Refinement vs Fine Uniform Mesh

Compares a coarse base mesh with localized wake refinement against
a fine uniform mesh to evaluate accuracy-per-cell and accuracy-per-second.
"""

import os
import re
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from grid_conv_study.grid_convergence_analysis import GridConvergenceAnalyzer


def extract_force_coefficients(case_dir: Path) -> Dict[str, float]:
    """Extract final force coefficients from a case"""
    force_file = case_dir / "postProcessing" / "forceCoeffs1" / "0" / "forceCoeffs.dat"

    if not force_file.exists():
        raise FileNotFoundError(f"Force coefficients file not found: {force_file}")

    with open(force_file, 'r') as f:
        lines = f.readlines()

    # Find header line
    header_idx = None
    for i, line in enumerate(lines):
        if 'Time' in line and 'Cd' in line and 'Cl' in line:
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Could not find header in forceCoeffs.dat")

    # Strip leading '#' from header line so indices match data columns
    header_line = lines[header_idx].lstrip('#').strip()
    header = header_line.split()
    time_idx = header.index('Time')
    cd_idx = header.index('Cd')
    cl_idx = header.index('Cl')
    cm_idx = header.index('Cm')

    # Get last data line
    last_data = None
    for line in reversed(lines):
        if line.strip() and not line.strip().startswith('#'):
            try:
                values = line.split()
                last_data = {
                    'time': float(values[time_idx]),
                    'Cd': float(values[cd_idx]),
                    'Cl': float(values[cl_idx]),
                    'Cm': float(values[cm_idx]),
                }
                break
            except (ValueError, IndexError):
                continue

    if last_data is None:
        raise ValueError("No data found in forceCoeffs.dat")

    return last_data


def extract_cell_count(case_dir: Path) -> Optional[int]:
    """Extract total cell count from snappyHexMesh or simpleFoam log"""
    log_file = case_dir / "log.snappyHexMesh"
    if log_file.exists():
        with open(log_file, 'r') as f:
            content = f.read()
            # Look for final layer mesh cell count
            matches = re.findall(r'Layer mesh\s*:\s*cells:(\d+)', content)
            if matches:
                return int(matches[-1])
            # Fallback to snapped mesh
            matches = re.findall(r'Snapped mesh\s*:\s*cells:(\d+)', content)
            if matches:
                return int(matches[-1])
            # Fallback to refined mesh
            matches = re.findall(r'Refined mesh\s*:\s*cells:(\d+)', content)
            if matches:
                return int(matches[-1])

    log_file = case_dir / "log.simpleFoam"
    if log_file.exists():
        with open(log_file, 'r') as f:
            for line in f:
                match = re.search(r'nCells:\s*(\d+)', line)
                if match:
                    return int(match.group(1))

    return None


def extract_timing(results_dir: Path) -> Dict[str, int]:
    """Extract timing from timing.txt"""
    timing_file = results_dir / "timing.txt"
    timing = {}
    if timing_file.exists():
        with open(timing_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    timing[parts[0]] = int(parts[1])
    return timing


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Performance comparison analysis')
    parser.add_argument('--output', type=str, default='results',
                        help='Output directory (default: results)')
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    fine_dir = script_dir / "fine_uniform"
    local_dir = script_dir / "coarse_local_wake"

    # Extract results
    print("Extracting results...")

    try:
        fine_forces = extract_force_coefficients(fine_dir)
        print(f"  fine_uniform:      Cd={fine_forces['Cd']:.3f}, Cl={fine_forces['Cl']:.3f}, Cm={fine_forces['Cm']:.3f}")
    except Exception as e:
        print(f"  Error reading fine_uniform: {e}")
        return 1

    try:
        local_forces = extract_force_coefficients(local_dir)
        print(f"  coarse_local_wake: Cd={local_forces['Cd']:.3f}, Cl={local_forces['Cl']:.3f}, Cm={local_forces['Cm']:.3f}")
    except Exception as e:
        print(f"  Error reading coarse_local_wake: {e}")
        return 1

    # Cell counts
    fine_cells = extract_cell_count(fine_dir)
    local_cells = extract_cell_count(local_dir)
    print(f"\n  fine_uniform cells:      {fine_cells:,}" if fine_cells else "  fine_uniform cells: N/A")
    print(f"  coarse_local_wake cells: {local_cells:,}" if local_cells else "  coarse_local_wake cells: N/A")

    # Timing
    timing = extract_timing(output_dir)
    fine_time = timing.get('fine_uniform', None)
    local_time = timing.get('coarse_local_wake', None)

    # Compute metrics
    print("\nComputing metrics...")

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("LOCALIZED WAKE REFINEMENT: PERFORMANCE COMPARISON")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("Comparison: coarse base mesh + localized wake refinement")
    report_lines.append("         vs fine uniform mesh")
    report_lines.append("")
    report_lines.append("Setup:")
    report_lines.append("  fine_uniform:      blockMesh 60x100x50, SHM refinementBox level 2")
    report_lines.append("  coarse_local_wake: blockMesh 15x25x12,  SHM refinementBox level 2")
    report_lines.append("                     + wakeRefinementBox (-20,-90,0)-(20,0,50) level 2")
    report_lines.append("")

    # Cell count comparison
    report_lines.append("-" * 80)
    report_lines.append("CELL COUNT COMPARISON")
    report_lines.append("-" * 80)
    if fine_cells and local_cells:
        cell_ratio = fine_cells / local_cells
        report_lines.append(f"  fine_uniform:      {fine_cells:>12,} cells")
        report_lines.append(f"  coarse_local_wake: {local_cells:>12,} cells")
        report_lines.append(f"  Ratio (fine/local): {cell_ratio:.2f}x")
        report_lines.append(f"  Cell savings:       {(1 - local_cells/fine_cells)*100:.1f}%")
    report_lines.append("")

    # Timing comparison
    report_lines.append("-" * 80)
    report_lines.append("TIMING COMPARISON")
    report_lines.append("-" * 80)
    if fine_time and local_time:
        time_ratio = fine_time / local_time if local_time > 0 else float('inf')
        report_lines.append(f"  fine_uniform:      {fine_time:>8d} seconds ({fine_time//60} min)")
        report_lines.append(f"  coarse_local_wake: {local_time:>8d} seconds ({local_time//60} min)")
        report_lines.append(f"  Speedup:            {time_ratio:.2f}x")
        report_lines.append(f"  Time savings:       {(1 - local_time/fine_time)*100:.1f}%")
    else:
        report_lines.append("  Timing data not available (run run_all_cases.sh first)")
    report_lines.append("")

    # Force coefficient comparison
    report_lines.append("-" * 80)
    report_lines.append("FORCE COEFFICIENT COMPARISON")
    report_lines.append("-" * 80)
    report_lines.append(f"  {'Quantity':<10} {'Fine Uniform':>15} {'Coarse+Local':>15} {'Abs Diff':>12} {'Rel Diff (%)':>14}")
    report_lines.append(f"  {'-'*10} {'-'*15} {'-'*15} {'-'*12} {'-'*14}")

    for qty in ['Cd', 'Cl', 'Cm']:
        fine_val = fine_forces[qty]
        local_val = local_forces[qty]
        abs_diff = abs(local_val - fine_val)
        rel_diff = abs(abs_diff / fine_val) * 100 if abs(fine_val) > 1e-10 else float('inf')
        report_lines.append(f"  {qty:<10} {fine_val:>15.3f} {local_val:>15.3f} {abs_diff:>12.3f} {rel_diff:>13.2f}%")

    report_lines.append("")

    # Efficiency metric: accuracy per cell
    report_lines.append("-" * 80)
    report_lines.append("EFFICIENCY METRICS")
    report_lines.append("-" * 80)

    if fine_cells and local_cells:
        cd_diff_fine = 0  # Fine is reference
        cd_diff_local = abs(local_forces['Cd'] - fine_forces['Cd'])
        cd_rel_local = abs(cd_diff_local / fine_forces['Cd']) * 100 if abs(fine_forces['Cd']) > 1e-10 else float('inf')

        report_lines.append(f"  Cd relative difference: {cd_rel_local:.2f}%")
        report_lines.append(f"  Cell count ratio (fine/local): {fine_cells/local_cells:.2f}x")

        if fine_time and local_time:
            report_lines.append(f"  Time ratio (fine/local): {fine_time/local_time:.2f}x")

            # Cost-accuracy trade-off
            if cd_rel_local < 5.0:
                report_lines.append("")
                report_lines.append(f"  RESULT: Localized refinement achieves <5% Cd difference")
                report_lines.append(f"  while using {local_cells/fine_cells*100:.1f}% of the cells")
                report_lines.append(f"  and {local_time/fine_time*100:.1f}% of the compute time.")
            elif cd_rel_local < 10.0:
                report_lines.append("")
                report_lines.append(f"  RESULT: Localized refinement achieves <10% Cd difference")
                report_lines.append(f"  while using {local_cells/fine_cells*100:.1f}% of the cells")
                report_lines.append(f"  and {local_time/fine_time*100:.1f}% of the compute time.")
            else:
                report_lines.append("")
                report_lines.append(f"  RESULT: Localized refinement has {cd_rel_local:.1f}% Cd difference")
                report_lines.append(f"  vs fine mesh, using {local_cells/fine_cells*100:.1f}% of cells")
                report_lines.append(f"  and {local_time/fine_time*100:.1f}% of compute time.")

    report_lines.append("")
    report_lines.append("=" * 80)

    report_text = "\n".join(report_lines)
    print(report_text)

    report_file = output_dir / "performance_report.txt"
    with open(report_file, 'w') as f:
        f.write(report_text)
    print(f"\nReport saved to {report_file}")

    # Generate comparison bar chart
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Plot 1: Force coefficients comparison
    ax = axes[0]
    quantities = ['Cd', 'Cl', 'Cm']
    fine_vals = [fine_forces[q] for q in quantities]
    local_vals = [local_forces[q] for q in quantities]
    x = np.arange(len(quantities))
    width = 0.35
    ax.bar(x - width/2, fine_vals, width, label='Fine Uniform', color='#2196F3', alpha=0.8)
    ax.bar(x + width/2, local_vals, width, label='Coarse + Local Wake', color='#FF9800', alpha=0.8)
    ax.set_xlabel('Force Coefficient')
    ax.set_ylabel('Value')
    ax.set_title('Force Coefficients')
    ax.set_xticks(x)
    ax.set_xticklabels(quantities)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 2: Cell count comparison
    ax = axes[1]
    if fine_cells and local_cells:
        bars = ax.bar(['Fine\nUniform', 'Coarse +\nLocal Wake'],
                       [fine_cells, local_cells],
                       color=['#2196F3', '#FF9800'], alpha=0.8)
        for bar, val in zip(bars, [fine_cells, local_cells]):
            ax.annotate(f'{val:,}', xy=(bar.get_x() + bar.get_width() / 2, val),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
        ax.set_ylabel('Number of Cells')
        ax.set_title('Mesh Size')
        ax.grid(True, alpha=0.3, axis='y')

    # Plot 3: Timing comparison
    ax = axes[2]
    if fine_time and local_time:
        bars = ax.bar(['Fine\nUniform', 'Coarse +\nLocal Wake'],
                       [fine_time, local_time],
                       color=['#2196F3', '#FF9800'], alpha=0.8)
        for bar, val in zip(bars, [fine_time, local_time]):
            ax.annotate(f'{val}s\n({val//60}m)', xy=(bar.get_x() + bar.get_width() / 2, val),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
        ax.set_ylabel('Wall Time (seconds)')
        ax.set_title('Compute Time')
        ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Localized Wake Refinement: Performance Comparison', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'performance_comparison.png', dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_dir / 'performance_comparison.png'}")

    return 0


if __name__ == '__main__':
    main()
