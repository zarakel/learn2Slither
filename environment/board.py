import random
from collections import deque
from enum import Enum, unique
from typing import Tuple, List


@unique
class Action(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


@unique
class Cell(str, Enum):
    EMPTY = "0"
    WALL = "W"
    HEAD = "H"
    BODY = "S"
    GREEN = "G"
    RED = "R"


class Board:
    """Moteur physique."""

    def __init__(self, size: int = 10):
        self.size = size
        self.snake: deque[Tuple[int, int]] = deque()
        self.green_apples: List[Tuple[int, int]] = []
        self.red_apple: Tuple[int, int] = (-1, -1)
        self.is_game_over = False

        self.reset()

    def reset(self):
        """Réinitialise le plateau pour une nouvelle partie."""
        self.is_game_over = False
        self.snake.clear()

        # Le serpent commence avec une taille de 3, placé aléatoirement
        # Pour éviter de générer un serpent enfermé dès le départ,
        # on le place au centre, aligné horizontalement.
        center = self.size // 2
        self.snake.append((center, center))  # Tête
        self.snake.append((center - 1, center))  # Corps 1
        self.snake.append((center - 2, center))  # Queue

        self.green_apples = []
        # On place 2 pommes vertes et 1 rouge
        self._spawn_apple(Cell.GREEN)
        self._spawn_apple(Cell.GREEN)
        self._spawn_apple(Cell.RED)

    def _spawn_apple(self, apple_type: Cell):
        """Fait apparaître une pomme sur une case vide."""
        while True:
            # Génère des coordonnées aléatoires
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            pos = (x, y)

            # Vérifie que la case est vide (ni serpent, ni autre pomme)
            if (
                pos not in self.snake
                and pos not in self.green_apples
                and pos != self.red_apple
            ):
                if apple_type == Cell.GREEN:
                    self.green_apples.append(pos)
                elif apple_type == Cell.RED:
                    self.red_apple = pos
                break

    def move(self, action: int) -> Tuple[bool, bool, bool]:
        """
        Déplace le serpent selon l'action donnée.
        Retourne (is_dead, ate_green, ate_red) pour les récompenses.
        """
        if self.is_game_over:
            return True, False, False

        # 1. Calculer la nouvelle position de la tête
        head_x, head_y = self.snake[0]

        if action == Action.UP.value:
            new_head = (head_x, head_y - 1)
        elif action == Action.DOWN.value:
            new_head = (head_x, head_y + 1)
        elif action == Action.LEFT.value:
            new_head = (head_x - 1, head_y)
        elif action == Action.RIGHT.value:
            new_head = (head_x + 1, head_y)
        else:
            raise ValueError("Action invalide.")

        # 2. Vérifier les collisions fatales (Murs)
        if not (0 <= new_head[0] < self.size and 0 <= new_head[1] < self.size):
            self.is_game_over = True
            return True, False, False

        # 3. Vérifier la collision avec soi-même
        # Note: on ne vérifie pas la pointe de la queue car elle va bouger,
        # sauf si on mange une pomme qui nous fait grandir, mais on gère ça au
        # mouvement.
        if new_head in self.snake and new_head != self.snake[-1]:
            self.is_game_over = True
            return True, False, False

        # 4. Gérer le déplacement et l'ingestion
        self.snake.appendleft(new_head)  # Insère la nouvelle tête

        ate_green = False
        ate_red = False

        if new_head in self.green_apples:
            ate_green = True
            self.green_apples.remove(new_head)
            self._spawn_apple(Cell.GREEN)  # Nouvelle pomme
            # On ne "pop" pas la queue, ce qui fait grandir le serpent de 1
        elif new_head == self.red_apple:
            ate_red = True
            self.red_apple = (-1, -1)
            self._spawn_apple(Cell.RED)  # Nouvelle pomme
            self.snake.pop()  # On pop pour le mouvement normal
            if len(self.snake) > 0:
                self.snake.pop()  # Pop pour diminuer la taille
        else:
            # Déplacement normal : on enlève la queue
            self.snake.pop()

        # 5. Vérifier si la taille tombe à 0
        if len(self.snake) == 0:
            self.is_game_over = True
            return True, False, ate_red

        return False, ate_green, ate_red

    def get_cell_type(self, x: int, y: int) -> str:
        """Retourne le type de la cellule à (x, y) pour générer la vision."""
        # 1. Gestion des murs (hors limites)
        if not (0 <= x < self.size and 0 <= y < self.size):
            return Cell.WALL.value

        # 2. Gestion du serpent (seulement s'il n'a pas disparu !)
        if len(self.snake) > 0:
            if (x, y) == self.snake[0]:
                return Cell.HEAD.value
            if (x, y) in self.snake:
                return Cell.BODY.value

        # 3. Gestion des pommes et du vide
        if (x, y) in self.green_apples:
            return Cell.GREEN.value
        if (x, y) == self.red_apple:
            return Cell.RED.value

        return Cell.EMPTY.value
