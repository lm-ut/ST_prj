### Script to test supervised admixture result on incremental sample size

import subprocess

filepath = 'ST_LIST'                           
chunk_size=34
steps=10

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


# EGREP command (append filtered lines to chunk_i)
egrep_command = """
for i in {1..10}; do 
    egrep 'France|NL-AncEMA' STref_YRI_geno01_UKRom_Ork_Ita_AARD_nlGone.fam >> chunk_$i
done
"""
subprocess.run(["bash", "-c", egrep_command], check=True)

# PLINK command
plink_command = """
for i in {1..10}; do
    ~/tools/plink --bfile STref_YRI_geno01_UKRom_Ork_Ita_AARD_nlGone \\
    --keep chunk_$i --make-bed --out chunk_${i}_SA
done
"""
# Stream output live
process = subprocess.Popen(["bash", "-c", plink_command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
for line in process.stdout:
    print(line, end='')
process.wait()


awk_command = """
for i in {1..10}; do
  awk '{
    if ($1 == "France-AncLIA")
      category = "France-AncLIA";
    else if ($1 == "NL-AncEMA")
      category = "NL-AncEMA";
    else if ($2 == "UN19" || $2 == "UN85" || $2 == "UN129")
      category = "-";
    else
      category = "-";
    print category, $2, $3, $4, $5, $6, category;
  }' chunk_${i}_SA.fam > chunk_${i}_SA.pop
done
"""

process = subprocess.Popen(["bash", "-c", awk_command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
for line in process.stdout:
    print(line, end='')  
process.wait()

job_parser = """
for i in {1..10}; do
  sed -r "s/ST_SupADM.bed/chunk_${i}_SA.bed/g" admixture.sh > admixture_c${i}.sh
done
"""
process = subprocess.Popen(["bash", "-c", job_parser], stdout=subprocess.PIPE, stderr=subprocess.STDOU
T, text=True)
for line in process.stdout:
    print(line, end='')
process.wait()



