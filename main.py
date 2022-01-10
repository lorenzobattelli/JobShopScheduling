from networkx import find_cycle, DiGraph
from networkx.exception import NetworkXNoCycle
from networkx.algorithms.dag import dag_longest_path, dag_longest_path_length
from copy import deepcopy
from random import choice
from argparse import ArgumentParser
import numpy as np

def read_input(istanza):

    if istanza == "toy":
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

    else:
        
        n = 10 # jobs, e operazioni per ciascuno
        m = 10 # machines
        d = 100 # durata massima
        generator = np.random.default_rng(seed=0)

        lista_associazioni_macchine = generator.integers(low=0, high=m, size=(n, n))
        lista_durate = generator.integers(low=1, high=d+1, size=(n, n))

    return n, m, lista_associazioni_macchine, lista_durate


class BgColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Job:
    '''
        Un job è formato da una lista di operazioni da eseguire sulle macchine
        Attributi:
        - id, identificativo del job
        - lista_operazioni che compongono il job, da eseguire in sequenza
    '''

    def __init__(self, id=0, lista_operazioni=[]):
        self.id = id
        self.lista_operazioni = lista_operazioni
    
    def __str__(self):
        return "Job {}: {}".format(self.id, [op.id for op in self.lista_operazioni])


class Operazione:
    '''
        Per ciascuna operazione tengo traccia di che job fa parte, e la macchina
        su cui va eseguita.
        Attributi:
        - id, identificativo dell'operazione
        - durata
        - job a cui appartiene
        - macchina su cui va eseguita
    '''

    def __init__(self, id, durata, job_id, macchina):
        self.id = id
        self.durata = durata
        self.job_id = job_id
        if isinstance(macchina, Macchina):
            self.macchina = macchina    
        else:
            raise Exception("Errore nell'istanziare il parametro 'macchina' dell'operazione {}, ".format(self.id))

    def __str__(self):
        return "O_{} (d={}, j={}, M={})".format(self.id, self.durata, self.job_id, self.macchina.id)

    def get_successori(self, operazioni, by_durate=False):
        if by_durate:
            l = [o.durata for o in get_ops_by_jobid(self.job_id, operazioni) if o.id > self.id]
        else:
            l = [o for o in get_ops_by_jobid(self.job_id, operazioni) if o.id > self.id]
        
        return l


class Macchina:
    '''
        Risorse condivise su cui si deve decidere lo scheduling delle operazioni
        Attributi:
        - id della macchina, colore
        - coda_da_processare, lista di operazioni che sono assegnate a questa macchina
        - in_esecuzione, oggetto di tipo Operazione, che sta eseguendo sulla macchina self, 
        se None vuol dire che la macchina è occupata
    '''

    def __init__(self, id, coda_da_processare=[]):
        self.id = id
        self.coda_da_processare = coda_da_processare

    def __str__(self):
        return "Macchina: {}, Coda da processare: {}".format(self.id, self.coda_da_processare)


class Tabu:
    def __init__(self, dim, max_iter, stallo):
        ''' 
            Per la tabu search mi serve una coda di mosse tabu, quindi essa sarà una lista di coppie, 
            poi come iperparametro ne decido la dimensione e il numero massimo di iterazioni 
            per definire il criterio di stop della search 
        '''

        self.tabulist = []

        self.dim = dim
        self.max_iter = max_iter
        self.stallo = stallo



def print_soluzione(soluzione):
    ''' stampo la struttura dati che contiene la soluzione parziale corrente '''

    if verbose: 
        for i in range(len(soluzione)):
            print("M{}: ".format(i+1), end="")
            print([op.id for op in soluzione[i]])


def print_groundset(groundset):
    ''' stampo la lista delle code di processamento con le macchine divise per job di appartenenza'''

    if verbose: 
        print("Code di processamento")
        for m in range(len(groundset)):
            print("M{}: ".format(m+1), end="")
            job = groundset[m]
            for j in range(len(job)):
                print("{}".format([op.id for op in job[j]]), end=", ")
            print()   


