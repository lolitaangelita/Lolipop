from pathlib import Path
import argparse

import itertools
import math
import json

try:
	import yaml
except ModuleNotFoundError:
	yaml = None
try:
	from muller.order_clusters import ClusterType, OrderClusterParameters
	from muller.get_genotypes import GenotypeOptions
	from muller.sort_genotypes import SortOptions
	from muller.time_series_import import import_timeseries

	from muller import get_genotypes
	from muller import order_clusters
	from muller import sort_genotypes
	from muller import data_conversions
except ModuleNotFoundError:
	from order_clusters import ClusterType, OrderClusterParameters
	from time_series_import import import_timeseries
	from get_genotypes import GenotypeOptions
	from sort_genotypes import SortOptions
	import get_genotypes
	import order_clusters
	import sort_genotypes
	import data_conversions

def workflow(input_filename: Path, output_folder: Path, program_options):
	compatibility_mode = program_options.mode
	if compatibility_mode:
		program_options_genotype = get_genotypes.GenotypeOptions.from_matlab()
		program_options_sort = sort_genotypes.SortOptions.from_matlab()
		program_options_clustering = order_clusters.OrderClusterParameters.from_matlab()
	else:
		freqs = program_options.frequencies
		if isinstance(freqs, str):
			if ',' in freqs:
				freqs = map(float, freqs.split(','))
			else:
				freqs = float(freqs)
		if isinstance(freqs, float):
			freqs = [math.fsum(itertools.repeat(freqs, i)) for i in range(int(1 / freqs) + 1)]
			freqs = [round(i,2) for i in freqs]

		program_options_genotype = get_genotypes.GenotypeOptions.from_parser(program_options)
		program_options_clustering = order_clusters.OrderClusterParameters.from_parser(program_options)
		program_options_sort = sort_genotypes.SortOptions(
			detection_breakpoint = program_options_genotype.detection_breakpoint,
			fixed_breakpoint = program_options_genotype.fixed_breakpoint,
			significant_breakpoint = program_options.significant_breakpoint,
			frequency_breakpoints = freqs
		)

	timepoints, info = import_timeseries(input_filename)

	mean_genotypes = get_genotypes.workflow(timepoints, options = program_options_genotype)
	mean_genotypes.to_excel(str(output_folder / (input_filename.stem + '.mean.xlsx')))
	sorted_genotypes = sort_genotypes.workflow(mean_genotypes)

	genotype_clusters = order_clusters.workflow(sorted_genotypes, options = program_options_clustering)

	# df = pandas.DataFrame(i.trajectory for i in genotype_clusters.values())
	formatted_output = data_conversions.generate_formatted_output(
		timepoints,
		mean_genotypes,
		genotype_clusters,
		program_options_genotype,
		program_options_sort,
		program_options_clustering
	)

	poutput_file = _output_folder / (_input_filename.stem + '.ggmuller_populations.csv')
	eoutput_file = _output_folder / (_input_filename.stem + '.ggmuller_edges.csv')
	formatted_output['ggmullerPopulationTable'].to_csv(str(poutput_file),index=False)
	formatted_output['ggmullerEdgeTable'].to_csv(str(eoutput_file),index=False)

	formatted_output['genotypeTable'] =  formatted_output['genotypeTable'].to_string()
	formatted_output['ggmullerPopulationTable'] = formatted_output['ggmullerPopulationTable'].to_string(index=False)
	formatted_output['ggmullerEdgeTable'] = formatted_output['ggmullerEdgeTable'].to_string(index=False)

	joutput_file = _output_folder / (_input_filename.stem + '.json')
	joutput_file.write_text(json.dumps(formatted_output, sort_keys = True, indent = 4))

	if yaml:
		youtput_file = _output_folder / (_input_filename.stem + '.yaml')
		youtput_file.write_text(yaml.dump(formatted_output))
	# pprint(formatted_output)
	return genotype_clusters


def create_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-i', '--input',
		help = "The table of trajectories to cluster.",
		action = 'store',
		dest = 'filename'
	)
	parser.add_argument(
		'-o', '--output',
		help = "The folder to save the files to.",
		action = 'store',
		dest = 'output_folder'
	)
	parser.add_argument(
		'--fixed',
		help = "The minimum frequency at which to consider a mutation fixed.",
		action = 'store',
		dest = 'fixed_breakpoint'
	)
	parser.add_argument(
		"--detected",
		help = "The minimum frequency at which to consider a mutation detected.",
		action = 'store',
		default = 0.03,
		dest = 'detection_breakpoint'
	)
	parser.add_argument(
		"-s", "--significant",
		help = "The frequency at which to consider a genotype significantly greater than zero.",
		action = 'store',
		default = 0.15,
		dest = "significant_breakpoint"
	)
	parser.add_argument(
		"--matlab",
		help = "Mimics the output of the original matlab script.",
		action = 'store_true',
		dest = "mode"
	)
	parser.add_argument(
		"-f", "--frequencies",
		help = 'The frequency cutoff to use when sorting the genotypes by first detected frequency. For example, a value of 0.15 will use the frequencies 0,.15,.30,.45...',
		action = 'store',
		dest = 'frequencies',
		default = 0.15
	)
	parser.add_argument(
		"-r", "--similarity-cutoff",
		help = "Maximum p-value difference to consider trajectories related. Used when grouping trajectories into genotypes.",
		action = "store",
		default = 0.05,
		dest = "similarity_breakpoint"
	)

	parser.add_argument(
		"-l", "--difference-cutoff",
		help = "Minimum p-value to consider a pair of genotypes unrelated. Used when splitting genotypes.",
		action = "store",
		default = 0.10,
		dest = "difference_breakpoint"
	)
	return parser


if __name__ == "__main__":
	cmd_parser = create_parser().parse_args()

	_input_filename = Path(cmd_parser.filename)
	if cmd_parser.output_folder:
		_output_folder = Path(cmd_parser.output_folder)
	else:
		_output_folder = _input_filename.parent

	if not _output_folder.exists():
		_output_folder.mkdir()

	workflow(_input_filename, _output_folder, program_options = cmd_parser)