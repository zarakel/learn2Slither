import argparse
import os
import time
import pygame
from environment.env import Learn2SlitherEnv
from environment.board import Cell
from agent.dqn_agent import DQNAgent

# --- Paramètres d'affichage Pygame ---
CELL_SIZE = 40
COLORS = {
    'BG': (240, 240, 240),
    'GRID': (200, 200, 200),
    Cell.GREEN.value: (0, 255, 0),     # Pomme Verte
    Cell.RED.value: (255, 0, 0),       # Pomme Rouge
    Cell.BODY.value: (0, 0, 255),      # Corps du Serpent Bleu
    Cell.HEAD.value: (0, 0, 200)       # Tête légèrement plus sombre
}

def draw_board(screen, env: Learn2SlitherEnv):
    """Dessine la grille et les éléments avec Pygame."""
    screen.fill(COLORS['BG'])
    board_size = env.board_size

    # Dessiner la grille
    for x in range(board_size):
        for y in range(board_size):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, COLORS['GRID'], rect, 1)
            
            # Récupérer le type de la cellule et la colorier
            cell_type = env.board.get_cell_type(x, y)
            if cell_type in COLORS:
                pygame.draw.rect(screen, COLORS[cell_type], rect)

    pygame.display.flip()

def parse_args():
    """Gère les arguments de la ligne de commande selon le sujet."""
    parser = argparse.ArgumentParser(description="Learn2Slither - RL Snake")
    parser.add_argument('-sessions', type=int, default=1, help="Nombre de sessions d'entraînement")
    parser.add_argument('-save', type=str, default=None, help="Chemin pour sauvegarder le modèle")
    parser.add_argument('-visual', choices=['on', 'off'], default='off', help="Activer l'affichage")
    parser.add_argument('-dontlearn', action='store_true', help="Désactiver l'apprentissage")
    parser.add_argument('-step-by-step', action='store_true', help="Attendre une touche entre chaque action")
    parser.add_argument('load_cmd', nargs='?', default=None, help="Mot-clé 'load'")
    parser.add_argument('load_path', nargs='?', default=None, help="Chemin du modèle à charger")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Initialisation de l'environnement et de l'Agent
    board_size = 10
    env = Learn2SlitherEnv(board_size=board_size, max_board_size=40)
    
    # input_dim = 4 directions * 4 caractéristiques * 4 frames = 64
    input_dim = env.observation_space.shape[0]
    output_dim = env.action_space.n # 4 actions
    
    agent = DQNAgent(input_dim=input_dim, output_dim=output_dim)

    # Chargement d'un modèle existant si demandé
    if args.load_cmd == 'load' and args.load_path:
        if os.path.exists(args.load_path):
            agent.load_model(args.load_path)
            print(f"Load trained model from {args.load_path}")
        else:
            print(f"Erreur : Le fichier {args.load_path} n'existe pas.")
            return

    # Configuration Pygame si le visuel est activé
    screen = None
    if args.visual == 'on':
        pygame.init()
        screen = pygame.display.set_mode((board_size * CELL_SIZE, board_size * CELL_SIZE))
        pygame.display.set_caption("Learn2Slither - Snake Game")

    global_max_length = 0
    global_max_duration = 0

    # --- BOUCLE PRINCIPALE DES SESSIONS ---
    for session in range(1, args.sessions + 1):
        state, _ = env.reset()
        is_dead = False
        duration = 0
        
        while not is_dead:
            # Gestion des événements Pygame (pour pouvoir fermer la fenêtre)
            if args.visual == 'on':
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                        
            # 1. L'agent choisit une action
            # On calcule un "boost d'exploration" très léger pour débloquer les boucles infinies 
            # (seulement si le serpent stagne vraiment, et max +10% pour éviter qu'il ne se suicide au hasard)
            steps = env.steps_without_green if hasattr(env, 'steps_without_green') else 0

            action = agent.select_action(state, learn_mode=not args.dontlearn, frustration_boost=0.0)
            
            # 2. L'environnement exécute l'action
            next_state, reward, is_dead, _, _ = env.step(action)
            duration += 1
            
            # 3. Apprentissage (Seulement si on n'a pas le flag -dontlearn)
            if not args.dontlearn:
                # L'agent mémorise cette expérience
                agent.memory.push(state, action, reward, next_state, is_dead)
                
                # Apprentissage
                if len(agent.memory) > agent.batch_size:
                    agent.optimize_model()
            
            state = next_state

            # 4. Affichage Pygame
            if args.visual == 'on':
                draw_board(screen, env)
                if args.step_by_step:
                    # Attendre que l'utilisateur appuie sur Espace pour avancer 
                    wait = True
                    while wait:
                        for event in pygame.event.get():
                            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                                wait = False
                            elif event.type == pygame.QUIT:
                                pygame.quit()
                                return
                else:
                    time.sleep(0.1) # Vitesse d'affichage lisible pour un humain 

        # Fin de la session : Statistiques et mise à jour
        current_length = len(env.board.snake)
        if current_length > global_max_length:
            global_max_length = current_length
        if duration > global_max_duration:
            global_max_duration = duration

        if not args.dontlearn:
            agent.decay_epsilon()
            # Mettre à jour le Target Net à la fin de chaque session (ou toutes les X steps)
            agent.update_target_network()

    # --- FIN DE L'ENTRAÎNEMENT ---
    print(f"Game over, max length = {global_max_length} max duration = {global_max_duration}")

    # Sauvegarde du modèle
    if args.save:
        # Créer le dossier models/ s'il n'existe pas
        os.makedirs(os.path.dirname(args.save), exist_ok=True)
        agent.save_model(args.save)
        print(f"Save learning state in {args.save}")

    if args.visual == 'on':
        pygame.quit()

if __name__ == "__main__":
    main()