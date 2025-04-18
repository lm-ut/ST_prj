import msprime
import daiquiri
import argparse
import os

parser = argparse.ArgumentParser(description="Perform msprime simulations.")

## ANCESTRAL POP
parser.add_argument("--pop_size_ANC", help="Pop Size ANC", type=int, default=10000)
parser.add_argument("--anc_split", help="Time of split from ANC into A and B", type=int, default=1000)


#######
## A ##
#######

parser.add_argument("--pop_size_A", help="Pop Size A", type=int, default=10000)
parser.add_argument("--post_btln_size_A", help="Post-bottleneck size A", type=int, default=1000)
parser.add_argument("--btln_time_A", help="Bottleneck time A", type=int, default=65)
parser.add_argument("--ind_sampled_A", help="Individuals sampled A", type=int, default=50)

#######
## B ##
#######

parser.add_argument("--pop_size_B", help="Pop Size B", type=int, default=10000)
parser.add_argument("--post_btln_size_B", help="Post-bottleneck size B", type=int, default=1000)
parser.add_argument("--btln_time_B", help="Bottleneck time B", type=int, default=65)
parser.add_argument("--ind_sampled_B", help="Individuals sampled B", type=int, default=50)

#######
## C ##
#######

parser.add_argument("--pop_size_C", help="Pop Size C", type=int, default=10000)
parser.add_argument("--prop_A", help="Proportion from A", type=float, default=0.7)
parser.add_argument("--prop_B", help="Proportion from B", type=float, default=0.3)
parser.add_argument("--admg_C", help="Admixture time C", type=int, default=25)
parser.add_argument("--post_btln_size_C", help="Post-bottleneck size C", type=int, default=3500)
parser.add_argument("--btln_time_C", help="Bottleneck time C", type=int, default=20)
parser.add_argument("--ind_sampled_C", help="Individuals sampled C", type=int, default=350)

###############
# Output name #
###############
parser.add_argument("--output", help="Output VCF filename", default="default_output.vcf")



args = parser.parse_args()

# Unpack args for clarity
population_size_ANC = args.pop_size_ANC
split_time_ANC = args.anc_split

# Population A
population_size_A = args.pop_size_A
post_bottleneck_size_A = args.post_btln_size_A
bottleneck_time_A = args.btln_time_A
num_individuals_to_sample_A = args.ind_sampled_A

# Population B
population_size_B = args.pop_size_B
post_bottleneck_size_B = args.post_btln_size_B
bottleneck_time_B = args.btln_time_B
num_individuals_to_sample_B = args.ind_sampled_B

# Population C
population_size_C = args.pop_size_C
admixture_proportion_A = args.prop_A
admixture_proportion_B = args.prop_B
admixture_time_C = args.admg_C
post_bottleneck_size_C = args.post_btln_size_C
bottleneck_time_C = args.btln_time_C
num_individuals_to_sample_C = args.ind_sampled_C

# Output file name
output_filename = args.output

# Set up the demography
demography = msprime.Demography()
demography.add_population(name="A", initial_size=population_size_A)
demography.add_population(name="B", initial_size=population_size_B)
demography.add_population(name="C", initial_size=population_size_C)
demography.add_population(name="ANC", initial_size=population_size_ANC, initially_active=False)

print("BEGIN")

# Split ANC into A and B
demography.add_population_split(time=split_time_ANC, ancestral="ANC", derived=["A", "B"])

# Bottlenecks in A and B
demography.add_population_parameters_change(
    time=bottleneck_time_A, population="A", initial_size=post_bottleneck_size_A
)
print("ADD BOTTLENECK on A")

demography.add_population_parameters_change(
    time=bottleneck_time_B, population="B", initial_size=post_bottleneck_size_B
)
print("ADD BOTTLENECK on B")

# Admixture event to create C
demography.add_admixture(
    time=admixture_time_C,
    derived="C",
    ancestral=["A", "B"],
    proportions=[admixture_proportion_A, admixture_proportion_B]
)
print("ADD ADMX")

# Bottleneck in C
demography.add_population_parameters_change(
    time=bottleneck_time_C, population="C", initial_size=post_bottleneck_size_C
)
print("ADD BOTTLENECK on C")

# Finalize and print
demography.sort_events()
print(demography)
print(demography.debug())

# Set up logging
daiquiri.setup(level="INFO")

# Simulate ancestry
simulation = msprime.sim_ancestry(
    samples={
        "A": num_individuals_to_sample_A,
        "B": num_individuals_to_sample_B,
        "C": num_individuals_to_sample_C
    },
    demography=demography,
    sequence_length=2.5e8,
    recombination_rate=1.25e-8
)

# Add mutations
mutated_ts = msprime.sim_mutations(simulation, rate=1e-8)
print("Done Mut")

# Write VCF output
with open(output_filename, "w") as vcf_file:
    mutated_ts.write_vcf(vcf_file)

print("VCF ready")
