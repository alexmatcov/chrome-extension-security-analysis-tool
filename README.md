# Chrome Extension Security Analysis Tool

A comprehensive research toolkit for analyzing Chrome extension security risks at scale, implementing the methodology from "Large-Scale Security Risk Evaluation of Chrome Browser Extensions" research paper.

## Overview

This research toolkit implements the methodology from "Large-Scale Security Risk Evaluation of Chrome Browser Extensions" to analyze Chrome extension security risks at scale. The system provides comprehensive tools for:

- Analyzing manifest-based risk scores using Google's permission risk framework
- Correlating risk scores with actual vulnerability discovery
- Processing large-scale extension datasets (10,000+ extensions)
- Identifying potentially malicious extensions based on permission patterns

## Key Features

### Risk Scoring Engine

The risk scoring engine implements the research paper's exact methodology:

```
Risk Score = Σ(permission_scores) + User Factor + Rating Factor
```

Based on the Google Chrome Enterprise Permission Risk Whitepaper (July 2019), the engine:
- Analyzes permissions, host access patterns, and metadata factors
- Categorizes extensions into risk levels:
 - **Critical** (≥18)
 - **High** (12-17)
 - **Medium** (6-11)
 - **Low** (1-5)
 - **No Risk** (<1)

### Vulnerability Correlation Analysis

- Correlates manifest-based risk scores with actual vulnerabilities
- Validates the predictive power of permission-based risk assessment
- Generates statistical metrics (Pearson/Spearman correlation, AUC scores)
- Creates visualizations showing risk-vulnerability relationships

### High-Speed Extension Crawler

- Direct API crawler optimized for maximum speed
- 12× concurrent downloads with minimal delays
- Supports multiple download strategies and fallback mechanisms
- Processes thousands of extensions efficiently

### Suspicious Extension Checker

- Compares extension datasets against known malicious extensions from EmPoWeb research
- Identifies extensions with suspicious permission patterns
- Provides detailed risk breakdowns and threat summaries

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd chrome-extension-security-analysis

# Install Python dependencies
pip install pandas numpy matplotlib seaborn

# For the crawler (optional)
cd src/crawler
npm install
```

## Usage

### Analyze Extension Risk Scores

```python
from src.analysis.manifest_analyzer import analyze_extensions_directory

# Analyze all extensions in a directory
all_results, top_10k = analyze_extensions_directory(
   "../extensions/manifests-2025-01-10",
   all_output_file="all_extensions_ranked.json",
   top_k_output_file="top_10k_risky_extensions.json",
   top_k=10000
)
```

### Check for Suspicious Extensions

```bash
python src/analysis/extension_checker.py
# Enter path to your all_extensions_ranked.json when prompted
```

### Analyze Risk-Vulnerability Correlation

```bash
python src/analysis/risk_analyzer.py \
   --csv top_10k_risky_extensions.csv \
   --json vulnerability_data.json
```

### Extract Extension IDs from CSV

```bash
python src/analysis/extract_ids.py
# Extracts Extension_ID column from top_10k_risky_extensions.csv
```

### Crawl Extension Files (Optional)

```bash
cd src/crawler
node crx-crawler.js
# Requires extension_ids.txt with one ID per line
```

## Risk Scoring Methodology

The tool implements a comprehensive risk scoring system based on three key factors:

### Permission Weights

| Risk Level | Score | Example Permissions |
|------------|-------|-------------------|
| Highest Risk | 10 | `<all_urls>`, broad host permissions |
| High Risk | 9 | `nativeMessaging`, `debugger`, `cookies`, `proxy` |
| Medium Risk | 6 | `bookmarks`, `geolocation`, `webRequest` |
| Low Risk | 2 | `storage`, `notifications` |

### User Factor

| User Count | Points Added |
|------------|-------------|
| ≥1M users | +2.0 |
| ≥100K users | +1.5 |
| ≥10K users | +1.0 |
| ≥1K users | +0.5 |

### Rating Factor

| Rating Criteria | Points Added |
|----------------|-------------|
| ≥4.5 stars + ≥1K reviews | -1.5 |
| ≥4.0 stars + ≥500 reviews | -1.0 |
| <2.5 stars or <10 reviews | +1.0 |

## Output Files

### Risk Analysis Results
- `all_extensions_ranked.json` - Complete analysis of all extensions
- `top_10k_risky_extensions.json` - Top 10,000 riskiest extensions
- `*.csv` versions for spreadsheet analysis

### Correlation Analysis
- `risk_correlation_report.txt` - Detailed statistical analysis
- `risk_vulnerability_analysis.png` - Visualization plots

### Suspicious Extension Report
- Console output with detailed breakdown of suspicious extensions found
- Risk distribution and threat summary

## Data Format

### Input Manifest Format

```yaml
---
extension_id: "..."
user_count: 1000000
rating: 4.5
rating_count: 5000
---
{
 "manifest_version": 2,
 "permissions": ["tabs", "storage"],
 "host_permissions": ["*://*.example.com/*"]
}
```

### Output Risk Analysis

```json
{
 "extension_id": "...",
 "total_risk_score": 25.5,
 "risk_level": "Critical",
 "risk_breakdown": {
   "permission_risk": 18,
   "host_risk": 10,
   "user_factor": -1.5,
   "rating_factor": -1.0
 }
}
```

## Research Context

This tool implements the methodology from the research paper on large-scale Chrome extension security evaluation. It helps:

- Identify potentially malicious extensions before manual review
- Prioritize security audits based on risk scores
- Validate the effectiveness of permission-based risk assessment
- Support enterprise deployment decisions
