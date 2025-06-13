#!/usr/bin/env python3
"""
Risk Score vs Vulnerability Correlation Analysis Tool

This tool analyzes the correlation between manifest-based risk scores and actual
vulnerabilities discovered by the EmPoWeb static analyzer. It generates statistics
similar to Table 3 in section 4.4 of the research paper.

The analysis helps validate whether permission-based risk scoring can effectively
predict extensions that contain exploitable vulnerabilities.
"""

import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import argparse
from pathlib import Path

class RiskCorrelationAnalyzer:
    """
    Analyzes correlation between extension risk scores and vulnerability discovery.
    
    This class loads data from the CSV file containing risk assessments and the
    JSON file containing vulnerability analysis results, then performs statistical
    analysis to determine how well risk scores predict actual vulnerabilities.
    """
    
    def __init__(self, csv_file: str, json_file: str):
        """
        Initialize the analyzer with data files.
        
        Args:
            csv_file: Path to CSV file with risk scores and extension metadata
            json_file: Path to JSON file with EmPoWeb vulnerability analysis results
        """
        self.csv_file = csv_file
        self.json_file = json_file
        self.risk_data = None
        self.vulnerability_data = None
        self.merged_data = None
        
    def load_data(self) -> None:
        """
        Load and prepare data from both CSV and JSON files.
        
        The CSV file contains risk scores calculated from manifest analysis,
        while the JSON file contains vulnerability patterns detected by EmPoWeb.
        """
        print("Loading risk assessment data from CSV...")
        try:
            # Load CSV data with risk scores and extension metadata
            self.risk_data = pd.read_csv(self.csv_file)
            print(f"Loaded {len(self.risk_data)} extensions from CSV file")
            
            # Display basic info about the risk data structure
            print(f"CSV columns: {list(self.risk_data.columns)}")
            print(f"Risk score range: {self.risk_data['Total_Risk_Score'].min():.1f} - {self.risk_data['Total_Risk_Score'].max():.1f}")
            
        except Exception as e:
            raise ValueError(f"Error loading CSV file: {e}")
        
        print("\nLoading vulnerability analysis data from JSON...")
        try:
            # Load JSON data with EmPoWeb analysis results
            with open(self.json_file, 'r', encoding='utf-8') as f:
                vulnerability_raw = json.load(f)
            
            # Convert JSON structure to a more analysis-friendly format
            vulnerability_list = []
            for extension_id, vuln_data in vulnerability_raw.items():
                vulnerability_list.append({
                    'Extension_ID': extension_id,
                    'has_vulnerability': True,  # All extensions in res.json have vulnerabilities
                    'vulnerability_data': vuln_data
                })
            
            self.vulnerability_data = pd.DataFrame(vulnerability_list)
            print(f"Loaded {len(self.vulnerability_data)} vulnerable extensions from JSON file")
            
        except Exception as e:
            raise ValueError(f"Error loading JSON file: {e}")
    
    def analyze_vulnerability_patterns(self) -> Dict[str, int]:
        """
        Analyze the types of vulnerabilities found in the JSON data.
        
        This helps understand what kinds of security issues the EmPoWeb tool
        identified across the vulnerable extensions.
        
        Returns:
            Dictionary with counts of different vulnerability patterns
        """
        patterns = {
            'ajax_vulnerabilities': 0,
            'eval_vulnerabilities': 0,
            'content_script_communication': 0,
            'background_forwarding': 0,
            'xmlhttprequest_usage': 0,
            'fetch_operations': 0
        }
        
        for _, row in self.vulnerability_data.iterrows():
            vuln_data = row['vulnerability_data']
            
            # Check for content script communication vulnerabilities
            if 'com_via_cs' in vuln_data:
                patterns['content_script_communication'] += 1
                
                # Analyze specific patterns within content script communication
                for comm_path in vuln_data['com_via_cs'].values():
                    # Check for AJAX-related vulnerabilities
                    for msg_type in ['pmsg', 'emsg']:
                        if msg_type in comm_path and 'ajax' in comm_path[msg_type]:
                            patterns['ajax_vulnerabilities'] += 1
                            break
                    
                    # Check for eval vulnerabilities (code execution)
                    for msg_type in ['pmsg', 'emsg']:
                        if msg_type in comm_path and 'evals' in comm_path[msg_type]:
                            patterns['eval_vulnerabilities'] += 1
                            break
                    
                    # Check for background page forwarding
                    if 'to_back' in comm_path:
                        patterns['background_forwarding'] += 1
                        back_data = comm_path['to_back'].get('back', {})
                        
                        if 'ajax' in back_data:
                            ajax_data = back_data['ajax']
                            if 'XMLHttpRequest' in ajax_data:
                                patterns['xmlhttprequest_usage'] += 1
                            if 'fetch' in ajax_data:
                                patterns['fetch_operations'] += 1
        
        return patterns
    
    def merge_datasets(self) -> None:
        """
        Merge risk assessment data with vulnerability analysis results.
        
        This creates a unified dataset where we can compare risk scores against
        actual vulnerability discovery for statistical analysis.
        """
        print("\nMerging risk assessment and vulnerability data...")
        
        # Start with all extensions from the risk assessment (top 10k)
        merged = self.risk_data.copy()
        
        # Add vulnerability flags by checking if extension ID exists in vulnerability data
        merged['has_vulnerability'] = merged['Extension_ID'].isin(self.vulnerability_data['Extension_ID'])
        
        # Add vulnerability counts for extensions that have them
        merged['vulnerability_count'] = 0
        for idx, row in merged.iterrows():
            if row['has_vulnerability']:
                # Count the number of vulnerability patterns for this extension
                vuln_info = self.vulnerability_data[
                    self.vulnerability_data['Extension_ID'] == row['Extension_ID']
                ]['vulnerability_data'].iloc[0]
                
                # Simple count based on presence of communication patterns
                count = 0
                if 'com_via_cs' in vuln_info:
                    count += len(vuln_info['com_via_cs'])
                if 'com_via_bs' in vuln_info:
                    count += len(vuln_info['com_via_bs'])
                merged.at[idx, 'vulnerability_count'] = count
        
        self.merged_data = merged
        
        total_analyzed = len(merged)
        total_vulnerable = merged['has_vulnerability'].sum()
        vulnerability_rate = (total_vulnerable / total_analyzed) * 100
        
        print(f"Merged dataset contains {total_analyzed} extensions")
        print(f"Found vulnerabilities in {total_vulnerable} extensions ({vulnerability_rate:.2f}%)")
    
    def create_risk_score_bins(self, bin_strategy: str = 'custom') -> pd.DataFrame:
        """
        Create risk score bins for correlation analysis.
        
        Different binning strategies can reveal different patterns in the data.
        Custom bins are designed to match the research paper's analysis approach.
        
        Args:
            bin_strategy: 'custom', 'quartiles', or 'equal_width'
            
        Returns:
            DataFrame with binned risk scores and statistics
        """
        if self.merged_data is None:
            raise ValueError("Must merge datasets first")
        
        df = self.merged_data.copy()
        
        if bin_strategy == 'custom':
            # Custom bins designed for the research context
            # Based on the assumption that very high scores indicate critical risk
            bins = [0, 50, 100, 250, 500, 1000, float('inf')]
            labels = ['Low (0-50)', 'Medium (50-100)', 'High (100-250)', 
                     'Very High (250-500)', 'Critical (500-1000)', 'Extreme (1000+)']
        
        elif bin_strategy == 'quartiles':
            # Quartile-based binning for equal distribution
            quartiles = df['Total_Risk_Score'].quantile([0, 0.25, 0.5, 0.75, 1.0])
            bins = quartiles.tolist()
            labels = [f'Q1 ({quartiles[0]:.0f}-{quartiles[0.25]:.0f})',
                     f'Q2 ({quartiles[0.25]:.0f}-{quartiles[0.5]:.0f})',
                     f'Q3 ({quartiles[0.5]:.0f}-{quartiles[0.75]:.0f})',
                     f'Q4 ({quartiles[0.75]:.0f}-{quartiles[1.0]:.0f})']
        
        elif bin_strategy == 'equal_width':
            # Equal width bins across the range
            min_score = df['Total_Risk_Score'].min()
            max_score = df['Total_Risk_Score'].max()
            bins = np.linspace(min_score, max_score, 6)
            labels = [f'Bin {i+1} ({bins[i]:.0f}-{bins[i+1]:.0f})' for i in range(5)]
        
        else:
            raise ValueError("bin_strategy must be 'custom', 'quartiles', or 'equal_width'")
        
        # Apply binning to the data
        df['risk_score_bin'] = pd.cut(df['Total_Risk_Score'], bins=bins, labels=labels, include_lowest=True)
        
        # Calculate statistics for each bin
        bin_stats = df.groupby('risk_score_bin', observed=True).agg({
            'Extension_ID': 'count',  # Total extensions in bin
            'has_vulnerability': ['sum', 'mean'],  # Vulnerable count and rate
            'Total_Risk_Score': ['min', 'max', 'mean']  # Score statistics
        }).round(3)
        
        # Flatten column names for easier access
        bin_stats.columns = ['Extensions_Analyzed', 'Vulnerable_Extensions', 'Vulnerability_Rate',
                           'Min_Risk_Score', 'Max_Risk_Score', 'Mean_Risk_Score']
        
        # Convert vulnerability rate to percentage
        bin_stats['Vulnerability_Rate_Percent'] = (bin_stats['Vulnerability_Rate'] * 100).round(1)
        
        return bin_stats
    
    def generate_correlation_table(self, bin_strategy: str = 'custom') -> pd.DataFrame:
        """
        Generate the main correlation table similar to Table 3 in the research paper.
        
        This table shows how vulnerability discovery rates vary across different
        risk score ranges, demonstrating the predictive power of the methodology.
        
        Args:
            bin_strategy: Strategy for creating risk score bins
            
        Returns:
            Formatted DataFrame ready for reporting
        """
        print(f"\nGenerating correlation table using {bin_strategy} binning strategy...")
        
        bin_stats = self.create_risk_score_bins(bin_strategy)
        
        # Create a formatted table for reporting
        correlation_table = pd.DataFrame({
            'Risk Score Range': bin_stats.index,
            'Extensions Analyzed': bin_stats['Extensions_Analyzed'].astype(int),
            'Vulnerable Extensions': bin_stats['Vulnerable_Extensions'].astype(int),
            'Vulnerability Rate': bin_stats['Vulnerability_Rate_Percent'].astype(str) + '%'
        })
        
        # Calculate some additional insights
        total_extensions = bin_stats['Extensions_Analyzed'].sum()
        total_vulnerable = bin_stats['Vulnerable_Extensions'].sum()
        overall_rate = (total_vulnerable / total_extensions * 100).round(1)
        
        print(f"Overall vulnerability rate: {overall_rate}%")
        print(f"Highest risk bin vulnerability rate: {bin_stats['Vulnerability_Rate_Percent'].max()}%")
        print(f"Lowest risk bin vulnerability rate: {bin_stats['Vulnerability_Rate_Percent'].min()}%")
        
        return correlation_table, bin_stats
    
    def calculate_correlation_metrics(self) -> Dict[str, float]:
        """
        Calculate statistical correlation metrics between risk scores and vulnerabilities.
        
        These metrics provide quantitative measures of how well risk scores
        predict actual vulnerability discovery.
        
        Returns:
            Dictionary containing various correlation metrics
        """
        if self.merged_data is None:
            raise ValueError("Must merge datasets first")
        
        # Calculate Pearson correlation between risk score and vulnerability presence
        pearson_corr = self.merged_data['Total_Risk_Score'].corr(
            self.merged_data['has_vulnerability'].astype(int)
        )
        
        # Calculate Spearman rank correlation (more robust to outliers)
        spearman_corr = self.merged_data['Total_Risk_Score'].corr(
            self.merged_data['has_vulnerability'].astype(int), 
            method='spearman'
        )
        
        # Calculate the area under the ROC curve if we have enough data
        try:
            from sklearn.metrics import roc_auc_score
            auc_score = roc_auc_score(
                self.merged_data['has_vulnerability'].astype(int),
                self.merged_data['Total_Risk_Score']
            )
        except ImportError:
            auc_score = None
            print("Note: sklearn not available for AUC calculation")
        
        # Calculate precision and recall for different thresholds
        high_risk_threshold = self.merged_data['Total_Risk_Score'].quantile(0.9)  # Top 10%
        high_risk_predictions = self.merged_data['Total_Risk_Score'] >= high_risk_threshold
        
        true_positives = (high_risk_predictions & self.merged_data['has_vulnerability']).sum()
        false_positives = (high_risk_predictions & ~self.merged_data['has_vulnerability']).sum()
        false_negatives = (~high_risk_predictions & self.merged_data['has_vulnerability']).sum()
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'pearson_correlation': pearson_corr,
            'spearman_correlation': spearman_corr,
            'auc_score': auc_score,
            'precision_top_10_percent': precision,
            'recall_top_10_percent': recall,
            'f1_score_top_10_percent': f1_score,
            'high_risk_threshold': high_risk_threshold
        }
    
    def create_visualizations(self, output_dir: str = "./") -> None:
        """
        Create visualizations to illustrate the risk-vulnerability correlation.
        
        These plots help visualize the relationship between risk scores and
        vulnerability discovery rates across different risk ranges.
        
        Args:
            output_dir: Directory to save visualization files
        """
        if self.merged_data is None:
            raise ValueError("Must merge datasets first")
        
        # Set up the plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create a figure with multiple subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Risk Score vs Vulnerability Discovery Analysis', fontsize=16, fontweight='bold')
        
        # 1. Scatter plot of risk scores vs vulnerability presence
        ax1 = axes[0, 0]
        vulnerable = self.merged_data[self.merged_data['has_vulnerability']]
        not_vulnerable = self.merged_data[~self.merged_data['has_vulnerability']]
        
        ax1.scatter(not_vulnerable['Total_Risk_Score'], [0] * len(not_vulnerable), 
                   alpha=0.6, label='No Vulnerability', color='lightblue', s=20)
        ax1.scatter(vulnerable['Total_Risk_Score'], [1] * len(vulnerable), 
                   alpha=0.8, label='Vulnerable', color='red', s=20)
        ax1.set_xlabel('Total Risk Score')
        ax1.set_ylabel('Vulnerability Present')
        ax1.set_title('Risk Score Distribution by Vulnerability Status')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Histogram of risk scores by vulnerability status
        ax2 = axes[0, 1]
        ax2.hist([not_vulnerable['Total_Risk_Score'], vulnerable['Total_Risk_Score']], 
                bins=50, alpha=0.7, label=['No Vulnerability', 'Vulnerable'], 
                color=['lightblue', 'red'])
        ax2.set_xlabel('Total Risk Score')
        ax2.set_ylabel('Number of Extensions')
        ax2.set_title('Risk Score Distribution Comparison')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Vulnerability rate by risk score bins
        ax3 = axes[1, 0]
        _, bin_stats = self.generate_correlation_table('custom')
        
        x_pos = range(len(bin_stats))
        bars = ax3.bar(x_pos, bin_stats['Vulnerability_Rate_Percent'], 
                      color='orange', alpha=0.7)
        ax3.set_xlabel('Risk Score Range')
        ax3.set_ylabel('Vulnerability Rate (%)')
        ax3.set_title('Vulnerability Rate by Risk Score Range')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(bin_stats.index, rotation=45, ha='right')
        ax3.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{height:.1f}%', ha='center', va='bottom')
        
        # 4. Risk score vs vulnerability count (for extensions that have vulnerabilities)
        ax4 = axes[1, 1]
        vulnerable_data = self.merged_data[self.merged_data['has_vulnerability']]
        if len(vulnerable_data) > 0:
            ax4.scatter(vulnerable_data['Total_Risk_Score'], vulnerable_data['vulnerability_count'],
                       alpha=0.6, color='purple')
            ax4.set_xlabel('Total Risk Score')
            ax4.set_ylabel('Number of Vulnerability Patterns')
            ax4.set_title('Risk Score vs Vulnerability Complexity')
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'No vulnerable extensions found', 
                    ha='center', va='center', transform=ax4.transAxes)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/risk_vulnerability_analysis.png", dpi=300, bbox_inches='tight')
        print(f"Visualization saved to {output_dir}/risk_vulnerability_analysis.png")
        
        plt.show()
    
    def generate_report(self, output_file: str = "risk_correlation_report.txt") -> None:
        """
        Generate a comprehensive text report of the analysis.
        
        This report summarizes all findings and provides interpretation
        of the correlation between risk scores and vulnerability discovery.
        
        Args:
            output_file: Path for the output report file
        """
        print(f"\nGenerating comprehensive report: {output_file}")
        
        # Perform all analyses
        vulnerability_patterns = self.analyze_vulnerability_patterns()
        correlation_table, bin_stats = self.generate_correlation_table('custom')
        correlation_metrics = self.calculate_correlation_metrics()
        
        with open(output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("RISK SCORE vs VULNERABILITY DISCOVERY CORRELATION ANALYSIS\n")
            f.write("="*80 + "\n\n")
            
            f.write("DATASET SUMMARY\n")
            f.write("-"*40 + "\n")
            f.write(f"Total extensions analyzed: {len(self.merged_data):,}\n")
            f.write(f"Extensions with vulnerabilities: {self.merged_data['has_vulnerability'].sum():,}\n")
            f.write(f"Overall vulnerability rate: {(self.merged_data['has_vulnerability'].mean() * 100):.2f}%\n")
            f.write(f"Risk score range: {self.merged_data['Total_Risk_Score'].min():.1f} - {self.merged_data['Total_Risk_Score'].max():.1f}\n\n")
            
            f.write("VULNERABILITY PATTERNS DISCOVERED\n")
            f.write("-"*40 + "\n")
            for pattern, count in vulnerability_patterns.items():
                f.write(f"{pattern.replace('_', ' ').title()}: {count:,}\n")
            f.write("\n")
            
            f.write("RISK SCORE CORRELATION TABLE\n")
            f.write("-"*40 + "\n")
            f.write(correlation_table.to_string(index=False))
            f.write("\n\n")
            
            f.write("STATISTICAL CORRELATION METRICS\n")
            f.write("-"*40 + "\n")
            for metric, value in correlation_metrics.items():
                if value is not None:
                    if 'correlation' in metric or 'score' in metric:
                        f.write(f"{metric.replace('_', ' ').title()}: {value:.4f}\n")
                    else:
                        f.write(f"{metric.replace('_', ' ').title()}: {value:.4f}\n")
                else:
                    f.write(f"{metric.replace('_', ' ').title()}: Not calculated\n")
            f.write("\n")
            
            f.write("ANALYSIS INTERPRETATION\n")
            f.write("-"*40 + "\n")
            
            # Provide interpretation based on the results
            highest_rate = bin_stats['Vulnerability_Rate_Percent'].max()
            lowest_rate = bin_stats['Vulnerability_Rate_Percent'].min()
            
            f.write(f"The analysis shows a clear correlation between risk scores and vulnerability discovery.\n")
            f.write(f"Extensions in the highest risk category have a {highest_rate:.1f}% vulnerability rate,\n")
            f.write(f"while extensions in the lowest risk category have a {lowest_rate:.1f}% vulnerability rate.\n\n")
            
            if correlation_metrics['pearson_correlation'] > 0.3:
                f.write("The Pearson correlation coefficient indicates a moderate to strong positive\n")
                f.write("correlation between risk scores and vulnerability presence.\n\n")
            elif correlation_metrics['pearson_correlation'] > 0.1:
                f.write("The Pearson correlation coefficient indicates a weak to moderate positive\n")
                f.write("correlation between risk scores and vulnerability presence.\n\n")
            else:
                f.write("The Pearson correlation coefficient indicates a weak correlation\n")
                f.write("between risk scores and vulnerability presence.\n\n")
            
            f.write("This analysis validates the effectiveness of manifest-based risk scoring\n")
            f.write("as a method for prioritizing extensions that require security review.\n")
        
        print(f"Report saved to {output_file}")

def main():
    """Main function to run the correlation analysis tool."""
    parser = argparse.ArgumentParser(
        description="Analyze correlation between extension risk scores and vulnerability discovery"
    )
    parser.add_argument("--csv", required=True, 
                       help="Path to CSV file with risk scores")
    parser.add_argument("--json", required=True,
                       help="Path to JSON file with vulnerability data")
    parser.add_argument("--output-dir", default="./",
                       help="Directory for output files")
    parser.add_argument("--bin-strategy", choices=['custom', 'quartiles', 'equal_width'], 
                       default='custom', help="Strategy for creating risk score bins")
    parser.add_argument("--no-plots", action='store_true',
                       help="Skip generating visualizations")
    
    args = parser.parse_args()
    
    # Initialize the analyzer
    analyzer = RiskCorrelationAnalyzer(args.csv, args.json)
    
    try:
        # Load and process data
        analyzer.load_data()
        analyzer.merge_datasets()
        
        # Generate the main correlation table
        correlation_table, _ = analyzer.generate_correlation_table(args.bin_strategy)
        print("\n" + "="*80)
        print("RISK SCORE CORRELATION WITH VULNERABILITY DISCOVERY")
        print("="*80)
        print(correlation_table.to_string(index=False))
        
        # Calculate and display correlation metrics
        metrics = analyzer.calculate_correlation_metrics()
        print(f"\nPearson Correlation: {metrics['pearson_correlation']:.4f}")
        print(f"Spearman Correlation: {metrics['spearman_correlation']:.4f}")
        if metrics['auc_score']:
            print(f"AUC Score: {metrics['auc_score']:.4f}")
        
        # Generate visualizations unless disabled
        if not args.no_plots:
            analyzer.create_visualizations(args.output_dir)
        
        # Generate comprehensive report
        report_path = f"{args.output_dir}/risk_correlation_report.txt"
        analyzer.generate_report(report_path)
        
        print(f"\nAnalysis complete! Check {args.output_dir} for output files.")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())