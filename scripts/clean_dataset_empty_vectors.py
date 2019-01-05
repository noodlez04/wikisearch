import argparse
import time
from importlib import import_module

from scripts.utils import print_progress_bar
from wikisearch.consts.mongo import WIKI_LANG, PAGES
from wikisearch.embeddings import EMBEDDINGS_MODULES, AVAILABLE_EMBEDDINGS

parser = argparse.ArgumentParser()
parser.add_argument('--in', '-i', dest='inp', required=True)
parser.add_argument('--out', '-o', required=True)
parser.add_argument('--embedding', required=True, choices=AVAILABLE_EMBEDDINGS)

args = parser.parse_args()

# Loads dynamically the relevant embedding class.
embedding_module = import_module('.'.join(['wikisearch', 'embeddings', EMBEDDINGS_MODULES[args.embedding]]),
                                 package='wikisearch')
embedding_class = getattr(embedding_module, args.embedding)

embedder = embedding_class(WIKI_LANG, PAGES)

missing_counter = 0
with open(args.inp, 'r', encoding='utf8') as in_file:
    dataset_size = len(list(in_file.readlines())) - 1

with open(args.inp, 'r', encoding='utf8') as in_file:
    with open(args.out, 'w', encoding='utf8') as out_file:
        start = time.time()
        for i, line in enumerate(in_file.readlines()):
            if i == 0:
                out_file.write(line)
                continue
            source_title, dest_title, min_distance = line.split('\t')
            source_tensor = embedder.embed(source_title)
            dest_tensor = embedder.embed(dest_title)

            if source_tensor.size() and dest_tensor.size():
                out_file.write(f'{source_title}\t{dest_title}\t{min_distance}')
            else:
                missing_counter += 1
            print_progress_bar(i, dataset_size, time.time() - start, length=50)
print(f'-INFO- Missing pages\' vector amount: {missing_counter}')