def print_lista_soluzioni(soluzioni):
    ''' stampo lista dei valori di f.o. delle soluzioni trovate attraverso Soluzione.find_greedy_solution() '''

    print("Lista delle soluzioni trovate")
    for i in range(len(soluzioni)):
        best = min(soluzioni[i], key=lambda s: s.makespan)
        print("Start {}:".format(i+1), [s.makespan for s in soluzioni[i]], BgColors.OKGREEN+"best = {}".format(best.makespan)+BgColors.ENDC)
    

def get_ops_by_jobid(job_id, operazioni):
    ''' seleziono le operazioni dato job_id in input ''' 

    return [o for o in operazioni if o.job_id == job_id]


def build_groundset(jobs, macchine):
    '''
        crea una struttura dati che contiene, per ogni macchina, la lista delle operazioni da processare, 
        divise per job di appartenenza, in cui c'è:
        - una lista per macchina,
        - per ciascuna di liste, una lista per ogni job con cui suddividere le operazioni della coda
        - e ciascuna lista job contiene le operazioni che lo compongono, da eseguire su quella macchina
    '''

    ground_set = [[] for m in macchine] # una riga per macchina
    for m in range(len(macchine)): # ciascuna contenente una riga per ogni job
        ground_set[m] = [[] for j in jobs] # una lista per ogni job
        for j in range(len(ground_set[m])):
            ground_set[m][j] = [op for op in macchine[m].coda_da_processare if op.job_id == j+1]
    return ground_set


def build_collections(n, m, macchine_associate, durate_ops):
    ''' 
        instanzio gli oggetti con i valori degli input:
        1) creo lista di oggetti di tipo Macchina
        2) creo lista di tipo Operazioni
        3) creo lista di oggetti di tipo Job, contenente oggetti Operazioni
    '''

    jobs = []
    operazioni = []
    if verbose:
        print("Sono stati creati i seguenti oggetti:")

    # creo la lista delle macchine
    macchine = [Macchina(id=id+1) for id in range(m)]
    
    index = 0
    for j in range(n): # per ogni job
        # creo e aggiungo le operazioni di questo job
        num_ops = len(macchine_associate[j]) # lunghezza riga j
        for i in range(num_ops): # per ogni operazione del job j
            macchina_id = macchine_associate[j][i]
            durata = durate_ops[j][i]
            
            # creo nuovo oggetto Operazione
            nuova_operazione = Operazione(
                id=index+1, 
                durata=durata, 
                job_id=j+1, 
                macchina=macchine[macchina_id]
            )
            operazioni.append(nuova_operazione) # riempio lista di tutte operazioni
            if verbose:
                print(nuova_operazione.__str__())
            index += 1           

    for m in macchine:
        m.coda_da_processare = [o for o in operazioni if o.macchina.id == m.id]

    # assegno le operazioni alla lista dei job
    for j in range(n):
        ops = get_ops_by_jobid(j+1, operazioni)
        nuovo_job = Job(id=j+1, lista_operazioni=ops)
        jobs.append(nuovo_job)
    
    if verbose: print();
    return jobs, operazioni, macchine


def inv(mossa):
    return (mossa[1], mossa[0])


def stop_conditions(ground_set):
    ''' 
        L'algoritmo iterativo termina quando ho analizzato ogni elemento del grounset, 
        quindi quindi quando ho schedulato tutte le operazioni 
    '''

    empty = True
    for lista_jobs in ground_set:
        for job in lista_jobs:
            if job != []:
                empty = False
                break
    return empty


