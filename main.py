import argparse

from wikisearch.astar import Astar
from wikisearch.consts.mongo import WIKI_LANG
from wikisearch.costs.uniform_cost import UniformCost
from wikisearch.graph import WikiGraph
from wikisearch.heuristics.bfs_heuristic import BFSHeuristic
from wikisearch.strategies.default_astar_strategy import DefaultAstarStrategy
from wikisearch.utils.clean_data import tokenize_title

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True, help="Source title")
    parser.add_argument('-d', '--dest', required=True, help="Destination title")
    parser.add_argument('-t', '--time_limit', type=float, default=60,
                        help="Time limit (seconds) for source-dest distance calculation")
    args = parser.parse_args()

    cost = UniformCost()
    heuristic = BFSHeuristic()
    strategy = DefaultAstarStrategy()
    graph = WikiGraph(WIKI_LANG)
    astar = Astar(cost, heuristic, strategy, graph)

    path, distance, developed = astar.run(tokenize_title(args.source), tokenize_title(args.dest), args.time_limit)
    if path:
        print("Path: ", end="")
        print(*[node.title for node in path], sep=" -> ")
        print("Distance:", distance)
        print("Number of nodes developed:", developed)
    else:
        print("Path not found. Number of nodes developed:", developed)
