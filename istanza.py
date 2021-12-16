import numpy as np

def read_input():

    n = 3 # numero job
    m = 2 # numero macchine
    lista_associazioni_macchine = [ # per ogni operazione dico su quale macchina va eseguita
        [0, 1, 0, 1, 0, 1, 0], 
        [0, 1, 0], 
        [0, 1]
    ] 
    lista_durate = [  # per ogni operazione indico la sua durata
        [2, 1, 2, 2, 1, 1, 1], 
        [2, 2, 1], 
        [2, 2]
    ]

    """ Istanza 10x10x10 """
    # n = 10 # jobs, e operazioni per ciascuno
    # m = 10 # machines

    # generator = np.random.default_rng(seed=0)

    # lista_associazioni_macchine = generator.integers(low=0, high=m, size=(n, n))
    # lista_durate = generator.integers(low=1, high=n+1, size=(n, n))

    return n, m, lista_associazioni_macchine, lista_durate