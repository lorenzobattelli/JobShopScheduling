from utils import *
from istanza import read_input

if __name__ == "__main__":

    p = Problema(*read_input())
    p.find_greedy_solution()
    
    print("\nRICERCA LOCALE\n")
    search = Tabu(dim=2, max_iter=5)

    x_0 = p.get_current_sol() # soluzione di partenza ottenuta dalla greedy
    
    x_k, mossa = x_0.find_best()

    # da implementare l'algortimo della tabu search qui sotto, 
    # vedi schema foglio
    
    
    

