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
        states, actions, rewards, next_states, dones = zip(*random.sample(self.buffer, batch_size))
        return np.array(states), actions, rewards, np.array(next_states), dones

    def __len__(self):
        return len(self.buffer)

class DQNAgent:
    """L'Agent qui interagit avec l'environnement et apprend."""
    
    def __init__(self, input_dim: int, output_dim: int, lr: float = 1e-3, gamma: float = 0.99,
                 epsilon_start: float = 1.0, epsilon_end: float = 0.01, epsilon_decay: float = 0.995):
        self.output_dim = output_dim
        self.gamma = gamma # Importance des récompenses futures
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        
        # 1. Création des deux réseaux (Policy et Target)
        self.policy_net = DQN(input_dim, output_dim)
        self.target_net = DQN(input_dim, output_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval() # Le Target net ne s'entraîne pas directement
        
        # 2. L'optimiseur (celui qui modifie les poids du réseau)
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.loss_fn = nn.MSELoss() # Erreur quadratique moyenne
        
        # 3. La mémoire
        self.memory = ReplayBuffer(capacity=10000)
        self.batch_size = 64

    def select_action(self, state: np.ndarray, learn_mode: bool = True) -> int:
        """
        Choisit une action. 
        Gère l'Exploration vs Exploitation si learn_mode est True.
        Permet l'exploitation pure (-dontlearn) si learn_mode est False .
        """
        if learn_mode and random.random() < self.epsilon:
            # EXPLORATION : Action au hasard
            return random.randrange(self.output_dim)
            
        # EXPLOITATION : On demande au réseau de neurones
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()

    def optimize_model(self):
        """La fonction Q-Learning : Met à jour le réseau de neurones."""
        if len(self.memory) < self.batch_size:
            return # Pas assez de souvenirs pour s'entraîner
            
        # 1. Récupérer un lot de souvenirs
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
        
        # Conversion en Tenseurs PyTorch
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions).unsqueeze(1)
        rewards = torch.FloatTensor(rewards).unsqueeze(1)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones).unsqueeze(1)
        
        # 2. Calculer les Q-values actuelles Q(S_t, A_t)
        current_q_values = self.policy_net(states).gather(1, actions)
        
        # 3. Calculer les Q-values cibles : R_{t+1} + gamma * max Q(S_{t+1}, a)
        with torch.no_grad():
            max_next_q_values = self.target_net(next_states).max(1)[0].unsqueeze(1)
            # Si le jeu est fini (done=1), il n'y a pas de récompense future
            target_q_values = rewards + (self.gamma * max_next_q_values * (1 - dones))
            
        # 4. Calcul de l'erreur (Loss) et rétropropagation (Apprentissage)
        loss = self.loss_fn(current_q_values, target_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def update_target_network(self):
        """Copie les poids du Policy Net vers le Target Net pour stabiliser l'apprentissage."""
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self):
        """Diminue la probabilité d'exploration à la fin de chaque session."""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def save_model(self, filepath: str):
        """Exporte le modèle dans un fichier [cite: 165-167, 193-194]."""
        torch.save(self.policy_net.state_dict(), filepath)

    def load_model(self, filepath: str):
        """Importe un modèle depuis un fichier [cite: 165-167, 206-207]."""
        self.policy_net.load_state_dict(torch.load(filepath))
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.epsilon = self.epsilon_end # On arrête d'explorer avec un modèle déjà entraîné