def heuristic_sort(operazioni, tutte_ops):
    ''' ordino una lista di operazioni in base ad un criterio euristico sulla durata dell'operazione '''

    if euristica == "LPT":
        sorted_ops = sorted(operazioni, reverse=True, key=lambda o: o.durata)

    elif euristica == "SPT":
        sorted_ops = sorted(operazioni, reverse=False, key=lambda o: o.durata)

    elif euristica == "MIS": # maggior numero di successori, conto i successori
        mapp = {o:o.get_successori(tutte_ops) for o in operazioni}
        sorted_map = sorted(mapp.items(), reverse=True, key=lambda el: len(el))
        sorted_ops = [op for (op, _) in sorted_map]

    elif euristica == "MWKR": # maggior quantità di tempo-lavoro rimanente dopo il completamento, sommo le durate
        mapp = [(o, sum(o.get_successori(tutte_ops, by_durate=True))) for o in operazioni]
        sorted_map = sorted(mapp, reverse=True, key=lambda el: el[1])
        sorted_ops = [op for (op, _) in sorted_map]

    return sorted_ops


def prune_ops(jobs):
    ''' 
        elimino da una lista di operazioni quelle che sono sicuro a priori 
        andranno a rendere inammissibile la soluzione parziale , violando vincoli di precedenza
    ''' 

    return [job[0] for job in jobs if job != []]


def is_secure(ground_set, op):
    ''' 
        quando seleziono un'operazione da inserire in soluzione, mi vado ad accertare che non ci siano altre 
        operazioni dello stesso job di quella scelta, che debbano ancora essere assegnate. 
        In questo modo mi assicuro che man mano che la soluzione di allarga, questa rimanga ammissibile 
        e non violi vincoli di precedenza. In caso contrario semplicemente ripesco un'altra operazione, 
        e itero il ragionamento
    '''

    tutte = []
    for m in range(len(ground_set)):
        if m != op.macchina.id-1:
            lista_ops = get_ops_by_jobid(op.job_id, ground_set[m][op.job_id-1]) 
            tutte += lista_ops    

    if tutte != []:
        ordinata = sorted(tutte, key=lambda o: o.id)
        return False if ordinata[0].id < op.id else True 
    else:
        return True


def build_graph(jobs, operazioni):
    ''' creo grafo delle dipendenze, data la lista di job e delle operazioni '''

    n_operazioni = len(operazioni)
    g = DiGraph(directed=True)

    # creo innanzitutto i nodi
    g.add_nodes_from("st")
    g.add_nodes_from([i+1 for i in range(n_operazioni)])
    for i in range(n_operazioni):
        g.nodes[i+1]['su_macchina'] = operazioni[i].macchina.id
        g.nodes[i+1]
    assert g.number_of_nodes() == n_operazioni+2

    # poi gli archi
    for job in jobs:
        ops = job.lista_operazioni
        g.add_edge('s', ops[0].id, weight=0) # gli archi uscenti da s hanno peso zero
        g.add_edge(ops[-1].id, 't', weight=ops[-1].durata)
        for i in range(len(ops)-1):
            g.add_edge(ops[i].id, ops[i+1].id, weight=ops[i].durata)
    return g


def update_grafo(grafo, soluzione):
    ''' Aggiungo gli archi al grafo  '''
    
    for m in range(len(soluzione)):
        edges = [[soluzione[m][i], soluzione[m][i+1]] for i in range(len(soluzione[m])-1)]
        for e in edges:
            grafo.add_edge(e[0].id, e[1].id, weight=e[0].durata)
    return grafo


def in_stallo(l_sols, search):
    l = l_sols[-search.stallo:]
    return all(l[i].makespan <= l[i+1].makespan for i in range(len(l)-1))


def halt(l_sols, k, search):
    ''' condizione di stop: max_iter o stallo (massimo numero di iterazioni in cui non migliora la soluzione) '''
    
    if len(l_sols) > search.stallo + 1:
        return k >= search.max_iter or in_stallo(l_sols, search)
    else:
        return k >= search.max_iter


