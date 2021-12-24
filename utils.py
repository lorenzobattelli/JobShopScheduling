from networkx import find_cycle, DiGraph
from networkx.algorithms import swap
from networkx.exception import NetworkXNoCycle
from networkx.algorithms.dag import dag_longest_path, dag_longest_path_length
from copy import deepcopy
from istanza import *
from random import choice



verbose = True

''' Classes '''
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
        Un job è formato da una lista di operazione da eseguire sulle macchine
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


class Problema:
    ''' Istanza del problema, memorizza lista delle soluzioni trovate '''

    def __init__(self, n, m, macchine_associate, durate_ops):
        ''' prendo in input l'istanza del problema, istanzio le strutture dati e il grafo iniziale senza archi disgiuntivi '''

        self.lista_soluzioni = []
        self.jobs, self.operazioni, self.macchine = build_collections(n, m, macchine_associate, durate_ops)
        self.grafo_iniziale = build_graph(self.jobs, self.operazioni)


    def find_greedy_solution(self, random=False):
        ''' algoritmo greedy non esatto per la ricerca di una soluzione ammissibile del problema '''

        ground_set = build_groundset(self.jobs, deepcopy(self.macchine))
        soluzione_parziale = [[] for i in self.macchine]
        
        k = 0
        print_groundset(ground_set)
        if verbose:
            print("S_{}".format(k))
        print_soluzione(soluzione_parziale); print()

        while not stop_conditions(ground_set):
            if verbose:
                print(u'\u2501' * 100)
                print("Iterazione k={}\n".format(k))

            for m_index in range(len(ground_set)):
                possibili_operazioni = prune_ops(ground_set[m_index])
                possibili_operazioni_ordinate, euristica = heuristic_sort(possibili_operazioni, self.operazioni, random_heuristic=random)
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
        if s.is_ammissibile():
            if verbose:
                print(u'\u2501' * 100)
                print(s.__str__())
                print(u'\u2501' * 100)
                print(u'\u2501' * 100)
                print()
            return s
        else:
            del s
            raise Exception("Errore: la soluzione NON è ammissibile\nCammino critico\t{}\nCosto\t\t{}".format(s.cammino_critico, s.makespan))


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
        self.makespan = self.getobjval()
        self.lista_blocchi = self.split_in_blocchi(self.problema.operazioni)

    
    def __str__(self):
        return "La soluzione è ammissibile\nCAMMINO CRITICO\t{}\nCOSTO\t\t{}\n".format(self.cammino_critico[1:-1], self.makespan)


    def getobjval(self):
        return dag_longest_path_length(self.grafo, default_weight=0)


    def split_in_blocchi(self, operazioni):
        ''' Creo e restituisco il dizionario dei blocchi trasformato in lista '''

        lista_blocchi = {}
        cammino = self.cammino_critico[1:-1]
        
        id_blocco = 1
        lista_blocchi[id_blocco] = [cammino[0]]

        for i in range(len(cammino)-1):
            if operazioni[cammino[i]-1].macchina.id == operazioni[cammino[i+1]-1].macchina.id:
                lista_blocchi[id_blocco].append(cammino[i+1]) # sono dello stesso blocco
            else: # non sono dello stesso blocco, ne creo uno per metterci il secondo elemento
                id_blocco += 1
                lista_blocchi[id_blocco] = [cammino[i+1]]

        return list(lista_blocchi.items())


    def is_ammissibile(self):
        ''' Ritorna vero se il grafo delle dipendenze è aciclico '''

        try: 
            find_cycle(self.grafo, orientation="original")
            f = False
        except NetworkXNoCycle:
            f = True

        return f


    def get_lista_mosse(self):
        '''  
            calcolo tutte le possibili mosse di swap che compongono l'intorno, 
            che consistono nello scambiare due operazioni adiacenti che stanno ad una delle due 
            estremità di un blocco. Un blocco è una sottosequenza del cammino critico, 
            le cui operazioni sono eseguite tutte nella stessa macchina
            
        '''
        mosse = []
        lista_blocchi = self.lista_blocchi
        for i in range(len(lista_blocchi)):
            blocco = lista_blocchi[i][1]
            dim = len(blocco)
            if dim == 2:
                mosse.append(tuple(blocco))
            elif dim > 2:
                mosse.append(tuple(blocco[:2]))
                mosse.append(tuple(blocco[-2:]))

        return mosse


    def find_best(self):
        ''' 
            Partendo dalla SOLUZIONE CORRENTE, effettuo un'esplorazione esaustiva dell'intorno,
            attraverso un passo di Very Large Neighborhood Search. Le mosse possibili che costituiscono l'intorno sono
            in numero polinomiale, infatti dalla lunghezza del cammino critico
        '''
        
        lista_valutazioni = []
        lista_mosse = self.get_lista_mosse()
                
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
                x_k.lista_blocchi = x_k.split_in_blocchi(self.problema.operazioni)

                lista_valutazioni.append((x_k, target))

        # ora ho una lista di soluzioni calcolate visitando l'intorno partendo dalla quella corrente
        lista_ordinata_fo = sorted(lista_valutazioni, key=lambda t: dag_longest_path_length(t[0].grafo, default_weight=0))

        return lista_ordinata_fo


class Tabu:
    def __init__(self, dim, max_iter):
        ''' 
            Per la tabu search mi serve una coda di mosse tabu, quindi essa sarà una lista di coppie, 
            poi come iperparametro ne decido la dimensione e il numero massimo di iterazioni 
            per definire il criterio di stop della search 
        '''

        self.tabulist = []
        self.dim = dim
        self.max_iter = max_iter


    def is_full(self):
        return len(self.tabulist) == self.dim


''' Utils functions '''
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


def heuristic_sort(operazioni, tutte_ops, random_heuristic=False):
    ''' ordino una lista di operazioni in base ad un criterio euristico sulla durata dell'operazione '''

    opts = ("LPT", "SPT", "MIS", "MWKR")
    if random_heuristic:
        euristica = choice(opts)
    else:
        euristica = opts[0]

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

    return sorted_ops, euristica


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

    all = []
    for m in range(len(ground_set)):
        if m != op.macchina.id-1:
            lista_ops = get_ops_by_jobid(op.job_id, ground_set[m][op.job_id-1]) 
            all += lista_ops    

    if all != []:
        ordinata = sorted(all, key=lambda o: o.id)
        return False if ordinata[0].id < op.id else True 
    else:
        return True


def halt(k, maxiter):
    return k >= maxiter


def inv(mossa):
    return (mossa[1], mossa[0])


def update_grafo(grafo, soluzione):
    ''' Aggiungo gli archi al grafo  '''
    
    for m in range(len(soluzione)):
        edges = [[soluzione[m][i], soluzione[m][i+1]] for i in range(len(soluzione[m])-1)]
        for e in edges:
            grafo.add_edge(e[0].id, e[1].id, weight=e[0].durata)
    return grafo


''' Print functions '''
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

    if verbose:
        print("Lista di tutte le soluzioni trovate\n{}".format([s.makespan for s in soluzioni]))