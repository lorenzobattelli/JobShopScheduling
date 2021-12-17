from utils import *
from istanza import read_input

if __name__ == "__main__":

    p = Problema(*read_input())
    p.find_greedy_solution()

    s = p.get_current_sol()


    print(s.calcola_mosse())