def find_best(p, search, start_i):
    s = p.lista_soluzioni[start_i]

    k = 0
    s.append(p.find_greedy_solution())
    best = s[k]
    if verbose:
        print(BgColors.OKBLUE+"Soluzione di partenza")
        print_soluzione(s[k].soluzione)
        print("Costo: {}".format(s[k].makespan))
        print("\nTabu list: {}\n".format(search.tabulist)+BgColors.ENDC)

    while not halt(p.lista_soluzioni[start_i], k, search):

        if verbose:
            print(u'\u2500' * 100)
            print("Iterazione", k+1)
        
        lista_ordinata = s[k].esplora_intorno()
        if verbose:
            print("Lista delle mosse possibili:", [(a,b)for (_, (a,b)) in lista_ordinata])

        flag_loop = 0
        n_mosse = len(lista_ordinata)
        for i in range(n_mosse):
            flag_loop += 1

            curr = lista_ordinata[i][0]
            mossa = lista_ordinata[i][1]

            if verbose:
                print("Estraggo S_curr, con mossa {}:".format(mossa))
                print_soluzione(curr.soluzione)
                print("Costo: {}\n".format(curr.makespan))
            
            # criterio di aspirazione
            if verbose:
                print("Test su criterio di attivazione...")
            if curr.getobjval() < best.getobjval(): # se la corrente è migliore dell'ottimo candidato
                if verbose:
                    print(BgColors.OKGREEN+"Successo! La soluzione S_curr diventa ottimo candidato! f(S_curr) < f(S_best)\nMi sposto su questa nuova soluzione\n"+BgColors.ENDC)
                best = curr                         # aggiorno l'ottimo candidato
                s.append(curr)                      # e mi sposto su questa soluzione
                k += 1
                # esco dal ciclo perchè ho trovato una soluzione migliore dell'ottimo candidato
                # su cui mi sposto con sicurezza     
                break
            else:
                if verbose:
                    print(BgColors.FAIL+"Fallito. La soluzione S_curr non è migliore dell'ottimo candidato\n"+BgColors.ENDC)
            
            if verbose:
                print("Stato della Tabulist: {}".format(search.tabulist))
            if mossa not in search.tabulist:
                if verbose:
                    print(BgColors.OKGREEN+"La mossa {} NON è vietata dalla tabulist\nPosso spostarmi sulla soluzione generata da {}".format(mossa, mossa)+BgColors.ENDC)
                s.append(curr)
                if verbose:
                    print("Aggiungo {} nella tabulist".format(inv(mossa)))
                search.tabulist.append(inv(mossa))
                if len(search.tabulist) > search.dim:
                    forgotten = search.tabulist.pop(0)
                    if verbose:
                        print("Cancello dalla tabulist la mossa {}".format(forgotten))
                k += 1
                # posso eseguire la mossa perchè non è vietata, altrimenti di nuovo avrei dovuto 
                # iterare per provare la prossima soluzione trovata dalla best
                break
            else:
                if verbose:
                    print("Non posso eseguire la mossa {} perché è vietata dalla tabulist\n".format(mossa))
            
            # controllo se ho terminato di le possibli mosse dell'intorno corrente
            if flag_loop >= n_mosse:
                if verbose:
                    print(BgColors.FAIL+"Termino la ricerca. Non posso scegliere nessuna mossa dell'intorno"+BgColors.ENDC)
                return best
                
            if verbose:
                print(BgColors.FAIL + "Seleziono la prossima soluzione utile\n"+BgColors.ENDC)

        
        if verbose:
            print("Tabulist aggiornata: {}\n".format(search.tabulist))

    return best

    
