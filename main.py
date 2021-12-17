from utils import *
from istanza import read_input

if __name__ == "__main__":

    p = Problema(*read_input())
    p.find_greedy_solution()
    s = p.get_current_sol()

    s_k = s.applica_mossa()

    # devo testare se questa s_k è ammissibile
    # ne aggiorno i vari attributi per completarne la modifica
    
    
    

    
