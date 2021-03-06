import torch

from wikisearch.consts.mongo import ENTRY_TEXT
from wikisearch.embeddings import FastText


class FastTextTextAverage(FastText):
    """
    The class represents the fasttext embedding when a page's vector is calculated by taking an average
    of all the words in the page's text
    """

    def _embed(self, page):
        tokenized_text = self.tokenize_text(page[ENTRY_TEXT])
        embedded_words = [self._model[tagged_word] for tagged_word in tokenized_text
                          if tagged_word in self._model.__dict__['vocab']]

        # Getting also the words without a vector representation
        # embedded_words, missing_vector_words = self._get_embedded_words_and_missing_vectors(tokenized_text)

        torched_words_vectors = torch.Tensor(embedded_words)

        return self._zeros_if_empty_vector(torch.mean(torched_words_vectors, 0))

    def _get_embedded_words_and_missing_vectors(self, text):
        """
        Embeds the words and indicates which words can't be embedded
        :param text: The words to examine if they can be embedded
        :return: The embedded words and the words which cannot be embedded
        """
        embedded_words = []
        missing_vector_words = set()
        for word in text:
            if word in self._model.__dict__['vocab']:
                embedded_words.append(self._model[word])
            else:
                missing_vector_words |= {word}
        print(f"-INFO- Found {len(missing_vector_words)} words without vector representation.\n"
              f"The words are: {missing_vector_words}")
        return embedded_words, missing_vector_words