class Problema:
    ''' Istanza del problema, memorizza lista delle soluzioni trovate '''

    def __init__(self, n, m, macchine_associate, durate_ops, multistart):
        ''' prendo in input l'istanza del problema, istanzio le strutture dati e il grafo iniziale senza archi disgiuntivi '''

        self.lista_soluzioni = [[] for _ in range(multistart)]
        self.jobs, self.operazioni, self.macchine = build_collections(n, m, macchine_associate, durate_ops)
        self.grafo_iniziale = build_graph(self.jobs, self.operazioni)


    def find_greedy_solution(self):
        ''' algoritmo greedy non esatto per la ricerca di una soluzione ammissibile del problema '''

        ground_set = build_groundset(self.jobs, deepcopy(self.macchine))
        soluzione_parziale = [[] for i in self.macchine]
        
        k = 0
        print_groundset(ground_set)
        if verbose:
            print("S_{}".format(k))
        print_soluzione(soluzione_parziale); 
        if verbose: print()

        while not stop_conditions(ground_set):
            if verbose:
                print(u'\u2501' * 100)
                print("Iterazione k={}\n".format(k+1))

            for m_index in range(len(ground_set)):
                possibili_operazioni = prune_ops(ground_set[m_index])
                possibili_operazioni_ordinate = heuristic_sort(operazioni=possibili_operazioni, tutte_ops=self.operazioni)
                if possibili_operazioni_ordinate != []:
                    if verbose:
                        print("Seleziono per M{} con euristica {} tra le seguenti: {}".format(m_index+1, euristica, ["{}(d={})".format(op.id, op.durata) for op in possibili_operazioni_ordinate]))
                
                for z in range(len(possibili_operazioni_ordinate)):
                    
                    # controllo se posso scegliere effettivamente questa operazione per mantenere l'ammissibilità futura
                    chosen = possibili_operazioni_ordinate[z]
                    if verbose:
                        print("provo {}".format(chosen.id))
                    if is_secure(ground_set, chosen):
                        soluzione_parziale[m_index].append(chosen)
                        if verbose:
                            print(BgColors.OKGREEN+"Aggiungo l'operazione {} su M{}".format(chosen.id, m_index+1))
                            print(BgColors.ENDC)
                        # a questo punto posso eliminare dal groundset l'operazione che ho appena deciso di inserire in soluzione
                        ground_set[m_index][chosen.job_id-1].remove(chosen)
                        
                        # e ora posso uscire dal ciclo perchè ho scelto l'operazione da inserire
                        break
                    else:
                        if verbose:
                            print(BgColors.FAIL+"Rifiuto di aggiungere l'operazione {} in M{} perchè mi porterrebbe all'ammissibilità".format(chosen.id, m_index+1))
                            print(BgColors.ENDC)

            k += 1
            print_groundset(ground_set)
            if verbose:
                print("S_{}".format(k))
            print_soluzione(soluzione_parziale)
        
        s = Soluzione(problema=self, soluzione=soluzione_parziale, grafo=deepcopy(self.grafo_iniziale))
        if verbose:
            print(u'\u2501' * 100)
            print("Euristica: {}".format(euristica))
            print(s.__str__())
        
        return s


