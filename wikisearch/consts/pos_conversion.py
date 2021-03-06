# Dictionary to convert from Penn Treebank POS to Universal POS
TREEBANK_TO_UNIVERSAL = \
    {
        '#': 'SYM', '$': 'SYM', 'SYM': 'SYM',
        '"': 'PUNCT', ',': 'PUNCT', '-LRB-': 'PUNCT', '-RRB-': 'PUNCT', '.': 'PUNCT', ':': 'PUNCT', 'HYPN': 'PUNCT', '``': 'PUNCT',
        'AFX': 'ADJ', 'JJ': 'ADJ', 'JJR': 'ADJ', 'JJS': 'ADJ',
        'CC': 'CCONJ',
        'CD': 'NUM',
        'DT': 'DET', 'PDT': 'DET', 'PRP$': 'DET', 'WDT': 'DET', 'WP$': 'DET',
        'EX': 'PRON', 'WP': 'PRON',
        'FW': 'X', 'LS': 'X', 'NIL': 'X',
        'IN': 'ADP',
        'MD': 'VERB', 'VB': 'VERB', 'VBD': 'VERB', 'VBG': 'VERB', 'VBN': 'VERB', 'VBP': 'VERB', 'VBZ': 'VERB',
        'NN': 'NOUN', 'NNS': 'NOUN',
        'NNP': 'PROPN', 'NNPS': 'PROPN',
        'POS': 'PART', 'TO': 'PART',
        'PRP': 'PRON',
        'RB': 'ADV', 'RBR': 'ADV', 'RBS': 'ADV', 'WRB': 'ADV',
        'RP': 'ADP',
        'UH': 'INTJ',
    }
