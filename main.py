from utils import *
from istanza import read_input

if __name__ == "__main__":

    p = Problema(*read_input())
    search = Tabu(dim=2, max_iter=5)
    s = p.lista_soluzioni

    k = 0
    s.append(p.find_greedy_solution())
    best = s[k]
    if verbose:
        print(BgColors.OKBLUE+"Soluzione di partenza")
        print_soluzione(s[k].soluzione)
        print("Costo: {}".format(s[k].makespan))
        print("\nTabu list: {}\n".format(search.tabulist)+BgColors.ENDC)

    while not halt(k, search.max_iter):

        if verbose:
            print(u'\u2500' * 100)
            print("Iterazione", k+1)
        
        lista_ordinata = s[k].find_best()

        for i in range(len(lista_ordinata)):
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

            if verbose:
                print(BgColors.FAIL + "Seleziono la prossima soluzione utile\n"+BgColors.ENDC)


        if verbose:
            print("Tabulist aggiornata: {}\n".format(search.tabulist))
    
    print(u'\u2501' * 100)
    print(u'\u2501' * 100)
    print("Miglior soluzione trovata")
    print_soluzione(best.soluzione)
    print("Cammino critico: {}\nCosto: {}\n".format(best.cammino_critico[1:-1], best.makespan)) 
