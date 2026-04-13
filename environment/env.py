import gymnasium as gym
from gymnasium import spaces
import numpy as np
from collections import deque
from environment.board import Board, Action, Cell

# Valeurs numériques pour le réseau de neurones
NUM_MAPPING = {
    Cell.EMPTY.value: 0,
    Cell.WALL.value: 1,
    Cell.BODY.value: 2,
    Cell.GREEN.value: 3,
    Cell.RED.value: 4,
    Cell.HEAD.value: 5 # Utilisé uniquement pour l'affichage terminal
}

class Learn2SlitherEnv(gym.Env):
    """Interpréteur : Pont entre la physique du jeu et l'Agent IA."""
    
    metadata = {"render_modes": ["ansi", "human"]}

    def __init__(self, board_size: int = 10, max_board_size: int = 40):
        super().__init__()
        self.board_size = board_size
        self.max_board_size = max_board_size
        
        self.board = Board(size=self.board_size)
        
        # Actions : 4 (Haut, Droite, Bas, Gauche)
        self.action_space = spaces.Discrete(4)
        
        # Frame Stacking : On conserve les 4 dernières visions en mémoire
        self.num_frames = 4
        self.frames = deque(maxlen=self.num_frames)
        
        # Observation : 4 directions * 4 features * num_frames
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, 
            shape=(4 * 4 * self.num_frames,), 
            dtype=np.float32 
        )
        
        # Pour stocker la vision sous forme de chaîne (pour le rendu terminal)
        self.current_vision_dict = {}

    def reset(self, seed=None, options=None):
        """Réinitialise l'environnement pour une nouvelle session."""
        super().reset(seed=seed)
        self.board.reset()
        self.steps_without_green = 0
        
        base_obs = self._extract_state()
        for _ in range(self.num_frames):
            self.frames.append(base_obs)
            
        stacked_obs = np.concatenate(self.frames).astype(np.float32)
        return stacked_obs, {}

    def step(self, action: int):
        """Exécute une action et renvoie (Observation, Récompense, Terminé, Tronqué, Info)."""

        is_dead, ate_green, ate_red = self.board.move(action)
        self.steps_without_green += 1
        
        # 1. Calcul des récompenses
        reward = -0.1 # Pénalité de temps pour le forcer à explorer rapidement

        # Pénalité sévère si le serpent tourne en rond trop longtemps
        max_steps_allowed = max(200, 100 * len(self.board.snake))
        if self.steps_without_green > max_steps_allowed and not is_dead:
            is_dead = True
            reward = -10.0 # Pénalité de boucle infinie
            
        if is_dead and self.steps_without_green <= max_steps_allowed:
            # Pénalité fixe pour la mort
            reward = -15.0
        elif ate_green:
            reward = 10.0
            self.steps_without_green = 0
        elif ate_red:
            reward = -10.0

        # 2. Extraction du nouvel état combiné
        new_obs = self._extract_state()
        self.frames.append(new_obs)
        stacked_obs = np.concatenate(self.frames).astype(np.float32)
        
        # Terminated = Game Over physique
        # Truncated = Limite de temps arbitraire (optionnel, on le met à False)
        return stacked_obs, reward, is_dead, False, {}

    def _extract_state(self) -> np.ndarray:
        """
        Génère la vision en croix depuis la tête du serpent de façon agnostique à la taille du plateau.
        Pour chaque direction : [1/dist_mur, 1/dist_corps, 1/dist_pomme_v, 1/dist_pomme_r]
        Si non présent dans la ligne de vue, la valeur est 0.0.
        """
        if len(self.board.snake) == 0:
            return np.zeros((16,), dtype=np.float32)

        head_x, head_y = self.board.snake[0]
        
        # Ordre strict : Haut, Bas, Gauche, Droite
        directions = {
            'UP': (0, -1),
            'DOWN': (0, 1),
            'LEFT': (-1, 0),
            'RIGHT': (1, 0)
        }
        
        vision_features = []
        self.current_vision_dict = {dir_name: [] for dir_name in directions}

        for dir_name, (dx, dy) in directions.items():
            cx, cy = head_x + dx, head_y + dy
            dist = 1
            
            dist_wall = -1.0
            dist_body = 0.0
            dist_green = 0.0
            dist_red = 0.0
            
            # On avance dans la direction jusqu'à toucher un mur
            while 0 <= cx < self.board.size and 0 <= cy < self.board.size:
                cell_val = self.board.get_cell_type(cx, cy)
                self.current_vision_dict[dir_name].append(cell_val)
                
                if cell_val == Cell.BODY.value and dist_body == 0.0:
                    dist_body = dist
                elif cell_val == Cell.GREEN.value and dist_green == 0.0:
                    dist_green = dist
                elif cell_val == Cell.RED.value and dist_red == 0.0:
                    dist_red = dist
                    
                cx += dx
                cy += dy
                dist += 1
                
            dist_wall = dist  # Le mur est juste après la dernière case valide
            self.current_vision_dict[dir_name].append(Cell.WALL.value)
            
            # Normalisation inverse : 1.0 (très proche) -> 0.0 (très loin)
            fv_wall = 1.0 / dist_wall
            fv_body = 1.0 / dist_body if dist_body > 0 else 0.0
            fv_green = 1.0 / dist_green if dist_green > 0 else 0.0
            fv_red = 1.0 / dist_red if dist_red > 0 else 0.0
            
            vision_features.extend([fv_wall, fv_body, fv_green, fv_red])

        return np.array(vision_features, dtype=np.float32)

    def render(self):
        """Affiche la vision sous la forme de croix demandée par le sujet."""
        if not self.current_vision_dict:
            return
            
        print("\n--- VISION DU SERPENT ---")
        
        # On calcule d'abord la ligne horizontale pour connaître le décalage
        left_str = "".join(reversed(self.current_vision_dict['LEFT']))
        right_str = "".join(self.current_vision_dict['RIGHT'])
        
        # Le secret est là : on crée un espacement dynamique !
        offset_spaces = " " * len(left_str)
        
        # Affichage Haut
        for char in reversed(self.current_vision_dict['UP']):
            print(f"{offset_spaces}{char}")
            
        # Affichage Gauche + Tête + Droite
        print(f"{left_str}H{right_str}")
        
        # Affichage Bas
        for char in self.current_vision_dict['DOWN']:
            print(f"{offset_spaces}{char}")
            
        print("-------------------------\n")