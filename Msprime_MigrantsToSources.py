import msprime
import daiquiri
import argparse
import os

parser = argparse.ArgumentParser(description="Perform msprime simulations, with same-pop migrants to the sources of the admixture")

# === Ancestral split ===
parser.add_argument("--pop_size_ANC", type=int, default=10000)
parser.add_argument("--anc_split", type=int, default=80)

# === Intermediate pops ===
parser.add_argument("--pop_size_X", type=int, default=10000)
parser.add_argument("--split_X", type=int, default=70)
parser.add_argument("--btln_time_X", type=int, default=75)
parser.add_argument("--post_btln_size_X", type=int, default=1000)

parser.add_argument("--pop_size_Y", type=int, default=10000)
parser.add_argument("--pop_size_K", type=int, default=10000)
parser.add_argument("--pop_size_J", type=int, default=10000)

# === Population A ===
parser.add_argument("--pop_size_A", type=int, default=10000)
parser.add_argument("--post_btln_size_A", type=int, default=1000)
parser.add_argument("--btln_time_A", type=int, default=50)
parser.add_argument("--ind_sampled_A", type=int, default=50)
parser.add_argument("--prop_X_A", type=float, default=0.1)
parser.add_argument("--prop_K_A", type=float, default=0.9)
parser.add_argument("--admg_A", type=int, default=60)

# === Population B ===
parser.add_argument("--pop_size_B", type=int, default=10000)
parser.add_argument("--post_btln_size_B", type=int, default=1000)
parser.add_argument("--btln_time_B", type=int, default=50)
parser.add_argument("--ind_sampled_B", type=int, default=50)
parser.add_argument("--prop_X_B", type=float, default=0.1)
parser.add_argument("--prop_J_B", type=float, default=0.9)
parser.add_argument("--admg_B", type=int, default=60)

# === Population C ===
parser.add_argument("--pop_size_C", type=int, default=10000)
parser.add_argument("--prop_A", type=float, default=0.7)
parser.add_argument("--prop_B", type=float, default=0.3)
parser.add_argument("--admg_C", type=int, default=25)
parser.add_argument("--post_btln_size_C", type=int, default=3500)
parser.add_argument("--btln_time_C", type=int, default=20)
parser.add_argument("--ind_sampled_C", type=int, default=350)

# Output
parser.add_argument("--output", default="default_output.vcf")

args = parser.parse_args()

demography = msprime.Demography()

# Base populations
demography.add_population(name="ANC", initial_size=args.pop_size_ANC, initially_active = False)
demography.add_population(name="X", initial_size=args.pop_size_X)
demography.add_population(name="Y", initial_size=args.pop_size_Y)
demography.add_population(name="K", initial_size=args.pop_size_K)
demography.add_population(name="J", initial_size=args.pop_size_J)
demography.add_population(name="A", initial_size=args.pop_size_A)
demography.add_population(name="B", initial_size=args.pop_size_B)
demography.add_population(name="C", initial_size=args.pop_size_C)

# Splits
demography.add_population_split(time=args.anc_split, derived=["X", "Y"], ancestral="ANC")
demography.add_population_split(time=args.split_X, derived=["K", "J"], ancestral="Y")

# Bottlenecks
demography.add_population_parameters_change(time=args.btln_time_A, population="A", initial_size=args.post_btln_size_A)
demography.add_population_parameters_change(time=args.btln_time_B, population="B", initial_size=args.post_btln_size_B)
demography.add_population_parameters_change(time=args.btln_time_C, population="C", initial_size=args.post_btln_size_C)
demography.add_population_parameters_change(time=args.btln_time_X, population="X", initial_size=args.post_btln_size_X)

# Admixture
demography.add_admixture(
    time=args.admg_A, derived="A", ancestral=["X", "K"], proportions=[args.prop_X_A, args.prop_K_A]
)
demography.add_admixture(
    time=args.admg_B, derived="B", ancestral=["X", "J"], proportions=[args.prop_X_B, args.prop_J_B]
)
demography.add_admixture(
    time=args.admg_C, derived="C", ancestral=["A", "B"], proportions=[args.prop_A, args.prop_B]
)

# Finalize
demography.sort_events()
print(demography)
print(demography.debug())

# Log
daiquiri.setup(level="INFO")

# Simulate
ts = msprime.sim_ancestry(
    samples={
        "A": args.ind_sampled_A,
        "B": args.ind_sampled_B,
        "C": args.ind_sampled_C
    },
    demography=demography,
    sequence_length=2.5e8,
    recombination_rate=1.25e-8,
)

mutated_ts = msprime.sim_mutations(ts, rate=1e-8)

# Output VCF
with open(args.output, "w") as vcf_file:
    mutated_ts.write_vcf(vcf_file)

print("Simulation complete. VCF written to:", args.output)
