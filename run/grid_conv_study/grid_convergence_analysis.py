#!/usr/bin/env python3
"""
Grid Convergence Analysis Script for OpenFOAM Simulations

This script:
1. Extracts force coefficients from OpenFOAM results
2. Performs Richardson extrapolation
3. Calculates Grid Convergence Index (GCI)
4. Generates convergence plots
"""

import os
import re
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class GridConvergenceAnalyzer:
    """Analyze grid convergence for OpenFOAM simulations"""
    
    def __init__(self, case_dirs: List[str], refinement_ratios: List[float] = None):
        """
        Initialize analyzer
        
        Args:
            case_dirs: List of case directories in order from coarse to fine
            refinement_ratios: List of refinement ratios (r_i = h_i / h_{i+1})
                             If None, assumes uniform refinement ratio of 2
        """
        self.case_dirs = [Path(d) for d in case_dirs]
        if refinement_ratios is None:
            # Assume uniform refinement ratio of 2
            self.refinement_ratios = [2.0] * (len(case_dirs) - 1)
        else:
            self.refinement_ratios = refinement_ratios
        
        if len(self.refinement_ratios) != len(case_dirs) - 1:
            raise ValueError("Number of refinement ratios must be len(case_dirs) - 1")
        
        self.results = {}
        self.cell_counts = {}
    
    def extract_force_coefficients(self, case_dir: Path, time: float = None) -> Dict[str, float]:
        """
        Extract force coefficients from OpenFOAM results
        
        Args:
            case_dir: Path to OpenFOAM case directory
            time: Time to extract (if None, uses last time in file)
        
        Returns:
            Dictionary with Cd, Cl, Cm values
        """
        force_file = case_dir / "postProcessing" / "forceCoeffs1" / "0" / "forceCoeffs.dat"
        
        if not force_file.exists():
            raise FileNotFoundError(f"Force coefficients file not found: {force_file}")
        
        # Read the file
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
        
        # Parse header to find column indices
        # Strip leading '#' from header line so indices match data columns
        header_line = lines[header_idx].lstrip('#').strip()
        header = header_line.split()
        time_idx = header.index('Time')
        cd_idx = header.index('Cd')
        cl_idx = header.index('Cl')
        cm_idx = header.index('Cm')
        
        # Read data
        data = []
        for line in lines[header_idx + 1:]:
            if line.strip() and not line.strip().startswith('#'):
                try:
                    values = line.split()
                    if len(values) > max(time_idx, cd_idx, cl_idx, cm_idx):
                        t = float(values[time_idx])
                        cd = float(values[cd_idx])
                        cl = float(values[cl_idx])
                        cm = float(values[cm_idx])
                        data.append((t, cd, cl, cm))
                except (ValueError, IndexError):
                    continue
        
        if not data:
            raise ValueError("No data found in forceCoeffs.dat")
        
        # Get value at specified time or last time
        if time is None:
            # Use last time step
            t, cd, cl, cm = data[-1]
        else:
            # Find closest time
            closest = min(data, key=lambda x: abs(x[0] - time))
            t, cd, cl, cm = closest
        
        return {
            'time': t,
            'Cd': cd,
            'Cl': cl,
            'Cm': cm
        }
    
    def extract_cell_count(self, case_dir: Path) -> int:
        """
        Extract total cell count from log file or checkMesh output
        
        Args:
            case_dir: Path to OpenFOAM case directory
        
        Returns:
            Total number of cells
        """
        # Try to get from log.snappyHexMesh
        log_file = case_dir / "log.snappyHexMesh"
        if log_file.exists():
            with open(log_file, 'r') as f:
                content = f.read()
                # Look for "Final mesh has X cells"
                match = re.search(r'Final mesh has (\d+) cells', content)
                if match:
                    return int(match.group(1))
        
        # Try to get from log.simpleFoam (mesh info at start)
        log_file = case_dir / "log.simpleFoam"
        if log_file.exists():
            with open(log_file, 'r') as f:
                for line in f:
                    # Look for "Mesh:  X cells"
                    match = re.search(r'Mesh:\s+(\d+)\s+cells', line)
                    if match:
                        return int(match.group(1))
        
        # If not found, return None (user can manually specify)
        return None
    
    def collect_results(self, time: float = None):
        """Collect results from all cases"""
        missing_results = []
        
        for i, case_dir in enumerate(self.case_dirs):
            if not case_dir.exists():
                print(f"Warning: Case directory not found: {case_dir}")
                continue
            
            print(f"Processing case {i+1}/{len(self.case_dirs)}: {case_dir.name}")
            
            # Extract force coefficients
            try:
                forces = self.extract_force_coefficients(case_dir, time)
                self.results[case_dir.name] = forces
                print(f"  ✓ Successfully extracted force coefficients")
            except FileNotFoundError as e:
                print(f"  ✗ Error: {e}")
                missing_results.append(case_dir.name)
                continue
            except Exception as e:
                print(f"  ✗ Error extracting forces from {case_dir.name}: {e}")
                missing_results.append(case_dir.name)
                continue
            
            # Extract cell count
            cell_count = self.extract_cell_count(case_dir)
            if cell_count:
                self.cell_counts[case_dir.name] = cell_count
                print(f"  ✓ Cell count: {cell_count:,}")
            else:
                print(f"  ⚠ Warning: Could not extract cell count for {case_dir.name}")
        
        # Provide helpful message if results are missing
        if missing_results:
            print("\n" + "=" * 80)
            print("ERROR: Missing simulation results!")
            print("=" * 80)
            print(f"\nThe following cases have not been run yet:")
            for case in missing_results:
                print(f"  - {case}")
            print("\nTo run the simulations, execute:")
            for case in missing_results:
                case_path = next((d for d in self.case_dirs if d.name == case), None)
                if case_path:
                    print(f"  cd {case_path}")
                    print(f"  bash ./Allclean")
                    print(f"  bash ./Allrun")
                    print()
            print("After all simulations complete, run this analysis script again.")
            print("=" * 80)
            return False
        
        return True
    
    def richardson_extrapolation(self, values: List[float], r: float, p: float = None) -> Tuple[float, float, float]:
        """
        Perform Richardson extrapolation
        
        Args:
            values: List of values from coarse to fine [φ_coarse, φ_medium, φ_fine]
            r: Refinement ratio
            p: Order of accuracy (if None, will be calculated)
        
        Returns:
            (extrapolated_value, order_of_accuracy, GCI_fine)
        """
        if len(values) < 3:
            raise ValueError("Need at least 3 values for Richardson extrapolation")
        
        φ_coarse, φ_medium, φ_fine = values[-3], values[-2], values[-1]
        
        # Calculate observed order of accuracy
        if p is None:
            if abs(φ_fine - φ_medium) < 1e-10:
                p = 1.0  # Default if division by zero
            else:
                ε32 = φ_fine - φ_medium
                ε21 = φ_medium - φ_coarse
                if abs(ε21) < 1e-10:
                    p = 1.0
                else:
                    p = np.log(abs(ε32 / ε21)) / np.log(r)
                    # Clamp to reasonable range
                    p = max(0.5, min(3.0, p))
        
        # Calculate extrapolated value
        φ_extrapolated = φ_fine + (φ_fine - φ_medium) / (r**p - 1)
        
        # Calculate Grid Convergence Index (GCI) for fine mesh
        # Using safety factor F_s = 1.25 for 3 grids
        F_s = 1.25
        ε_relative = abs((φ_fine - φ_medium) / φ_fine) if abs(φ_fine) > 1e-10 else abs(φ_fine - φ_medium)
        GCI_fine = (F_s * ε_relative) / (r**p - 1)
        
        return φ_extrapolated, p, GCI_fine
    
    def analyze_convergence(self) -> Dict:
        """
        Analyze convergence for all quantities
        
        Returns:
            Dictionary with convergence analysis results
        """
        if not self.results:
            raise ValueError(
                "No results collected. Run collect_results() first.\n"
                "Make sure all simulations have been completed before running the analysis."
            )
        
        analysis = {}
        
        # Analyze each quantity
        quantities = ['Cd', 'Cl', 'Cm']
        
        for qty in quantities:
            values = [self.results[case.name][qty] for case in self.case_dirs 
                     if case.name in self.results]
            
            if len(values) < 3:
                print(f"Warning: Not enough data points for {qty} analysis")
                continue
            
            # Use last refinement ratio (assuming uniform)
            r = self.refinement_ratios[-1]
            
            # Perform Richardson extrapolation
            try:
                φ_ext, p, GCI = self.richardson_extrapolation(values, r)
                
                # Calculate convergence ratio
                if len(values) >= 3:
                    R = (values[-2] - values[-3]) / (values[-1] - values[-2]) if abs(values[-1] - values[-2]) > 1e-10 else 0
                else:
                    R = 0
                
                analysis[qty] = {
                    'values': values,
                    'extrapolated': φ_ext,
                    'order_of_accuracy': p,
                    'GCI_fine': GCI,
                    'convergence_ratio': R,
                    'convergence_type': self._classify_convergence(R)
                }
            except Exception as e:
                print(f"Error analyzing {qty}: {e}")
                continue
        
        return analysis
    
    def _classify_convergence(self, R: float) -> str:
        """Classify convergence type based on convergence ratio"""
        if abs(R - 1.0) < 0.1:
            return "Monotonic convergence"
        elif R < 0:
            return "Oscillatory convergence"
        elif abs(R) > 1:
            return "Divergence"
        else:
            return "Uncertain"
    
    def plot_convergence(self, output_dir: Path = None):
        """
        Generate convergence plots
        
        Args:
            output_dir: Directory to save plots (if None, uses current directory)
        """
        if output_dir is None:
            output_dir = Path.cwd()
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        analysis = self.analyze_convergence()
        
        # Plot 1: Quantity vs Cell Count
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        quantities = ['Cd', 'Cl', 'Cm']
        
        for idx, qty in enumerate(quantities):
            if qty not in analysis:
                continue
            
            ax = axes[idx]
            values = analysis[qty]['values']
            
            # Get cell counts if available
            if self.cell_counts:
                cell_counts = [self.cell_counts[case.name] for case in self.case_dirs 
                              if case.name in self.cell_counts and case.name in self.results]
                if len(cell_counts) == len(values):
                    ax.loglog(cell_counts, values, 'o-', linewidth=2, markersize=8)
                    ax.set_xlabel('Number of Cells', fontsize=12)
                else:
                    # Use mesh level index
                    mesh_levels = list(range(1, len(values) + 1))
                    ax.plot(mesh_levels, values, 'o-', linewidth=2, markersize=8)
                    ax.set_xlabel('Mesh Level (1=Coarse, 2=Medium, 3=Fine)', fontsize=12)
            else:
                # Use mesh level index
                mesh_levels = list(range(1, len(values) + 1))
                ax.plot(mesh_levels, values, 'o-', linewidth=2, markersize=8)
                ax.set_xlabel('Mesh Level (1=Coarse, 2=Medium, 3=Fine)', fontsize=12)
            
            ax.set_ylabel(f'{qty}', fontsize=12)
            ax.set_title(f'{qty} Convergence', fontsize=14)
            ax.grid(True, alpha=0.3)
            
            # Add extrapolated value
            if 'extrapolated' in analysis[qty]:
                φ_ext = analysis[qty]['extrapolated']
                ax.axhline(y=φ_ext, color='r', linestyle='--', 
                          label=f'Extrapolated: {φ_ext:.4f}')
                ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_dir / 'convergence_plots.png', dpi=300, bbox_inches='tight')
        print(f"Saved convergence plots to {output_dir / 'convergence_plots.png'}")
        
        # Plot 2: Relative error
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for qty in quantities:
            if qty not in analysis:
                continue
            
            values = analysis[qty]['values']
            if len(values) < 2:
                continue
            
            # Calculate relative error with respect to finest mesh
            φ_fine = values[-1]
            relative_errors = [abs((v - φ_fine) / φ_fine) * 100 if abs(φ_fine) > 1e-10 
                              else abs(v - φ_fine) * 100 for v in values[:-1]]
            relative_errors.append(0)  # Fine mesh has 0 error
            
            mesh_levels = list(range(1, len(values) + 1))
            ax.semilogy(mesh_levels, relative_errors, 'o-', linewidth=2, 
                       markersize=8, label=qty)
        
        ax.set_xlabel('Mesh Level', fontsize=12)
        ax.set_ylabel('Relative Error (%)', fontsize=12)
        ax.set_title('Relative Error vs Mesh Level', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.tight_layout()
        plt.savefig(output_dir / 'relative_error_plot.png', dpi=300, bbox_inches='tight')
        print(f"Saved relative error plot to {output_dir / 'relative_error_plot.png'}")
    
    def generate_report(self, output_file: Path = None):
        """
        Generate a text report of convergence analysis
        
        Args:
            output_file: Path to save report (if None, prints to stdout)
        """
        analysis = self.analyze_convergence()
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("GRID CONVERGENCE STUDY REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Case information
        report_lines.append("Case Directories (coarse to fine):")
        for i, case_dir in enumerate(self.case_dirs):
            cell_count = self.cell_counts.get(case_dir.name, "N/A")
            report_lines.append(f"  Level {i+1}: {case_dir.name} ({cell_count} cells)")
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
                report_lines.append(f"  GCI (fine mesh): {analysis[qty]['GCI_fine']*100:.2f}%")
                report_lines.append(f"  Convergence ratio (R): {analysis[qty]['convergence_ratio']:.3f}")
                report_lines.append(f"  Convergence type: {analysis[qty]['convergence_type']}")
            
            # Calculate relative differences
            if len(values) >= 2:
                diff_medium_fine = abs((values[-1] - values[-2]) / values[-1]) * 100 if abs(values[-1]) > 1e-10 else abs(values[-1] - values[-2])
                report_lines.append(f"  Relative difference (fine - medium): {diff_medium_fine:.2f}%")
        
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


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Grid Convergence Analysis for OpenFOAM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run from grid_conv_study directory with default cases (coarse, medium, fine):
  python grid_convergence_analysis.py coarse medium fine
  
  # Run with custom output directory:
  python grid_convergence_analysis.py coarse medium fine --output results
  
  # Run with custom refinement ratios:
  python grid_convergence_analysis.py coarse medium fine --refinement-ratios 2.0 2.0
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
    
    args = parser.parse_args()
    
    # Resolve case directories relative to current working directory
    # This allows the script to work when run from grid_conv_study/
    resolved_cases = []
    for case in args.cases:
        case_path = Path(case)
        if not case_path.is_absolute():
            # If relative path, resolve relative to current working directory
            case_path = Path.cwd() / case_path
        resolved_cases.append(str(case_path))
    
    # Create analyzer
    analyzer = GridConvergenceAnalyzer(resolved_cases, args.refinement_ratios)
    
    # Collect results
    print("Collecting results from cases...")
    success = analyzer.collect_results(time=args.time)
    
    if not success:
        print("\nCannot proceed with analysis - missing simulation results.")
        return 1
    
    # Analyze convergence
    print("\nAnalyzing convergence...")
    try:
        analysis = analyzer.analyze_convergence()
    except ValueError as e:
        print(f"\nError: {e}")
        return 1
    
    # Resolve output directory relative to current working directory
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir
    
    # Generate plots
    print("\nGenerating plots...")
    analyzer.plot_convergence(output_dir=output_dir)
    
    # Generate report
    print("\nGenerating report...")
    output_dir.mkdir(parents=True, exist_ok=True)
    analyzer.generate_report(output_file=output_dir / 'convergence_report.txt')
    
    print(f"\nAnalysis complete! Results saved to {output_dir}")
    return 0


if __name__ == '__main__':
    main()
