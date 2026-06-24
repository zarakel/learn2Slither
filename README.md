# Learn2Slither : Apprentissage par Renforcement Profond (Snake IA)

*Un agent autonome entraîné via Double Deep Q-Networks (DDQN) sur un environnement personnalisé sous contraintes de vision strictes.*

---

## Présentation & Points Forts du Projet

Ce projet dépasse le cadre d'un simple jeu Snake pour devenir une **vitrine technique d'ingénierie en IA (Reinforcement Learning)**. Face à des contraintes de vision et de ressources, des solutions élégantes ont été implémentées pour permettre à un réseau de neurones d'acquérir des réflexes de survie complexes.

* **Robustesse de la Modélisation (Gymnasium)** : Customisation complète de l'API Gymnasium pour la simulation physique du plateau, permettant à l'agent d'apprendre sur n'importe quelle taille de carte (de 10x10 à 40x40).
* **Vision Relative Continue & Temporelle** : Le serpent perçoit les distances inverses de son environnement (Murs, Corps, Pomme Verte, Pomme Rouge) dans 4 directions, éliminant tout biais de coordonnées absolues. L'empilement temporel (Frame Stacking des 4 dernières frames) permet de surmonter la perte de dynamique temporelle (POMDP).
* **Stabilité d'Apprentissage par Double DQN** : Résolution du problème de surestimation des Q-Values (biais classique du DQN) par l'utilisation de deux réseaux de neurones synchronisés (Policy et Target Network).
* **Interface Rétro Immersive & Débogage** : Une interface graphique nostalgique de type Nokia 3310 codée sous Pygame, incluant une police de caractères matricielle (bitmap) personnalisée et un outil de débogage pas-à-pas de l'agent.

---

## Techniques & Compétences Acquises

La réalisation de ce projet a permis de maîtriser les concepts clés de l'Intelligence Artificielle moderne et de l'ingénierie logicielle :

* **Deep Reinforcement Learning (DRL)** : Conception et réglage d'algorithmes de Q-Learning profond, gestion de la mémoire de rejeu (*Replay Buffer*), et équilibrage Exploration/Exploitation (*Epsilon-greedy decay*).
* **Reward Engineering** : Conception d'une fonction de récompense efficace (pénalité de temps à chaque pas, punition de boucle infinie, etc.) pour guider l'apprentissage vers des comportements optimaux et robustes.
* **Deep Learning avec PyTorch** : Création de réseaux de neurones MLP (Multi-Layer Perceptron), gestion de l'inférence en temps réel et de la rétropropagation (optimiseur Adam, MSE Loss).
* **Conteneurisation (Docker & Docker Compose)** : Isolation totale de l'environnement d'exécution, gestion du partage du serveur X11 local pour afficher l'interface Pygame depuis un conteneur, et entraînement en mode *headless* (sans interface graphique) pour démultiplier la vitesse d'apprentissage.
* **Tests unitaires et simulations physiques** : Développement de bancs d'essais interactifs pour isoler le moteur du jeu de l'apprentissage machine.

---

## Commandes Importantes

*Entraîner le Cerveau (1000 sessions, mode rapide) :*
```bash
docker compose run --rm agent python main.py -sessions 1000 -save models/1000sess.pth -visual off
```

*Voir l'agent jouer (sans explorer aléatoirement) :*
```bash
docker compose run --rm agent python main.py -visual on load models/1000sess.pth -sessions 5 -dontlearn
```

*Personnaliser la taille du plateau de jeu (ex: une grande carte de 20x20) :*
```bash
docker compose run --rm agent python main.py -board_size 20 -sessions 500 -visual off
```

*Débogage visuel pas-à-pas (met le jeu en pause après chaque action, idéal pour analyser les décisions de l'agent) :*
```bash
docker compose run --rm agent python main.py -visual on -step-by-step load models/1000sess.pth
```

---

## Architecture & Détails de l'Apprentissage

### 1. Le Cerveau : Double Deep Q-Network (DDQN)
Plutôt qu'un simple Q-Learning (impossible avec un grand nombre d'états) ou un DQN classique, nous utilisons un **Double-DQN (DDQN)**.
- **Le Problème du DQN classique** : Il a tendance à surestimer les Q-Values (la récompense attendue), ce qui pousse le serpent à prendre des décisions trop optimistes et à foncer dans les murs en pensant survivre.
- **La Solution DDQN** : Nous utilisons deux réseaux de neurones. Le `Policy Network` choisit la meilleure action, et le `Target Network` (mis à jour plus lentement) évalue la valeur de cette action. Cela stabilise considérablement l'apprentissage mathématique.

