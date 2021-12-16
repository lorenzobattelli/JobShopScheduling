from utils import *
from istanza import read_input

if __name__ == "__main__":

    p = Problema(*read_input())
    p.find_greedy_solution()
  
    s = p.get_current_sol()

    blocchi = s.split_in_blocchi(p.operazioni)

    for (key, value) in blocchi.items():
        print(key, value)