class Soluzione: 
    '''
        Oggetto Soluzione contiene informazioni su:
        - Valore F.O. Min makespan
        - cammino critico, cammino di costo massimo nel grafo delle dipendenze
        - grafo delle dipendenze diretto aciclico, in cui gli archi rappresentano le dipendenze già note a priori, vincoli tecnici
            - per ogni job, le sue operazioni vanno eseguite in sequenza in ordine di definizione
            - per ogni macchina, invece, l'ordine con cui si eseguono le operazioni associate è da decidere
    '''

    def __init__(self, problema, soluzione, grafo):
        ''' Della soluzione mi salvo in più anche il puntatore all'istanza Problema '''

        self.problema = problema
        self.soluzione = soluzione
        self.grafo = update_grafo(grafo, soluzione)
        self.cammino_critico = dag_longest_path(self.grafo, default_weight=0)
        self.makespan = dag_longest_path_length(self.grafo, default_weight=0)

    
    def __str__(self):
        return "CAMMINO CRITICO\t{}\nCOSTO\t\t{}".format(self.cammino_critico[1:-1], self.makespan)


    def getobjval(self):
        return dag_longest_path_length(self.grafo, default_weight=0)


    def is_ammissibile(self):
        ''' Ritorna vero se il grafo delle dipendenze è aciclico '''

        try: 
            find_cycle(self.grafo, orientation="original")
            f = False
        except NetworkXNoCycle:
            f = True

        return f


    def crea_intorno(self):
        '''  
            calcolo tutte le possibili mosse di swap che compongono l'intorno, 
            che consistono nello scambiare due operazioni adiacenti che stanno ad una delle due 
            estremità di un blocco. Un blocco è una sottosequenza del cammino critico, 
            le cui operazioni sono eseguite tutte nella stessa macchina
            
        '''
        
        lista_blocchi = {}
        cammino = self.cammino_critico[1:-1]
        id_blocco = 1
        lista_blocchi[id_blocco] = [cammino[0]]
        for i in range(len(cammino)-1):
            if self.problema.operazioni[cammino[i]-1].macchina.id == self.problema.operazioni[cammino[i+1]-1].macchina.id:
                lista_blocchi[id_blocco].append(cammino[i+1]) # sono dello stesso blocco
            else: # non sono dello stesso blocco, ne creo uno per metterci il secondo elemento
                id_blocco += 1
                lista_blocchi[id_blocco] = [cammino[i+1]]
        lista_blocchi = list(lista_blocchi.items())

        mosse = []
        for i in range(len(lista_blocchi)):
            blocco = lista_blocchi[i][1]
            dim = len(blocco)
            if dim == 2:
                mosse.append(tuple(blocco))
            elif dim > 2:
                mosse.append(tuple(blocco[:2]))
                mosse.append(tuple(blocco[-2:]))

        return mosse


    def esplora_intorno(self):
        ''' 
            Partendo dalla SOLUZIONE CORRENTE, effettuo un'esplorazione esaustiva dell'intorno,
            attraverso un passo di Very Large Neighborhood Search. Le mosse possibili che costituiscono l'intorno sono
            in numero polinomiale, dipendono infatti dalla lunghezza del cammino critico
        '''
        
        lista_valutazioni = []
        lista_mosse = self.crea_intorno()
                
        # scorro la lista delle mosse possibili per l'intorno corrente e ne valuto il valore della funzione obiettivo
        for i in range(len(lista_mosse)):

            x_k = deepcopy(self)

            # ad ogni iterazione il grafo si ripristina allo stato iniziale  
            x_k.grafo = deepcopy(x_k.problema.grafo_iniziale)

            target = lista_mosse[i]
            m_index = self.problema.operazioni[target[0]-1].macchina.id
            
            # faccio swap
            lista_ops = x_k.soluzione[m_index-1]
            for index in range(len(lista_ops)):
                if lista_ops[index].id == target[0]:
                    i = index
                if lista_ops[index].id == target[1]:
                    j = index

            park = lista_ops[i]
            lista_ops[i] = lista_ops[j]
            lista_ops[j] = park

            # ne aggiorno i vari attributi e controllo l'ammissibilità di questa nuova soluzione
            x_k.grafo = update_grafo(grafo=x_k.grafo, soluzione=x_k.soluzione)
            if x_k.is_ammissibile():
                x_k.cammino_critico = dag_longest_path(x_k.grafo, default_weight=0)
                x_k.makespan = dag_longest_path_length(x_k.grafo, default_weight=0)

                lista_valutazioni.append((x_k, target))

        # ora ho una lista di soluzioni calcolate visitando l'intorno partendo dalla quella corrente
        lista_ordinata_fo = sorted(lista_valutazioni, key=lambda t: dag_longest_path_length(t[0].grafo, default_weight=0))

        return lista_ordinata_fo



