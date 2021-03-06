import argparse
import os
import time
from collections import Counter
from os import path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tabulate
import torch.utils.data

from scripts.consts.statistics import *
from scripts.loaders import load_embedder_from_model_path, load_model_from_path
from scripts.utils import print_progress_bar
from wikisearch.consts.mongo import CSV_SEPARATOR

# Prepare the statistics table
pd.set_option('display.max_columns', 10)
pd.set_option('precision', 2)


def create_distances_dataframe(dataset_file_path):
    # Loads the dataset file
    dataset = pd.read_csv(dataset_file_path, sep=CSV_SEPARATOR).values

    df = pd.DataFrame(columns=[SRC_NODE, DST_NODE, BFS_DIST, NN_DIST])
    with torch.no_grad():
        start = time.time()
        for idx, (source, destination, actual_distance) in enumerate(dataset, 1):
            df = df.append(
                {
                    SRC_NODE: source,
                    DST_NODE: destination,
                    BFS_DIST: actual_distance,
                    NN_DIST: model(embedder.embed(source).unsqueeze(0), embedder.embed(destination).unsqueeze(0)).round().int().item()
                }, ignore_index=True)
            print_progress_bar(idx, len(dataset), time.time() - start, prefix=f'Progress: ', length=50)

    return df.infer_objects()


def create_histogram(values, values_ticks, title, output_path, histogram_name):
    plt.figure(figsize=(16, 9))
    plt.title(title)
    plt.xlabel("Differences")
    plt.ylabel("# Occurences")
    counts, _, _ = plt.hist(values, bins=values_ticks, align='left')
    plt.gca().set_xticks(values_ticks[:-1])
    for i, distance in enumerate(values_ticks[:-1]):
        plt.text(distance, counts[i] + 1, str(int(counts[i])))
    plt.savefig(path.join(output_path, histogram_name))


def create_percentile_graph(values, title, output_path):
    sorted_values = sorted(values)
    values_length = len(sorted_values)
    interval = 0.01
    # quantiles is [0, interval, 2*interval, ..., 1 - interval, 1]
    quantiles = np.arange(0, 1 + interval, interval)
    plt.figure(figsize=(16, 9))
    plt.title(title)
    plt.xlabel("Quantiles")
    plt.ylabel("# of Distance Differences at Quantile")
    distances_at_quantiles = np.array([sorted_values[max(0, int(round(quantile * values_length)) - 1)] for quantile in quantiles])
    auc = distances_at_quantiles[1:].sum() * interval
    plt.plot(quantiles, distances_at_quantiles, drawstyle='steps')
    plt.fill_between(quantiles, 0, distances_at_quantiles, step='pre', alpha=0.3)
    plt.legend([f"AUC = {auc:.3f}"])
    plt.xticks(np.arange(0, 1.05, 0.05))
    plt.grid(True, which='both')
    plt.savefig(path.join(output_path, 'differences_quantiles.jpg'))
    return auc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model', required=True, help='Path to the model file. When running from linux - '
                                                             'notice to not put a \'/\' after the file name')
    parser.add_argument('-df', '--dataset_file', required=True, help='Path to a dataset file')
    args = parser.parse_args()

    output_dir = path.dirname(args.model)
    model_file_name = path.splitext(path.basename(args.model))[0]

    embedder = load_embedder_from_model_path(args.model)
    model = load_model_from_path(args.model)

    statistics_df = create_distances_dataframe(args.dataset_file)

    # Print out the statistics to csv file
    statistics_file_path = path.join(output_dir, f"{model_file_name}.stats")
    statistics_df.to_csv(statistics_file_path, sep=CSV_SEPARATOR, header=True, index=False)

    # Compare between BFS to NN
    first_distances = statistics_df[BFS_DIST]
    second_distances = statistics_df[NN_DIST]

    # Generate distances histogram
    plt.figure(figsize=(16, 9))
    plt.title(f"Distances {BFS_DIST} vs. {NN_DIST}")
    plt.xlabel("Distances")
    plt.ylabel("# Occurences")
    width = 0.3
    first_distances_ticks = np.arange(min(first_distances), max(first_distances) + 1)
    first_distances_counter = Counter(first_distances)
    plt.bar(first_distances_ticks - width / 2,
            [first_distances_counter[distance] for distance in first_distances_ticks], width=width, align='center')
    second_distances_ticks = np.arange(min(second_distances), max(second_distances) + 1)
    second_distances_counter = Counter(second_distances)
    plt.bar(second_distances_ticks + width / 2,
            [second_distances_counter[distance] for distance in second_distances_ticks], width=width, align='center')
    plt.legend([BFS_DIST, NN_DIST])
    plt.savefig(path.join(os.path.join(output_dir, f"{BFS_DIST}_{NN_DIST}_distances_histogram.jpg")))

    # Generate differences histogram
    differences = first_distances - second_distances
    differences_ticks = range((min(differences)), max(differences) + 2)
    create_histogram(differences, differences_ticks,
                     f"Differences between {BFS_DIST} to {NN_DIST}",
                     output_dir, f"{BFS_DIST}_{NN_DIST}_differences_histogram.jpg")

    # Generate absolute differences histogram
    abs_differences = abs(first_distances - second_distances)
    abs_differences_ticks = range(min(abs_differences), max(abs_differences) + 2)
    create_histogram(abs_differences, abs_differences_ticks,
                     f"Absolute Differences between {BFS_DIST} to {NN_DIST}",
                     output_dir, f"{BFS_DIST}_{NN_DIST}_abs_differences_histogram.jpg")

    percentile_graph_auc = create_percentile_graph(abs_differences, 'Quantiles of Distance Differences', output_dir)
    differences_length = len(abs_differences)
    admissability = sum(differences >= 0) / differences_length

    # Options used for printing dataset summaries and statistics
    pd.set_option('display.max_columns', 10)
    pd.set_option('precision', 2)
    statistics_df = pd.DataFrame(columns=['Methods Compared', 'Admissablity', 'AUC Quantile', 'Average Difference',
                                          'Std', 'Average Abs Difference', 'Std for Abs', '50% Percentage',
                                          '75% Percentage', '90% Percentage'])
    sorted_differences = abs_differences.sort_values().get_values()
    statistics_df = statistics_df.append(
        {
            'Methods Compared': f"{BFS_DIST} to {NN_DIST}",
            'Admissablity': f"{admissability * 100:.1f}%",
            'AUC Quantile': percentile_graph_auc,
            '50% Percentage': abs_differences.median(),
            '75% Percentage': sorted_differences[round(0.75 * differences_length)],
            '90% Percentage': sorted_differences[round(0.90 * differences_length)],
            'Average Difference': differences.mean(),
            'Std': differences.std(),
            'Average Abs Difference': abs_differences.mean(),
            'Std for Abs': abs_differences.std()
        }, ignore_index=True)

    # Print out statistics to file
    statistics_df = statistics_df.rename(lambda col: col.replace(' ', '\n'), axis='columns')
    print(tabulate.tabulate(statistics_df, headers='keys', tablefmt='fancy_grid', floatfmt='.2f', showindex=False))
    with open(path.join(output_dir, "distances_differences.stats"), 'w', encoding='utf8') as f:
        f.write(tabulate.tabulate(statistics_df, headers='keys', showindex=False, tablefmt='fancy_grid', floatfmt='.2f'))
