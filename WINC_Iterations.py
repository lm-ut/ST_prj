#!/usr/bin/env python
# coding: utf-8

import subprocess
import os
import argparse

# -----------------------------
# Argument Parsing
# -----------------------------
parser = argparse.ArgumentParser(description="Run WINC-based analysis for two populations.")
parser.add_argument("--file_path", help="Path to file with list of target samples", type=str, required=True)
parser.add_argument("--popA", help="Label Pop A", type=str, required=True)
parser.add_argument("--popB", help="Label Pop B", type=str, required=True)
parser.add_argument("--bfile_base", help="Base name for PLINK files (without extension)", type=str, required=True)
args = parser.parse_args()

# -----------------------------
# Variables
# -----------------------------
filepath = args.file_path
popA = args.popA
popB = args.popB
bfile_base = args.bfile_base

# Sanitize pop names for filenames
popA_safe = popA.replace(" ", "_")
popB_safe = popB.replace(" ", "_")

# -----------------------------
# Chunk Creation (increasing sizes)
# -----------------------------
steps = 5  # Number of chunks we want to create
chunk_sizes = [10, 20, 30, 40, 50]  # Chunk sizes (10, 20, 30, ..., 50)

with open(filepath, 'r') as f:
    lines = f.readlines()

    # Create the chunks based on the sizes
    chunks = []
    for size in chunk_sizes:
        chunk = lines[:size]  # Take the first 'size' lines from the file
        chunks.append(chunk)

# Write each chunk to a separate file
for i, chunk in enumerate(chunks, 1):
    with open(f'chunk_{i}_{popA_safe}_{popB_safe}', 'w') as f:
        f.writelines(chunk)

# -----------------------------
# EGREP: Filter fam by popA or popB
# -----------------------------
pattern = f"{popA}|{popB}"
egrep_command = f"""
for i in {{1..{steps}}}; do
    egrep -w '{pattern}' {bfile_base}.fam >> chunk_${{i}}_{popA_safe}_{popB_safe}
done
"""
subprocess.run(["bash", "-c", egrep_command], check=True)

# -----------------------------
# PLINK: Create new binary files
# -----------------------------
plink_command = f"""
for i in {{1..{steps}}}; do
    ~/tools/plink --bfile {bfile_base} \\
    --keep chunk_${{i}}_{popA_safe}_{popB_safe} --make-bed --out chunk_${{i}}_{popA_safe}_{popB_safe}_SA
done
"""
process = subprocess.Popen(["bash", "-c", plink_command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
for line in process.stdout:
    print(line, end='')
process.wait()

# -----------------------------
# AWK: Annotate .fam with population labels
# -----------------------------
awk_command = f"""
for i in {{1..{steps}}}; do 
  awk -v popA="{popA}" -v popB="{popB}" '{{ 
    if ($1 == popA)
      category = "popA"; 
    else if ($1 == popB) 
      category = "popB"; 
    else 
      category = "-"; 
    print category, $2, $3, $4, $5, $6, category; 
  }}' chunk_${{i}}_{popA_safe}_{popB_safe}_SA.fam > chunk_${{i}}_{popA_safe}_{popB_safe}_SA.pop
done
"""
process = subprocess.Popen(["bash", "-c", awk_command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
process.wait()

# -----------------------------
# ADMIXTURE Job Preparation
# -----------------------------
job_parser = f"""
for i in {{1..{steps}}}; do
  sed -r "s/ST_SupADM.bed/chunk_${{i}}_{popA_safe}_{popB_safe}_SA.bed/g" admixture.sh > admixture_c${{i}}_{popA_safe}_{popB_safe}.sh
done
"""

process = subprocess.Popen(["bash", "-c", job_parser], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
for line in process.stdout:
    print(line, end='')
process.wait()
