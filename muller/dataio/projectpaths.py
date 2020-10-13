import json
from pathlib import Path
from typing import Union, Dict, List
import pandas


class OutputFilenames:
	""" Used to organize the files generated by the workflow.
	"""

	def __str__(self):
		string = f"OutputFilenames('{self.folder_output}')"
		return string

	def __init__(self, output: Path, name: str, suffix = 'tsv'):
		self.name = name
		self.suffix = suffix

		def check_folder(path: Union[str, Path]) -> Path:
			path = Path(path)
			if not path.exists():
				path.mkdir()
			return path.absolute()

		self.folder_output = check_folder(output)
		self.folder_supplementary = check_folder(self.folder_output / "supplementary-files")
		self.folder_figures = check_folder(self.folder_output / "graphics")
		self.folder_figures_unique = check_folder(self.folder_figures / "unique")
		self.folder_figures_lineage = check_folder(self.folder_figures / "lineage")
		self.folder_tables = check_folder(self.folder_output / "tables")
		self.folder_scripts = check_folder(self.folder_output / "scripts")

		# General Files
		self.filename_trajectory_table: Path = self.folder_output / (name + f'.trajectories.{suffix}')
		self.filename_table_genotypes: Path = self.folder_output / (name + f'.genotypes.{suffix}')
		self.filename_palette: Path = self.folder_supplementary / (name + f'.palette.json')

		# tables
		self.filename_table_trajectories: Path = self.folder_tables / (name + f'.trajectories.{suffix}')
		self.filename_table_trajectories_rejected: Path = self.folder_tables / (
				name + f"trajectories.rejected.{suffix}")
		# self.filename_table_genotypes: Path = self.folder_tables / (name + f'.genotypes.original.{suffix}')

		self.filename_table_population: Path = self.folder_tables / (name + f'.populations.{suffix}')
		self.filename_table_edges: Path = self.folder_tables / (name + f'.edges.{suffix}')
		self.filename_table_muller: Path = self.folder_tables / (name + f".muller.{suffix}")
		self.filename_table_lineage_scores: Path = self.folder_tables / (name + '.lineagescores.tsv')
		self.filename_table_linkage = self.folder_tables / (name + f".linkagematrix.tsv")
		self.filename_table_distance: Path = self.folder_tables / (name + f".distance.{suffix}")

		# graphics
		# The extensions fo reach figure will be generated based on which file formats the
		# corresponding plotter objects support.
		# The figures will also be generated twice, but there's no point in making a separate Path variable
		# For each pallette used.
		# Muller Plots
		# The muller diagram generator will automatically add filetype extensions and an svg render of each file.

		self.template_figure_panel_timeseries: str = (name + '.timeseriespanel')
		self.template_figure_panel_muller: str = (name + '.mullerpanel')
		self.template_figure_muller_diagram_annotated: str = (name + '.mullerdiagram.annotated')
		self.template_figure_muller_diagram_unannotated: str = (name + '.mullerdiagram.unannotated')
		# self.filename_figure_muller_diagram_clade_annotated: Path = self.folder_figures_lineage / (name + '.annotated')
		# self.filename_figure_muller_diagram_clade_unannotated: Path = self.folder_figures_lineage / (name + '.unannotated')
		# self.filename_figure_muller_diagram_distinct_annotated: Path = self.folder_figures_unique / (name + '.annotated')
		# self.filename_figure_muller_diagram_distinct_unannotated: Path = self.folder_figures_unique / (name + '.unannotated')

		## Timeseries plots
		self.template_figure_timeseries_genotype: str = (name + ".genotypes")
		self.template_figure_timeseries_trajectory: str = (name + f".trajectories")
		# self.filename_figure_timeseries_plot_genotype_unique: Path = self.folder_figures_unique / (name + '.genotypes')
		# self.filename_figure_timeseries_plot_genotype_clade: Path = self.folder_figures_lineage / (name + '.genotypes')

		## Lineage plots
		self.template_figure_lineageplot: str = (name + f".lineage")
		# self.filename_figure_lineage_distinct: Path = self.folder_figures_unique / (name + f".lineage.png")
		# self.filename_figure_lineage_clade: Path = self.folder_output / (name + '.lineage.png')

		## Other plots

		self.filename_figure_distance_heatmap: Path = self.folder_figures / (name + f".pairwisedistance.svg")
		self.filename_figure_linkage_plot = self.folder_figures / (name + f".dendrogram.png")
		self.filename_figure_distribution = self.folder_figures / (name + f".distribution.png")
		# scripts
		self.filename_script_r_script: Path = self.folder_scripts / (name + '.r')
		self.filename_script_graphviz: Path = self.folder_scripts / (name + '.dot')

		# supplementary files
		self.filename_data_genotype_members: Path = self.folder_supplementary / (name + '.genotypemembers.json')
		self.filename_parameters: Path = self.folder_supplementary / (name + '.options.json')
		self.filename_clusterdata: Path = self.folder_supplementary / (name + '.clusterdata.json')
		self.genotype_information: Path = self.folder_supplementary / (name + '.genotypeinformation.json')

	@staticmethod
	def _generate_trajectory_table(table_trajectories: pandas.DataFrame, table_info: pandas.DataFrame,
			genotype_members: Dict[str, List[str]]):
		"""
			Merges all of the available data on trajectories into a single table. Both the `trajectories` and trajectory_info` table
			should be indexed by trajectory id.
		"""
		# Convert the mapping from genotype->members into members->genotype
		trajectory_genotypes = dict()
		for genotype_name, genotype_members in genotype_members.items():
			for member_name in genotype_members:
				trajectory_genotypes[member_name] = genotype_name

		table_trajectories = table_trajectories.merge(table_info, left_index = True, right_index = True, how = 'outer')

		# Add a column to the `trajectories` table with the resulting parent genotype.
		table_trajectories['genotype'] = [trajectory_genotypes.get(i, 'rejected') for i in table_trajectories.index]

		return table_trajectories

	@staticmethod
	def get_template(folder: Path, template: str, extension: str):
		"""
			Generates an actual filename based on the template string.
		"""
		if not extension.startswith('.'):
			extension = '.' + extension
		result = folder / (template + extension)
		return result

	def save_projectdata_basic(self, data):
		program_options = {key: str(value) for key, value in vars(data.program_options).items()}
		options = {
			'version':    data.version,
			'filename':   str(data.filename),
			'parameters': program_options
		}

		self.filename_parameters.write_text(json.dumps(options, indent = 4, sort_keys = True))

	def save_workflow_clustering(self, data):

		table_trajectories = self._generate_trajectory_table(
			data.table_trajectories,
			data.table_trajectories_info,
			data.genotype_members
		)

		table_trajectories.to_csv(self.filename_table_trajectories, sep = self.delimiter)
		# TODO: merge table_trajectories_info with the trajectories table.
		# data.table_trajectories_info.to_csv()
		members = {key: '|'.join(values) for key, values in data.genotype_members.items()}

		data.table_genotypes['members'] = [members[i] for i in data.table_genotypes.index]
		data.table_genotypes.to_csv(self.filename_table_genotypes, sep = self.delimiter)
		if data.matrix_distance is not None:
			data.matrix_distance.squareform().to_csv(self.filename_table_distance, sep = self.delimiter)
		if data.clusterdata is not None:
			data.clusterdata.table_linkage.to_csv(self.filename_table_linkage, sep = self.delimiter)

		self.filename_data_genotype_members.write_text(json.dumps(data.genotype_members, indent = 4, sort_keys = True))

	def save_workflow_hierarchy(self, data):
		if data is not None:
			self.filename_clusterdata.write_text(json.dumps(data.to_dict(), indent = 4, sort_keys = True))

	def save_workflow_lineage(self, data):
		data.table_scores.to_csv(self.filename_table_lineage_scores, sep = self.delimiter, index = False)

	def save_workflow_ggmuller(self, data):
		if not self.filename_table_population.exists():
			data.table_populations.to_csv(self.filename_table_population, sep = self.delimiter, index = False)
		if not self.filename_table_edges.exists():
			table_edges = data.series_edges.to_frame()
			# GGmuller expected the columns to be ordered as ['Parent', 'Identity']
			table_edges = table_edges[['Parent', 'Identity']]
			data.series_edges.to_frame().to_csv(self.filename_table_edges, sep = self.delimiter, index = True)

		data.table_muller.to_csv(self.filename_table_muller, sep = self.delimiter, index = False)

	@property
	def delimiter(self) -> str:
		if self.suffix == 'tsv':
			return '\t'
		else:
			return ','
