import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
from agent.model import DQN


class ReplayBuffer:
    """Mémoire de l'agent pour stocker ses expériences."""

    def __init__(self, capacity: int):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        """Ajoute un souvenir à la mémoire."""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int):
        """Tire un lot de souvenirs au hasard pour s'entraîner."""
        states, actions, rewards, next_states, dones = zip(
            *random.sample(self.buffer, batch_size)
        )
        return np.array(states), actions, rewards, np.array(next_states), dones

    def __len__(self):
        return len(self.buffer)


class DQNAgent:
    """L'Agent qui interagit avec l'environnement et apprend."""

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        lr: float = 1e-3,
        gamma: float = 0.95,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
    ):
        self.output_dim = output_dim
        self.gamma = gamma  # Importance des récompenses futures
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay

        # Configuration de l'appareil (GPU / CPU)
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # 1. Création des deux réseaux (Policy et Target)
        self.policy_net = DQN(input_dim, output_dim).to(self.device)
        self.target_net = DQN(input_dim, output_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # Le Target net ne s'entraîne pas directement

        # 2. L'optimiseur (celui qui modifie les poids du réseau)
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.loss_fn = nn.MSELoss()  # Erreur quadratique moyenne

        # 3. La mémoire
        self.memory = ReplayBuffer(capacity=100000)
        self.batch_size = 128

    def select_action(
        self,
        state: np.ndarray,
        learn_mode: bool = True,
        frustration_boost: float = 0.0,
    ) -> int:
        """
        Choisit une action.
        Gère l'Exploration vs Exploitation si learn_mode est True.
        """
        # Augmentation dynamique de l'exploration si le serpent tourne en
        # boucle
        current_epsilon = min(1.0, self.epsilon + frustration_boost)

        if learn_mode and random.random() < current_epsilon:
            # EXPLORATION : Action au hasard
            return random.randrange(self.output_dim)

        # EXPLOITATION : On demande au réseau de neurones
        with torch.no_grad():
            state_tensor = (
                torch.FloatTensor(state).unsqueeze(0).to(self.device)
            )
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()

    def optimize_model(self):
        """La fonction Q-Learning : Met à jour le réseau de neurones."""
        if len(self.memory) < self.batch_size:
            return  # Pas assez de souvenirs pour s'entraîner

        # 1. Récupérer un lot de souvenirs
        states, actions, rewards, next_states, dones = self.memory.sample(
            self.batch_size
        )

        # Conversion en Tenseurs PyTorch sur le bon Device (GPU/CPU)
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.device)

        # 2. Calculer les Q-values actuelles Q(S_t, A_t)
        current_q_values = self.policy_net(states).gather(1, actions)

        # 3. Calculer les Q-values cibles (DOUBLE DQN)
        with torch.no_grad():
            # a) Le Policy Net choisit la meilleure action pour l'état suivant
            best_next_actions = self.policy_net(next_states).argmax(
                dim=1, keepdim=True
            )
            # b) Le Target Net évalue la valeur de CETTE action (évite la
            # surestimation)
            next_q_values = self.target_net(next_states).gather(
                1, best_next_actions
            )

            # Si le jeu est fini (done=1), il n'y a pas de récompense future
            target_q_values = rewards + (
                self.gamma * next_q_values * (1 - dones)
            )

        # 4. Calcul de l'erreur (Loss) et rétropropagation (Apprentissage)
        loss = self.loss_fn(current_q_values, target_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def update_target_network(self):
        """Copie les poids du Policy Net vers le Target Net."""
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self):
        """Diminue la probabilité d'exploration à la fin de chaque session."""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def save_model(self, filepath: str):
        """Exporte le modèle avec ses métadonnées (checkpoint PyTorch)."""
        checkpoint = {
            "model_state_dict": self.policy_net.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
        }
        # Force l'extension .pth recommandée
        if not filepath.endswith(".pth") and not filepath.endswith(".pt"):
            filepath = filepath.rsplit(".", 1)[0] + ".pth"
        torch.save(checkpoint, filepath)

    def load_model(self, filepath: str):
        """Importe un modèle et ses métadonnées depuis un fichier."""
        checkpoint = torch.load(filepath, map_location=self.device)
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            self.policy_net.load_state_dict(checkpoint["model_state_dict"])
            if "optimizer_state_dict" in checkpoint:
                self.optimizer.load_state_dict(
                    checkpoint["optimizer_state_dict"]
                )
            self.epsilon = checkpoint.get("epsilon", self.epsilon_end)
        else:
            # Rétrocompatibilité avec les anciens fichiers .txt ou state_dicts
            # purs
            self.policy_net.load_state_dict(checkpoint)

        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
