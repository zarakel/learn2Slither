import gymnasium as gym
from gymnasium import spaces
import numpy as np
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
        self.max_board_size = max_board_size # Pour garantir la validation du Bonus
        
        self.board = Board(size=self.board_size)
        
        # Actions : 4 (Haut, Droite, Bas, Gauche)
        self.action_space = spaces.Discrete(4)
        
        # Observation : 4 directions * max_board_size (Taille fixe garantie)
        # On définit que les valeurs vont de 0 à 4
        self.observation_space = spaces.Box(
            low=0, high=4, 
            shape=(4 * self.max_board_size,), 
            dtype=np.float32 # float32 est plus standard pour PyTorch
        )
        
        # Pour stocker la vision sous forme de chaîne (pour le rendu terminal)
        self.current_vision_dict = {}

    def reset(self, seed=None, options=None):
        """Réinitialise l'environnement pour une nouvelle session."""
        super().reset(seed=seed)
        self.board.reset()
        
        observation = self._extract_state()
        return observation, {}

    def step(self, action: int):
        """Exécute une action et renvoie (Observation, Récompense, Terminé, Tronqué, Info)."""
        
        is_dead, ate_green, ate_red = self.board.move(action)
        
        # 1. Calcul des récompenses (Reward Shaping)
        reward = -0.1 # Pénalité de temps par défaut
        
        if is_dead:
            reward = -100.0
        elif ate_green:
            reward = 10.0
        elif ate_red:
            reward = -10.0

        # 2. Extraction du nouvel état
        observation = self._extract_state()
        
        # Terminated = Game Over physique
        # Truncated = Limite de temps arbitraire (optionnel, on le met à False)
        return observation, reward, is_dead, False, {}

    def _extract_state(self) -> np.ndarray:
        """
        Génère la vision en croix depuis la tête du serpent.
        C'est LA fonction qui évite la pénalité de -42 du sujet.
        """
        if len(self.board.snake) == 0:
            return np.zeros(self.observation_space.shape, dtype=np.float32)

        head_x, head_y = self.board.snake[0]
        
        # Ordre strict : Haut, Bas, Gauche, Droite
        directions = {
            'UP': (0, -1),
            'DOWN': (0, 1),
            'LEFT': (-1, 0),
            'RIGHT': (1, 0)
        }
        
        vision_array = []
        self.current_vision_dict = {dir_name: [] for dir_name in directions}

        for dir_name, (dx, dy) in directions.items():
            cx, cy = head_x + dx, head_y + dy
            ray_length = 0
            
            # On avance dans la direction jusqu'à toucher un mur
            while 0 <= cx < self.board.size and 0 <= cy < self.board.size:
                cell_val = self.board.get_cell_type(cx, cy)
                vision_array.append(NUM_MAPPING[cell_val])
                self.current_vision_dict[dir_name].append(cell_val)
                
                cx += dx
                cy += dy
                ray_length += 1
                
            # On a touché le mur (ou on est sorti). On ajoute le mur à la vision texte.
            self.current_vision_dict[dir_name].append(Cell.WALL.value)
            vision_array.append(NUM_MAPPING[Cell.WALL.value])
            ray_length += 1
            
            # PADDING : On remplit le reste avec des "Murs" jusqu'à max_board_size
            while ray_length < self.max_board_size:
                vision_array.append(NUM_MAPPING[Cell.WALL.value])
                ray_length += 1

        return np.array(vision_array, dtype=np.float32)

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