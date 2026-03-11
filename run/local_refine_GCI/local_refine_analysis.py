#!/usr/bin/env python3
"""
Localized Wake Refinement Analysis Script for OpenFOAM Simulations

This script:
1. Extracts force coefficients from localized wake refinement cases
2. Performs Richardson extrapolation and GCI calculation
3. Compares results against the uniform refinement study
4. Generates convergence plots and a comparison report
"""

import os
import re
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path to reuse grid_convergence_analysis module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from grid_conv_study.grid_convergence_analysis import GridConvergenceAnalyzer


class LocalRefineAnalyzer(GridConvergenceAnalyzer):
    """Analyze localized wake refinement study results"""

    def __init__(self, case_dirs: List[str], refinement_ratios: List[float] = None,
                 uniform_results_dir: str = None):
        super().__init__(case_dirs, refinement_ratios)
        self.uniform_results_dir = Path(uniform_results_dir) if uniform_results_dir else None
        self.uniform_results = {}

    def load_uniform_results(self):
        """Load results from the uniform grid convergence study for comparison"""
        if self.uniform_results_dir is None:
            return

        report_file = self.uniform_results_dir / "convergence_report.txt"
        if not report_file.exists():
            print(f"Warning: Uniform study report not found: {report_file}")
            return

        with open(report_file, 'r') as f:
            content = f.read()

        # Parse GCI values from the report
        for qty in ['Cd', 'Cl', 'Cm']:
            pattern = rf'{qty} Analysis:.*?GCI \(fine mesh\):\s+([\d.]+)%'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                self.uniform_results[f'{qty}_GCI'] = float(match.group(1))

            # Parse values
            pattern = rf"{qty} Analysis:.*?Values \(coarse to fine\):\s+\[(.*?)\]"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                vals_str = match.group(1)
                vals = [float(v.strip().strip("'")) for v in vals_str.split(',')]
                self.uniform_results[f'{qty}_values'] = vals

    def generate_comparison_report(self, output_file: Path = None):
        """Generate a comparison report between localized and uniform refinement"""
        analysis = self.analyze_convergence()

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("LOCALIZED WAKE REFINEMENT STUDY REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("Study Purpose: Address Reviewer 2 major comment #1")
        report_lines.append("  'Consider adding localized wake refinement or at least")
        report_lines.append("   discuss limitations more explicitly.'")
        report_lines.append("")

        # Case information
        report_lines.append("Cases (coarse to fine wake refinement):")
        for i, case_dir in enumerate(self.case_dirs):
            cell_count = self.cell_counts.get(case_dir.name, "N/A")
            if isinstance(cell_count, int):
                cell_count = f"{cell_count:,}"
            report_lines.append(f"  Level {i+1}: {case_dir.name} ({cell_count} cells)")
        report_lines.append("")

        # Refinement strategy
        report_lines.append("Refinement Strategy:")
        report_lines.append("  Base mesh:    medium blockMesh (30x50x25)")
        report_lines.append("  Building box: (-1,-0.7,0) to (8,0.7,2.5) at level 2")
        report_lines.append("  Wake box:     (-20,-90,0) to (20,0,50)")
        report_lines.append("    fine_wake:   wake level 1 (baseline, ~217K cells)")
        report_lines.append("    coarse_wake: wake level 2 (~1.34M cells)")
        report_lines.append("    medium_wake: wake level 3 (~10.4M cells)")
        report_lines.append("")

        # Results for each quantity
        quantities = ['Cd', 'Cl', 'Cm']
        for qty in quantities:
            if qty not in analysis:
                continue

            report_lines.append(f"\n{qty} Analysis:")
            report_lines.append("-" * 80)

            values = analysis[qty]['values']
            report_lines.append(f"  Values (coarse to fine): {[f'{v:.6f}' for v in values]}")

            if 'extrapolated' in analysis[qty]:
                report_lines.append(f"  Extrapolated value: {analysis[qty]['extrapolated']:.6f}")
                report_lines.append(f"  Order of accuracy (p): {analysis[qty]['order_of_accuracy']:.3f}")
                gci = analysis[qty]['GCI_fine'] * 100
                report_lines.append(f"  GCI (fine mesh): {gci:.2f}%")
                report_lines.append(f"  Convergence ratio (R): {analysis[qty]['convergence_ratio']:.3f}")
                report_lines.append(f"  Convergence type: {analysis[qty]['convergence_type']}")

            # Calculate relative differences
            if len(values) >= 2:
                diff = abs((values[-1] - values[-2]) / values[-1]) * 100 if abs(values[-1]) > 1e-10 else abs(values[-1] - values[-2])
                report_lines.append(f"  Relative difference (fine - medium): {diff:.2f}%")

            # Comparison with uniform refinement
            uniform_gci_key = f'{qty}_GCI'
            if uniform_gci_key in self.uniform_results:
                uniform_gci = self.uniform_results[uniform_gci_key]
                local_gci = analysis[qty]['GCI_fine'] * 100
                report_lines.append(f"")
                report_lines.append(f"  Comparison with uniform refinement:")
                report_lines.append(f"    Uniform GCI:  {uniform_gci:.2f}%")
                report_lines.append(f"    Local GCI:    {local_gci:.2f}%")
                if local_gci < uniform_gci:
                    improvement = ((uniform_gci - local_gci) / uniform_gci) * 100
                    report_lines.append(f"    Improvement:  {improvement:.1f}% reduction in GCI")
                else:
                    report_lines.append(f"    No improvement over uniform refinement")

        # Summary
        report_lines.append("")
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("SUMMARY")
        report_lines.append("=" * 80)
        report_lines.append("")

        gci_results = {}
        for qty in quantities:
            if qty in analysis and 'GCI_fine' in analysis[qty]:
                gci_results[qty] = analysis[qty]['GCI_fine'] * 100

        if gci_results:
            cd_gci = gci_results.get('Cd', float('nan'))
            report_lines.append(f"Cd GCI (localized wake refinement): {cd_gci:.2f}%")

            if 'Cd_GCI' in self.uniform_results:
                uniform_cd_gci = self.uniform_results['Cd_GCI']
                report_lines.append(f"Cd GCI (uniform refinement):        {uniform_cd_gci:.2f}%")

                if cd_gci < 5.0:
                    report_lines.append(f"")
                    report_lines.append(f"Localized wake refinement achieves Cd GCI < 5%,")
                    report_lines.append(f"meeting the convergence criterion.")
                elif cd_gci < uniform_cd_gci:
                    report_lines.append(f"")
                    report_lines.append(f"Localized wake refinement reduces Cd GCI from")
                    report_lines.append(f"{uniform_cd_gci:.2f}% to {cd_gci:.2f}%, though still above the 5% target.")
                else:
                    report_lines.append(f"")
                    report_lines.append(f"Localized wake refinement did not improve Cd GCI.")
                    report_lines.append(f"This suggests the current mesh is adequate for the")
                    report_lines.append(f"quantities of interest, or further refinement in")
                    report_lines.append(f"other regions may be needed.")

        # Cell count comparison
        if self.cell_counts:
            report_lines.append("")
            report_lines.append("Cell Count Comparison:")
            for case_dir in self.case_dirs:
                if case_dir.name in self.cell_counts:
                    report_lines.append(f"  {case_dir.name}: {self.cell_counts[case_dir.name]:,} cells")

        report_lines.append("")
        report_lines.append("=" * 80)

        report_text = "\n".join(report_lines)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"Report saved to {output_file}")
        else:
            print(report_text)

        return report_text

    def plot_comparison(self, output_dir: Path = None):
        """Generate comparison plots between localized and uniform refinement"""
        if output_dir is None:
            output_dir = Path.cwd()
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        analysis = self.analyze_convergence()

        # Plot: GCI comparison bar chart
        quantities = ['Cd', 'Cl', 'Cm']
        local_gcis = []
        uniform_gcis = []
        labels = []

        for qty in quantities:
            if qty in analysis and 'GCI_fine' in analysis[qty]:
                labels.append(qty)
                local_gcis.append(analysis[qty]['GCI_fine'] * 100)
                uniform_gci_key = f'{qty}_GCI'
                if uniform_gci_key in self.uniform_results:
                    uniform_gcis.append(self.uniform_results[uniform_gci_key])
                else:
                    uniform_gcis.append(0)

        if labels:
            fig, ax = plt.subplots(figsize=(10, 6))
            x = np.arange(len(labels))
            width = 0.35

            bars1 = ax.bar(x - width/2, uniform_gcis, width, label='Uniform Refinement', color='#2196F3', alpha=0.8)
            bars2 = ax.bar(x + width/2, local_gcis, width, label='Localized Wake Refinement', color='#FF9800', alpha=0.8)

            ax.axhline(y=5.0, color='r', linestyle='--', linewidth=1.5, label='5% GCI Target')
            ax.set_xlabel('Force Coefficient', fontsize=12)
            ax.set_ylabel('GCI (%)', fontsize=12)
            ax.set_title('Grid Convergence Index: Uniform vs Localized Wake Refinement', fontsize=14)
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')

            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=10)
            for bar in bars2:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=10)

            plt.tight_layout()
            plt.savefig(output_dir / 'gci_comparison.png', dpi=300, bbox_inches='tight')
            print(f"Saved GCI comparison plot to {output_dir / 'gci_comparison.png'}")

        # Also generate standard convergence plots
        self.plot_convergence(output_dir=output_dir)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Localized Wake Refinement Analysis for OpenFOAM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python local_refine_analysis.py coarse_wake medium_wake fine_wake
  python local_refine_analysis.py coarse_wake medium_wake fine_wake --output results
  python local_refine_analysis.py coarse_wake medium_wake fine_wake --uniform-results ../grid_conv_study/results
        """
    )
    parser.add_argument('cases', nargs='+',
                        help='Case directories (coarse to fine). Can be relative or absolute paths.')
    parser.add_argument('--time', type=float, default=None,
                        help='Time to extract results (default: last time step)')
    parser.add_argument('--output', type=str, default='results',
                        help='Output directory for plots and report (default: results)')
    parser.add_argument('--refinement-ratios', nargs='+', type=float, default=None,
                        help='Refinement ratios (default: 2.0 for all)')
    parser.add_argument('--uniform-results', type=str, default=None,
                        help='Path to uniform refinement results directory for comparison')

    args = parser.parse_args()

    # Resolve case directories
    resolved_cases = []
    for case in args.cases:
        case_path = Path(case)
        if not case_path.is_absolute():
            case_path = Path.cwd() / case_path
        resolved_cases.append(str(case_path))

    # Auto-detect uniform results directory
    uniform_dir = args.uniform_results
    if uniform_dir is None:
        # Try default location relative to this script
        default_uniform = Path(__file__).resolve().parent.parent / "grid_conv_study" / "results"
        if default_uniform.exists():
            uniform_dir = str(default_uniform)
            print(f"Auto-detected uniform results at: {uniform_dir}")

    # Create analyzer
    analyzer = LocalRefineAnalyzer(
        resolved_cases,
        args.refinement_ratios,
        uniform_results_dir=uniform_dir
    )

    # Collect results
    print("Collecting results from cases...")
    success = analyzer.collect_results(time=args.time)

    if not success:
        print("\nCannot proceed with analysis - missing simulation results.")
        return 1

    # Load uniform results for comparison
    if uniform_dir:
        print("\nLoading uniform refinement results for comparison...")
        analyzer.load_uniform_results()

    # Analyze convergence
    print("\nAnalyzing convergence...")
    try:
        analysis = analyzer.analyze_convergence()
    except ValueError as e:
        print(f"\nError: {e}")
        return 1

    # Resolve output directory
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir

    # Generate plots
    print("\nGenerating plots...")
    analyzer.plot_comparison(output_dir=output_dir)

    # Generate comparison report
    print("\nGenerating comparison report...")
    output_dir.mkdir(parents=True, exist_ok=True)
    analyzer.generate_comparison_report(output_file=output_dir / 'local_refine_report.txt')

    # Also generate standard report
    analyzer.generate_report(output_file=output_dir / 'convergence_report.txt')

    print(f"\nAnalysis complete! Results saved to {output_dir}")
    return 0


if __name__ == '__main__':
    main()