### 2. La Vision du Serpent : Représentation Continue (L'Astuce Principale)
Le sujet imposait une contrainte majeure : **Le serpent ne peut voir qu'en ligne droite dans 4 directions (Haut, Bas, Gauche, Droite)**. Interdiction de lui donner les coordonnées absolues (X, Y) sous peine d'un malus de -42 points.

- **L'Ancienne tentative (Catégorielle)** : Au début, le serpent voyait des "blocs" (ex: [Mur, Vide, Pomme]). Mais un réseau de neurones a beaucoup de mal à déduire des distances à partir de listes variables d'objets ou d'identifiants (Embeddings).
- **Le Game Changer (Distance Inverse)** : Nous avons transformé sa vision en **valeurs continues normalisées (Float32 entre 0.0 et 1.0)**. 
  Pour chaque direction, l'agent calcule `1.0 / distance` jusqu'au prochain :
  1. `Mur`
  2. `Corps (Queue)`
  3. `Pomme Verte`
  4. `Pomme Rouge`
  
  *Pourquoi 1/distance ?* Si une pomme est à 1 case, la valeur est `1.0` (signal très fort). Si elle est à 10 cases, la valeur est `0.1`. Si l'objet n'existe pas dans cette direction, la valeur est `0.0`. Le réseau comprend désormais intuitivement la notion de **proximité et de danger immédiat**.

### 3. La Mémoire à Court-Terme (Frame Stacking)
Le jeu de Snake est un **POMDP** (Partially Observable Markov Decision Process). Si l'on donne au serpent uniquement l'image de l'instant T, il ne peut pas savoir s'il monte ou s'il descend (il ne connaît pas sa direction actuelle).
- **Technique** : Nous empilons les **4 dernières frames** (visions) du serpent.
- **Résultat** : L'état d'entrée n'est plus de 16 valeurs (4 directions × 4 caractéristiques), mais de **64 valeurs**. Le réseau de neurones peut déduire le mouvement (la dynamique) à partir de la différence entre ces 4 images temporelles.

### 4. Architecture du Réseau de Neurones (MLP)
Suite à l'abandon de la vision catégorielle, nous avons supprimé la couche `nn.Embedding` (qui ralentissait le CPU et n'était plus adaptée).
- **Entrée** : `nn.Linear(64, 256)` (Prend les 64 floats de distance inverse spatio-temporelle).
- **Couches cachées** : 256 -> 128 -> 64 (avec des activations `ReLU` pour la non-linéarité).
- **Sortie** : `nn.Linear(64, 4)` (Prédit la valeur des 4 actions : Haut, Bas, Gauche, Droite).
Cette structure 100% linéaire ("Fully Connected") est extrêmement rapide à calculer sur CPU, ce qui a permis de contourner les limitations de GPU physique indisponible.

### 5. Le Système de Récompenses
Pour guider le serpent sans le perturber :
- `+10.0` : Manger une pomme verte (objectif principal).
- `-15.0` : Mourir classiquement (mur, propre queue).
- `-10.0` : Manger une pomme rouge ou tourner en boucle infinie (timeout).
- `-0.1` : Pénalité de temps à chaque pas pour forcer à agir vite et ne pas se perdre.
- **L'Astuce d'Apprentissage** : Nous avons retiré les micro-récompenses continues (ex: "se rapprocher de la pomme donne +0.01"). Bien que tentantes, ces récompenses "denses" créent du bruit et poussent souvent l'agent à tourner en rond pour accumuler des micro-points au lieu de manger la pomme.

### 6. Infrastructure & Docker (Contournement Hardware)
Le développement sous GUI Linux / VirtualBox empêchait l'accès natif à l'accélération X11 (interface graphique) et au GPU (Nvidia) depuis Docker.
- **Solution d'entraînement** : Entraînement en mode `headless` (sans interface visuelle) via l'argument `-visual off`. Pygame est désactivé en fond de tâche, ce qui multiplie la vitesse d'apprentissage de l'agent par 100.
- **Solution de débogage visuel** : Ouverture du serveur graphique X11 à Docker localement via `xhost +local:docker`, permettant d'évaluer le modèle `.pth` avec l'argument `-visual on`.
