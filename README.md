# Tabu Search per il problema di Job Shop Scheduling

Per lo svolgimento di questo progetto è stato utilizzato il linguaggio Python 3.7, e la libreria per lavorare sui grafi NetworkX (https://networkx.org) (`pip install networkx`)che si é rivelata di enorme utilità per calcolare in modo semplice e rapido il valore della funzione obiettivo, quindi il cammino di costo massimo del grafo, ma anche il test di ammissibilità, che consiste semplicemente nella ricerca di un ciclo all’interno della rete.

Il programma consiste in uno script che è possibile eseguire da linea di comando. Ad esso è stata aggiunta una gestione dei parametri d’ingresso della CLI, in modo che l’utente possa eseguire il programma impostandone i parametri a piacimento. In base ai valori dei parametri e alle preferenze dell’utente, il programma risolverà il problema in modo diverso, e con tecniche diverse.
```
usage: main.py [-h] [-v] [-i {toy,10x10x10}] [-m MULTISTART]
               [-e {LPT,SPT,MIS,MWKR,auto}] [-t] [-d TABU_LIST_DIM]
               [-x MAX_ITER] [-s STALLO]

Il programma risolve il problema del Job Shop Scheduling utilizzando la
TabuSearch partendo da una soluzione iniziale calcolata con un algoritmo
euristico costruttivo Greedy

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose, se è True mostra tutti i dettagli della
                        computazione dell'algoritmo a schermo, altrimenti se
                        False mostra solo la soluzione finale calcolata
  -i {toy,10x10x10}, --istanza {toy,10x10x10}
                        Scelta dell'istanza da dare in input tra le possibili,
                        cioè [toy, 10x10x10].
  -m MULTISTART, --multistart MULTISTART
                        Definisco il numero di soluzioni di partenza, in modo
                        da appplicare la tabu search partendo da ciascuna di
                        esse. Se ha valore 0, l'algoritmo esegue un single-
                        start per ciascuna delle possibili euristiche: LPT,
                        SPT, MIS, MWKR
  -e {LPT,SPT,MIS,MWKR,auto}, --euristica {LPT,SPT,MIS,MWKR,auto}
                        Euritica di selezione per l'algoritmo greedy, le
                        possibili opzioni sono LPT, SPT, MIS, MWKR, auto. Se
                        'auto' (default = auto) allora viene scelta
                        casualmente dall'algoritmo ad ogni iterazione.
  -t, --tabu_search     Se True, decido di utilizzare la tabu search per
                        migliorare la soluzione iniziale ottenuta
                        dall'algoritmo euristico greedy, altrimenti calcolo
                        solamente la soluzione ottenuta dall'algoritmo greedy.
  -d TABU_LIST_DIM, --tabu_list_dim TABU_LIST_DIM
                        Iperparametro per la tabu search: dimesione della tabu
                        list. (default = 2).
  -x MAX_ITER, --max_iter MAX_ITER
                        Iperparametro per la tabu search: massimo numero di
                        iterazioni per far terminare la tabu search. (default
                        = 5).
  -s STALLO, --stallo STALLO
                        Iperparametro per la tabu search: massimo numero di
                        iterazioni in cui la soluzione non migliora durante la
                        search oltre il quale l'algoritmo termina. (default =
                        3).
```

Il problema può essere risolto utilizzando in questo caso due istanze possibili:
- toy: istanza giocattolo statica e di piccole dimensioni, utilizzata soprattutto in fase di progettazione degli algoritmi.
``` 
  n = 3 # numero job # {1, 2, 3}
  m = 2 # numero macchine # {1, 2}
  lista_associazioni_macchine = [ # per ogni operazione dico su quale macchina va eseguita
    [0, 1, 0, 1, 0, 1, 0], 
    [0, 1, 0],
    [0, 1]
  ]
lista_durate = [ # per ogni operazione indico la sua durata 
    [2, 1, 2, 2, 1, 1, 1], [2, 2, 1],
    [2, 2]
 ]
 ```
- 10x10x10: Si tratta di una famosa istanza con 10 job, 10 operazioni per job e 10 macchine. Le durate sono generate casualmente con una distribuzione uniforme fra 1 e 100. Anche l’assegnazione delle operazioni alle macchine è randomica. E' sicuramente un’istanza più ”challenging” rispetto alla toy. La si pu`o vedere qui sotto:
```
import numpy as np
n = 10 # numero jobs e di operazioni per ciascuno 
m = 10 # numero macchine
d = 100 # durata massima delle operazioni 
generator = np.random.default_rng(seed=0)
l_assoc_macchine = generator.integers(low=0, high=m, size=(n, n)) 
lista_durate = generator.integers(low=1, high=d+1, size=(n, n))
```

Si può decidere di eseguire il programma calcolando solamente la soluzione greedy, oppure senza utilizzare la tabu search per migliorarla. Quindi con il comando
`python3 main.py`   
si calcola la soluzione senza l’utilizzo della ricerca locale. Viceversa, con  
`python3 main.py --tabu_search`  
il programma non si ferma dopo aver calcolato la soluzione greedy, ma procede con la ricerca locale utilizzando la tabu search per migliorare la qualità della soluzione iniziale.  
Eventualmente si possono aggiungere dei valori d’ingresso che vadano ad impostare gli iperparametri dell’algoritmo, come ad esempio:  
`python3 main.py --istanza=10x10x10 --euristica=LPT`  
Con questo comando è possibile specificare l’istanza di input da utilizzare tra le due disponibili, poi si può anche scegliere l’euristica che seleziona la prossima operazione ad ogni iterazione. Mentre riguardo alla ricerca locale, è possibile specificare il valore dei suoi iperparametri principali:  
`python3 main.py --tabu_search --tabu_list_dim=2 --max_iter=5 --stallo=3`  
Con questo comando si va innanzitutto ad attivare la tabu search per migliorare la soluzione inizia- le, poi se ne specificano la dimensione della tabu list, il numero massimo di iterazioni che la tabu search deve compiere, ed infine lo stallo che indica il numero massimo di iterazioni consecutive in cui non si ha un miglioramento della soluzione. Lo stallo e max iter sono utilizzati come condizione di stop della tabu search. Per questi iperparametri sono anche impostati dei valori di default, ma in generale questo approccio è sconsigliatissimo perché in generale un tuning di questi parametri fatto in modo poco intelligente può portare la tabu search a lavorare molto male, per questo é assolutamente consigliato impostare tali valori manualmente in base alla singola istanza.  
Di default il programma è in modalità single-start, cièe esegue solo una volta l’algoritmo per cercare la soluzione migliore. Tuttavia è possibile scegliere di risolvere il problema attraverso dei multi-start, cioè il programma crea calcola più soluzioni greedy di partenza, e per ciascuna di queste applica la tabu search. Basterà scegliere la migliore tra le soluzioni trovate. Per eseguire l’algoritmo con più thread di ricerca basta usare aggiungere il parametro apposito, seguito dal numero di thread che si desiderano:  
`python3 main.py --tabu_search --tabu_list_dim=2 --max_iter=5 --stallo=3 --multistart=5`  
In questo modo si attivano 5 percorsi di ricerca ciascuno assegnato ad un thread indipendente che la tabu search partendo dalla soluzione di partenza assegnata.
Da notare che se multistart è maggiore di 1, l’algoritmo ignorerà un eventuale valore del parametro euristica, perchè teoricamente ha poco senso eseguire più thread su soluzioni greedy calcolate tutte con la stessa euristica, perchè avrebbero tutte lo stesso valore. Pertanto in questo caso l’euristica venga scelta casualmente ad ogni iterazione dell’algoritmo greedy in modo da avere soluzioni di partenza sempre differenti. Invece se multistart=0, allora l’algoritmo calcola una soluzione di partenza per ogni euristica disponibile, in questo caso 4.
