# test_board.py
import os
from environment.board import Board, Action, Cell

def print_board(board: Board):
    """Affiche la grille dans le terminal de manière lisible."""
    # Efface la console (cls pour Windows, clear pour Linux/Mac)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"--- Learn2Slither - Test Physique ---")
    print(f"Taille du serpent : {len(board.snake)} | Game Over : {board.is_game_over}")
    print("-" * (board.size * 2 + 1))
    
    for y in range(board.size):
        row_str = "|"
        for x in range(board.size):
            cell_type = board.get_cell_type(x, y)
            
            # Un peu de formatage visuel pour le test humain
            if cell_type == Cell.EMPTY.value:
                row_str += " ."
            elif cell_type == Cell.HEAD.value:
                row_str += " H"
            elif cell_type == Cell.BODY.value:
                row_str += " s"
            elif cell_type == Cell.GREEN.value:
                row_str += " G"
            elif cell_type == Cell.RED.value:
                row_str += " R"
            else:
                row_str += f" {cell_type}"
        row_str += " |"
        print(row_str)
    print("-" * (board.size * 2 + 1))

def main():
    board = Board(size=10) # Grille de 10x10
    
    mapping_touches = {
        'w': Action.UP.value,
        's': Action.DOWN.value,
        'a': Action.LEFT.value,
        'd': Action.RIGHT.value
    }
    
    while not board.is_game_over:
        print_board(board)
        
        # Demande à l'utilisateur de jouer
        mouvement = input("Mouvement (w=Haut, s=Bas, a=Gauche, d=Droite, x=Quitter) : ").lower()
        
        if mouvement == 'x':
            print("Arrêt du test.")
            break
            
        if mouvement in mapping_touches:
            action = mapping_touches[mouvement]
            is_dead, ate_green, ate_red = board.move(action)
            
            if ate_green:
                print("🍎 MIAM ! Pomme verte mangée !")
            if ate_red:
                print("☠️ AIE ! Pomme rouge mangée, le serpent rétrécit !")
        else:
            print("Touche invalide.")
            
    if board.is_game_over:
        print_board(board)
        print("💥 GAME OVER ! (Mur, collision ou taille 0)")

if __name__ == "__main__":
    main()