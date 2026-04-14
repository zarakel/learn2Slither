import torch
import torch.nn as nn
import torch.nn.functional as F


class DQN(nn.Module):
    """
    Deep Q-Network : Le réseau de neurones qui évalue la qualité des actions.
    Hérite de nn.Module, la brique de base de PyTorch.
    """

    def __init__(self, input_dim: int, output_dim: int):
        super(DQN, self).__init__()

        # Le state est maintenant un vecteur de valeurs numériques normalisées
        # entre 0 et 1 (pas besoin d'Embedding)
        self.fc1 = nn.Linear(input_dim, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 64)

        self.output = nn.Linear(64, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Aplatir les dimensions si le batch a des dimensions supplémentaires
        x = x.view(x.size(0), -1)

        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))

        q_values = self.output(x)
        return q_values
