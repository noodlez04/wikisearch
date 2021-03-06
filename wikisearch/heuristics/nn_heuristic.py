from .heuristic import Heuristic


class NNHeuristic(Heuristic):
    """
    The NN Heuristic class
    """

    def __init__(self, model, embedder):
        super(NNHeuristic, self).__init__()
        self._model = model
        self._embedder = embedder

    def _calculate(self, curr_state, dest_state):
        curr_embedding = self._embedder.embed(curr_state.title).unsqueeze(0)
        dest_embedding = self._embedder.embed(dest_state.title).unsqueeze(0)

        return self._model(curr_embedding, dest_embedding).round().int().item()
