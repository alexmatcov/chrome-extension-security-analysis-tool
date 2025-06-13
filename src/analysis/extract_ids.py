#!/usr/bin/env python3
"""
Script to extract Extension IDs from top_10k_risky_extensions.csv
and save them to extension_ids.txt
"""

import pandas as pd
import sys
import os

def extract_extension_ids():
    # Input and output file names
    input_file = "top_10k_risky_extensions.csv"
    output_file = "extension_ids.txt"
    
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Error: File '{input_file}' not found in current directory.")
            return False
        
        # Read the CSV file
        print(f"Reading {input_file}...")
        df = pd.read_csv(input_file)
        
        # Check if Extension_ID column exists
        if 'Extension_ID' not in df.columns:
            print("Error: 'Extension_ID' column not found in the CSV file.")
            print(f"Available columns: {list(df.columns)}")
            return False
        
        # Extract Extension IDs
        extension_ids = df['Extension_ID'].dropna().astype(str)
        
        # Remove any duplicates while preserving order
        extension_ids = extension_ids.drop_duplicates()
        
        print(f"Found {len(extension_ids)} unique Extension IDs")
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            for ext_id in extension_ids:
                f.write(f"{ext_id}\n")
        
        print(f"Extension IDs successfully saved to '{output_file}'")
        print(f"First 5 IDs: {list(extension_ids.head())}")
        
        return True
        
    except pd.errors.EmptyDataError:
        print("Error: The CSV file is empty.")
        return False
    except pd.errors.ParserError as e:
        print(f"Error parsing CSV file: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    success = extract_extension_ids()
    sys.exit(0 if success else 1)