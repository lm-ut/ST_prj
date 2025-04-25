#!/usr/bin/env python
# coding: utf-8

import subprocess
import os
import argparse

# -----------------------------
# Argument Parsing
# -----------------------------
parser = argparse.ArgumentParser(description="Run WINC-based analysis for two populations.")
parser.add_argument("--file_path", help="Path to file with list of target samples", type=str, required
=True)
parser.add_argument("--popA", help="Label Pop A", type=str, required=True)
parser.add_argument("--popB", help="Label Pop B", type=str, required=True)
parser.add_argument("--bfile_base", help="Base name for PLINK files (without extension)", type=str, re
quired=True)
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
# Chunk Creation
# -----------------------------
chunk_size = 10
steps = 5

with open(filepath, 'r') as f:
    lines = f.readlines()
    chunks = []
    for i in range(1, steps + 1):
        end_index = i * chunk_size
        chunk = lines[:end_index]
        chunks.append(chunk)

for i, chunk in enumerate(chunks, 1):
    with open(f'chunk_{i}', 'w') as f:
        f.writelines(chunk)

# -----------------------------
# EGREP: Filter fam by popA or popB
# -----------------------------
pattern = f"{popA}|{popB}"
egrep_command = f"""
for i in {{1..10}}; do 
    egrep '{pattern}' {bfile_base}.fam >> chunk_${{i}}_{popA_safe}_{popB_safe}
done
"""
subprocess.run(["bash", "-c", egrep_command], check=True)

# -----------------------------
# PLINK: Create new binary files
# -----------------------------
plink_command = f"""
for i in {{1..10}}; do
    ~/tools/plink --bfile {bfile_base} \\
    --keep chunk_${{i}}_{popA_safe}_{popB_safe} --make-bed --out chunk_${{i}}_{popA_safe}_{popB_safe}_
SA
done
"""
process = subprocess.Popen(["bash", "-c", plink_command], stdout=subprocess.PIPE, stderr=subprocess.ST
DOUT, text=True)
for line in process.stdout:
    print(line, end='')
process.wait()

# -----------------------------
# AWK: Annotate .fam with population labels
# -----------------------------
awk_command = f"""
for i in {{1..10}}; do 
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
process = subprocess.Popen(["bash", "-c", awk_command], stdout=subprocess.PIPE, stderr=subprocess.STDO
UT, text=True)
process.wait()

# -----------------------------
# ADMIXTURE Job Preparation
# -----------------------------

job_parser = f"""
for i in {{1..10}}; do
  sed -r "s/ST_SupADM.bed/chunk_${{i}}_{popA_safe}_{popB_safe}_SA.bed/g" admixture.sh > admixture_c${{
i}}_{popA_safe}_{popB_safe}.sh
done
"""

process = subprocess.Popen(["bash", "-c", job_parser], stdout=subprocess.PIPE, stderr=subprocess.STDOU
T, text=True)
for line in process.stdout:
    print(line, end='')
process.wait()
