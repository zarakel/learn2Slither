import torch
import torch.nn as nn
import torch.nn.functional as F

class DQN(nn.Module):
    """
    Deep Q-Network : Le réseau de neurones qui évalue la qualité des actions.
    Hérite de nn.Module, la brique de base de PyTorch.
    """
    
    def __init__(self, input_dim: int, output_dim: int):
        """
        Initialise l'architecture du réseau.
        :param input_dim: La taille du vecteur d'observation (ex: 160)
        :param output_dim: Le nombre d'actions possibles (ex: 4)
        """
        super(DQN, self).__init__()
        
        # Première couche cachée : prend l'entrée et l'envoie vers 128 neurones
        self.fc1 = nn.Linear(input_dim, 128)
        
        # Deuxième couche cachée : 128 neurones vers 128 neurones
        self.fc2 = nn.Linear(128, 128)
        
        # Couche de sortie : 128 neurones vers nos 4 actions
        self.output = nn.Linear(128, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        La "passe avant" (forward pass) : comment les données traversent le réseau.
        Cette fonction est appelée automatiquement quand on fait : dqn_model(etat)
        """
        # On passe les données dans la 1ère couche, puis on applique ReLU
        x = F.relu(self.fc1(x))
        
        # On passe dans la 2ème couche, puis on applique ReLU
        x = F.relu(self.fc2(x))
        
        # On passe dans la couche de sortie. 
        # ATTENTION : Pas de ReLU ici ! Les Q-values peuvent être négatives 
        # (ex: une action qui mène à la mort aura une Q-value fortement négative).
        q_values = self.output(x)
        
        return q_values