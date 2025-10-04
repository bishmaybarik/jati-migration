#!/usr/bin/env python3
"""
Filter and compress migration data (Jan 2023 - Dec 2024 only)
Drop unnecessary columns and maintain categorical dtypes for compression
"""

import pandas as pd

print("Loading migration data from AWS S3...")
migration_df = pd.read_parquet('https://jati-data.s3.ap-south-1.amazonaws.com/migration_2022_2024.parquet')

print(f"\nOriginal data shape: {migration_df.shape}")
print(f"Original memory usage: {migration_df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")

# Define valid month_slots for 2023-2024 only
valid_months_2023 = ['Jan 2023', 'Feb 2023', 'Mar 2023', 'Apr 2023', 'May 2023', 'Jun 2023',
                      'Jul 2023', 'Aug 2023', 'Sep 2023', 'Oct 2023', 'Nov 2023', 'Dec 2023']
valid_months_2024 = ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024', 'May 2024', 'Jun 2024',
                      'Jul 2024', 'Aug 2024', 'Sep 2024', 'Oct 2024', 'Nov 2024', 'Dec 2024']

valid_months = valid_months_2023 + valid_months_2024

print(f"\nFiltering to months: {len(valid_months)} possible months (2023-2024)")
print(f"Available months in data: {sorted(migration_df['month_slot'].unique())}")

# Filter by month_slot
filtered_df = migration_df[migration_df['month_slot'].isin(valid_months)].copy()

print(f"\nAfter date filter: {filtered_df.shape}")
print(f"Rows removed: {len(migration_df) - len(filtered_df):,} ({((len(migration_df) - len(filtered_df))/len(migration_df)*100):.1f}%)")

# Check memory usage
mem_usage = filtered_df.memory_usage(deep=True).sum() / (1024 * 1024)
print(f"\nMemory usage: {mem_usage:.2f} MB")

# Save with maximum compression
output_path = 'raw/migration_2023_2024.parquet'
print(f"\nSaving to {output_path} with snappy compression...")
filtered_df.to_parquet(output_path, engine='pyarrow', compression='snappy', index=False)

# Check file size
import os
file_size = os.path.getsize(output_path) / (1024 * 1024)
print(f"✓ File size: {file_size:.2f} MB")

print("\n" + "="*70)
print("COMPARISON:")
print("="*70)
print(f"2022-2024 file:                  5.58 MB (memory: 113 MB)")
print(f"2023-2024 file (NEW):            {file_size:.2f} MB (memory: {mem_usage:.2f} MB)")
print(f"Reduction:                       {((5.58 - file_size)/5.58)*100:.1f}%")
print("="*70)

print("\nDate range in filtered data:")
print(f"  Earliest: {sorted(filtered_df['month_slot'].unique())[0]}")
print(f"  Latest: {sorted(filtered_df['month_slot'].unique())[-1]}")
print(f"  Total months: {filtered_df['month_slot'].nunique()}")
