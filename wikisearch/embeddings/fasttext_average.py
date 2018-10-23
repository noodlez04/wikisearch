import torch

from wikisearch.embeddings import FastText


class FastTextAverage(FastText):
    def _embed(self, tokenized_text):
        embedded_words = [self._model[tagged_word] for tagged_word in tokenized_text
                          if tagged_word in self._model.__dict__['vocab']]

        # Don't delete!!!!!!
        # Getting also the words without a vector representation
        # embedded_words, missing_vector_words = self._get_embedded_words_and_missing_vectors(tokenized_text)

        torched_words_vectors = torch.Tensor(embedded_words)

        return torch.mean(torched_words_vectors, 0)

    def _get_embedded_words_and_missing_vectors(self, tokenized_text):
        embedded_words = []
        missing_vector_words = set()
        for word in tokenized_text:
            if word in self._model.__dict__['vocab']:
                embedded_words.append(self._model[word])
            else:
                missing_vector_words |= {word}
        print(f"Found {len(missing_vector_words)} words without vector representation.\n"
              f"The words are: {missing_vector_words}")
        return embedded_words, missing_vector_words