if __name__ == "__main__":
    parser = ArgumentParser(description='Il programma risolve il problema del Job Shop Scheduling utilizzando la TabuSearch partendo da una soluzione iniziale calcolata con un algoritmo euristico costruttivo Greedy')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="""Verbose, se è True mostra tutti i dettagli della computazione dell'algoritmo a schermo, 
                        altrimenti se False mostra solo la soluzione finale calcolata""")

    parser.add_argument('-i', '--istanza', default="toy", type=str, choices=["toy", "10x10x10"],
                        help="""Scelta dell'istanza da dare in input tra le possibili, cioè [toy, 10x10x10].""")
    parser.add_argument('-m', '--multistart', default=1, type=int,
                        help="""Definisco il numero di soluzioni di partenza, in modo da appplicare la tabu search partendo da ciascuna di esse. 
                        Se ha valore 0, l'algoritmo esegue un single-start per ciascuna delle possibili euristiche: LPT, SPT, MIS, MWKR""")
    parser.add_argument('-e', '--euristica', default="auto", type=str, choices=["LPT", "SPT", "MIS", "MWKR", "auto"],
                        help="""Euritica di selezione per l'algoritmo greedy, le possibili opzioni sono LPT, SPT, MIS, MWKR, auto. 
                        Se 'auto' (default = auto) allora viene scelta casualmente dall'algoritmo ad ogni iterazione.""")

    parser.add_argument('-t', '--tabu_search', action='store_true', default=False,
                        help="""Se True, decido di utilizzare la tabu search per migliorare la soluzione iniziale ottenuta dall'algoritmo euristico greedy,
                        altrimenti calcolo solamente la soluzione ottenuta dall'algoritmo greedy.""")

    parser.add_argument('-d', '--tabu_list_dim', default=2, type=int,
                        help="""Iperparametro per la tabu search: dimesione della tabu list. 
                        (default = 2).""")
    parser.add_argument('-x', '--max_iter', default=5, type=int,
                        help="""Iperparametro per la tabu search: massimo numero di iterazioni per far terminare la tabu search. 
                        (default = 5).""")
    parser.add_argument('-s', '--stallo', default=3, type=int,
                        help="""Iperparametro per la tabu search: massimo numero di iterazioni in cui la soluzione non 
                        migliora durante la search oltre il quale l'algoritmo termina. 
                        (default = 3).""")

    args = parser.parse_args()

    # arguments parser VARIABILI GLOBALI
    istanza = args.istanza
    verbose = args.verbose
    multistart = args.multistart
    euristica = args.euristica
    tabu_search = args.tabu_search
    tabu_list_dim = args.tabu_list_dim
    max_iter = args.max_iter
    stallo = args.stallo

    opts = ("LPT", "SPT", "MIS", "MWKR")
    if euristica == "auto":
        euristica = choice(opts)

    if not tabu_search:
        p = Problema(*read_input(istanza), multistart=1)
        best = p.find_greedy_solution()

        if not verbose:
            print_soluzione(best.soluzione)
            print("Euristica: {}".format(euristica))
            print(best.__str__())

    else:
        num_starts = multistart if multistart > 0 else len(opts)
        p = Problema(*read_input(istanza), multistart=num_starts)

        for start_i in range(num_starts):

            if multistart == 0:
                euristica = opts[start_i]

            tabusearch = Tabu(dim=tabu_list_dim, max_iter=max_iter, stallo=stallo)
            best = find_best(p, tabusearch, start_i)

            if verbose:
                print(u'\u2501' * 100)
                print(u'\u2501' * 100)
                print("Miglior soluzione trovata start {}/{}".format(start_i+1, num_starts))
                print_soluzione(best.soluzione)
                if multistart == 0:
                    print("Euristica: {}".format(euristica))
                print(best.__str__(), "\n")
            
        print_lista_soluzioni(p.lista_soluzioni)