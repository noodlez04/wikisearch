import argparse
import os
import random
import time
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tabulate

from scripts.utils import print_progress_bar
from wikisearch.graph import WikiGraph

# Options used for printing dataset summaries and statistics
pd.set_option('display.max_columns', 10)
pd.set_option('precision', 2)

dataset_types = ['train', 'validation', 'test']
rnd_generator = random.Random()


def find_at_distance(graph, source_node, desired_distance):
    """
    Find a node at desired distance from source node
    :param graph: wikisearch.WikiGraph instance
    :param source_node: wikisearch.GraphNode instance of source page
    :param desired_distance: distance (minimal) at which a node should be found
    :return: node at desired distance / shorter, if there are no nodes at such distance, and the real distance
    """
    if not list(graph.get_node_neighbors(source_node)):
        return None, 0, 0, 0

    actual_distance = 0
    nodes_developed = 0
    current_distance_nodes = {source_node}
    all_nodes = set(current_distance_nodes)
    nodes_at_distances = []
    developed_at_distances = []
    times_at_distances = []

    start = time.time()
    while actual_distance < desired_distance:
        # If neighbor has been found before, then there's a shorter path, and we don't add it to current
        # distance
        next_distance_nodes = [neighbor for node in current_distance_nodes
                               for neighbor in graph.get_node_neighbors(node)]
        nodes_developed += len(next_distance_nodes)
        # After getting the number of nodes developed, we can get rid of duplicate nodes in the list
        next_distance_nodes = set(next_distance_nodes)
        next_distance_nodes = next_distance_nodes - all_nodes
        if not next_distance_nodes:
            # No neighboring nodes (in shortest distance), so we break and choose one at random
            break
        nodes_at_distances.append(next_distance_nodes)
        developed_at_distances.append(nodes_developed)
        all_nodes.update(next_distance_nodes)
        times_at_distances.append(time.time() - start)
        actual_distance += 1
        current_distance_nodes = next_distance_nodes

    if actual_distance == 0:
        return None, 0, 0, 0

    actual_distance = desired_distance if actual_distance == desired_distance else rnd_generator.randint(1, actual_distance)
    index = actual_distance - 1
    # Return a random neighbor at actual_distance (which may also be desired distance) away from source page
    return rnd_generator.choice(list(nodes_at_distances[index])), actual_distance, developed_at_distances[index], times_at_distances[index]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-records', '-n', help='Number of records for training, validation, test sets', nargs=3,
                        type=int, required=True)
    parser.add_argument('--seed', '-s', type=int, help='Seed used by random generator')
    parser.add_argument('--out', '-o', required=True, help='Output dir path')
    parser.add_argument('--max-distance', '-d', type=int, default=20, help='Maximum distance to search for')
    args = parser.parse_args()

    if args.max_distance < 1:
        raise ValueError('Distance is not a positive integer')

    os.makedirs(args.out, exist_ok=True)

    rnd_generator.seed(args.seed)  # If args.seed is None, system's time is used (default behavior)

    graph = WikiGraph()
    graph_keys = sorted(graph.keys())

    entire_start = time.time()
    distances = defaultdict(list)
    developed_per_distance = defaultdict(list)
    runtimes = {}
    runtimes_per_distance = defaultdict(list)
    # Go over all types of datasets
    for dataset_type, num_records in zip(dataset_types, args.num_records):
        dataset_start = time.time()
        dataset = []
        # Build current dataset
        for i in range(num_records):
            dest = None
            source = None
            desired_distance = rnd_generator.randint(1, args.max_distance)
            distance, runtime, developed = 0, 0, 0
            while dest is None:  # This is to make sure that the source node actually has neighbors in the first place
                source = rnd_generator.choice(graph_keys)
                dest, distance, developed, runtime = find_at_distance(graph, graph.get_node(source), desired_distance)
            distances[dataset_type].append(distance)
            dataset.append((source, dest.title, distance))
            runtimes_per_distance[distance].append(runtime)
            developed_per_distance[distance].append(developed)
            print_progress_bar(i + 1, num_records, time.time() - dataset_start, prefix=dataset_type.capitalize(), length=50)
        print(f'-INFO- {dataset_type.capitalize()}: {num_records} datapoints created.')

        # Create dataframe from dataset
        df = pd.DataFrame.from_records(dataset, columns=['source', 'destination', 'min_distance'])
        # Define path to save dataset to
        dataset_path = os.path.abspath(os.path.join(args.out, dataset_type + '.csv'))
        # Save dataset (through dataframe)
        df.to_csv(dataset_path, header=True, index=False, sep='\t')
        runtimes[dataset_type] = time.time() - dataset_start

        # Generate distances histogram
        distance_occurrences = df['min_distance'].tolist()
        distances_ticks = range(min(distance_occurrences), max(distance_occurrences) + 2)

        plt.figure(figsize=(16, 9))
        plt.title('Number of records/distance')
        plt.xlabel('Distance')
        plt.ylabel('Number of records')
        counts, _, _ = plt.hist(distance_occurrences, bins=distances_ticks, align='left')
        plt.gca().set_xticks(distances_ticks[:-1])
        for i, distance in enumerate(distances_ticks[:-1]):
            plt.text(distance, counts[i] + 0.1, str(int(counts[i])))
        plt.savefig(os.path.splitext(dataset_path)[0] + '_distance_histogram.jpg')

    # Create statistics for dataset
    statistics_df = pd.DataFrame(columns=['Dataset', 'Number of entries', 'Build time', 'Average build time/entry',
                                          'Min distance', 'Max distance', 'Average distance', 'Standard deviation'])
    for dataset_type, num_records in zip(dataset_types, args.num_records):
        statistics_df = statistics_df.append({'Dataset': dataset_type.capitalize(),
                                              'Number of entries': num_records,
                                              'Build time': runtimes[dataset_type],
                                              'Average build time/entry': runtimes[dataset_type] / num_records,
                                              'Min distance': np.min(distances[dataset_type]),
                                              'Max distance': np.max(distances[dataset_type]),
                                              'Average distance': np.mean(distances[dataset_type]),
                                              'Standard deviation': np.std(distances[dataset_type])},
                                             ignore_index=True)

    # Print out statistics to file
    statistics_df = statistics_df.rename(lambda col: col.replace(' ', '\n'), axis='columns')
    print(tabulate.tabulate(statistics_df, headers='keys', showindex=False, tablefmt='fancy_grid', floatfmt='.2f'), )
    with open(os.path.join(args.out, 'datasets_stats.txt'), 'w') as f:
        f.write(tabulate.tabulate(statistics_df, headers='keys', showindex=False, tablefmt='fancy_grid', floatfmt='.2f'))

    # Create histogram of running times per distance
    runtimes_per_distance_averages = {k: np.mean(v) for k, v in runtimes_per_distance.items()}
    runtimes_per_distance_stds = {k: np.std(v) for k, v in runtimes_per_distance.items()}
    distances = sorted(runtimes_per_distance.keys())
    plt.figure(figsize=(16, 9))
    plt.title('Running times/distance')
    plt.xlabel('Distance')
    plt.ylabel('Running times (s)')
    plt.bar(distances, [runtimes_per_distance_averages[distance] for distance in distances],
            yerr=[runtimes_per_distance_stds[distance] for distance in distances])
    for distance in distances:
        plt.text(distance, runtimes_per_distance_averages[distance] + 0.1, str(round(runtimes_per_distance_averages[distance], 2)))
    plt.savefig(os.path.join(args.out, 'distance_runtimes.jpg'))

    # Create histogram of developed nodes per distance
    developed_per_distance_averages = {k: np.mean(v) for k, v in developed_per_distance.items()}
    developed_per_distance_stds = {k: np.std(v) for k, v in developed_per_distance.items()}
    distances = sorted(runtimes_per_distance.keys())
    plt.figure(figsize=(16, 9))
    plt.title('Developed nodes/distance')
    plt.xlabel('Distance')
    plt.ylabel('Developed nodes')
    plt.bar(distances, [developed_per_distance_averages[distance] for distance in distances],
            yerr=[developed_per_distance_stds[distance] for distance in distances])
    for distance in distances:
        plt.text(distance, developed_per_distance_averages[distance] + 0.1, str(int(developed_per_distance_averages[distance])))
    plt.savefig(os.path.join(args.out, 'distance_developed_nodes.jpg'))
