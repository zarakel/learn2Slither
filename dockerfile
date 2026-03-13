# Utiliser une image Python officielle légère
FROM python:3.11-slim

# Empêche Python de créer des fichiers .pyc et force l'affichage immédiat dans le terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installation des dépendances systèmes nécessaires pour Pygame (SDL)
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances Python en premier (pour utiliser le cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY . .

# Commande par défaut (sera souvent surchargée par le Makefile)
CMD ["python", "main.py"]