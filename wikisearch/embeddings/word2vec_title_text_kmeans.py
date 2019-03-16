import torch

from wikisearch.consts.mongo import ENTRY_TITLE
from wikisearch.embeddings import Word2VecTitle, Word2VecTextKMeans


class Word2VecTitleTextKMeans(Word2VecTitle):
    def __init__(self, save_to_db=True):
        # We do not save the Word2VecTitleCategoriesMultiHot to db because of size of embeddings in MongoDB
        super(Word2VecTitleTextKMeans, self).__init__(save_to_db=False)
        self._word2vec_title_embedder = Word2VecTitle(save_to_db)
        self._word2vec_text_kmeans_embedder = Word2VecTextKMeans(save_to_db)

        # Because embeddings are not in the DB, and we want to save time during runtime, we build all concatenated
        # embeddings up-front
        word2vec_title_embedder_titles = set(self._word2vec_title_embedder._cached_embeddings.keys())
        word2vec_text_kmeans_embedder_titles = set(self._word2vec_text_kmeans_embedder._cached_embeddings.keys())
        self._cached_embeddings = {title: torch.cat((self._word2vec_title_embedder.embed(title),
                                                     self._word2vec_text_kmeans_embedder.embed(title)), dim=0)
                                   for title in word2vec_title_embedder_titles & word2vec_text_kmeans_embedder_titles}

        # Clear caches of sub-embedders, to free up memory, because we've already got those cached entried
        # concatenated in the current embedder
        self._word2vec_title_embedder._cached_embeddings = {}
        self._word2vec_text_kmeans_embedder._cached_embeddings = {}

    def _embed(self, page):
        return torch.cat((self._word2vec_title_embedder.embed(page[ENTRY_TITLE]),
                          self._word2vec_text_kmeans_embedder.embed(page[ENTRY_TITLE])), dim=0)
