import math

import pandas

try:
	from inheritance.order_by_area import area_of_series, calculate_common_area
except ModuleNotFoundError:
	from ...inheritance.order_by_area import area_of_series, calculate_common_area
def minkowski_distance(left: pandas.Series, right: pandas.Series, p: int) -> float:
	""" Calculates the minkowski distance between two series. Essentially just a generic lp-norm.
		Parameters
		----------
		left:pandas.Series
		right:pandas.Series
		p:int
	"""
	total = sum([math.pow(abs(i - j), p) for i, j in zip(left.tolist(), right.tolist())])
	return math.pow(total, 1 / p)


def pearson_correlation_distance(left: pandas.Series, right: pandas.Series) -> float:
	"""
		Calculates the pearson correlation between two series. The resulting value lies in the range [0,2].
	Parameters
	----------
	left:pandas.Series
	right:pandas.Series

	Returns
	-------
	float
	"""

	pcc = left.corr(right, method = 'pearson')
	# convert to distance metric.
	return 1 - pcc


# noinspection PyTypeChecker
def binomial_distance(left: pandas.Series, right: pandas.Series) -> float:
	""" Based on the binomial calculations present in the original matlab scripts."""
	# Find the mean frequency of each timepoint
	# index is timepoints,  values are frequencies
	not_detected_fixed_df = pandas.concat([left, right], axis = 1)
	mean: pandas.Series = not_detected_fixed_df.mean(axis = 1)

	# Calculate sigma_freq
	# E(sigma) = (1/n) sum(sigma) = (1/n) sum(np(1-p)) == sum(p(1-p)
	# E(sigma_p) = (1/n) E(sigma) == 1/n(sum(p(1-p))
	# E(d_bar) = 1/n(sum(di)) == 1/n (n*sum(di))
	# pandas.Series.radd is slow for some reason. Use '-' operator instead.
	sigma_freq: pandas.Series = mean.mul(1 - mean)
	# Difference of frequencies at each timepoint
	# difference: pandas.Series = not_detected_fixed_df.iloc[:, 0] - not_detected_fixed_df.iloc[:, 1]
	difference = not_detected_fixed_df.diff(axis = 1).iloc[:, 1]
	sigma_pair: float = sigma_freq.sum() / len(mean)
	# Sum of differences
	difference_mean: float = abs(difference).sum()

	X = difference_mean / (math.sqrt(2 * sigma_pair))

	return X


def binomial_probability(left: pandas.Series, right: pandas.Series) -> float:
	X = binomial_distance(left, right)
	value = 1 - math.erf(X)
	return value


def bray_curtis(left: pandas.Series, right: pandas.Series) -> float:
	area_left = area_of_series(left)
	area_right = area_of_series(right)
	area_shared = calculate_common_area(left, right, 0.03)

	return 1-(2 * area_shared) / (area_left + area_right)


def jaccard_distance(left: pandas.Series, right: pandas.Series) -> float:
	area_left = area_of_series(left)
	area_right = area_of_series(right)
	area_shared = calculate_common_area(left, right, 0.03)
	j = area_shared / (area_left + area_right - area_shared)
	return 1 - j


def calculate_all_distances(left: pandas.Series, right: pandas.Series) -> pandas.Series:
	minkowski = minkowski_distance(left, right, 2)
	pearson = pearson_correlation_distance(left, right)
	bd = binomial_distance(left, right)
	bc = bray_curtis(left, right)

	data = {
		'minkowski':        minkowski,
		'pearson':          pearson,
		'binomialDistance': bd,
		'brayCurtis':       bc,
		'jaccard':			jaccard_distance(left, right),
		'combined':			2*pearson + minkowski
	}

	return pandas.Series(data)


if __name__ == "__main__":
	pass
