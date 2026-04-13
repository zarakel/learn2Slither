# Learn2Slither : Architecture & Techniques d'Apprentissage par Renforcement

Ce projet implémente un agent d'Intelligence Artificielle (Deep Reinforcement Learning) capable d'apprendre à jouer au jeu Snake par lui-même, tout en respectant des contraintes strictes (vision en croix uniquement).

---

## 1. Le Cerveau : Double Deep Q-Network (DDQN)
Plutôt qu'un simple Q-Learning (impossible avec un grand nombre d'états) ou un DQN classique, nous utilisons un **Double-DQN (DDQN)**.
- **Le Problème du DQN classique** : Il a tendance à surestimer les Q-Values (la récompense attendue), ce qui pousse le serpent à prendre des décisions trop optimistes et à foncer dans les murs en pensant survivre.
- **La Solution DDQN** : Nous utilisons deux réseaux de neurones. Le `Policy Network` choisit la meilleure action, et le `Target Network` (mis à jour plus lentement) évalue la valeur de cette action. Cela stabilise considérablement l'apprentissage mathématique.

## 2. La Vision du Serpent : Représentation Continue (L'Astuce Principale)
Le sujet imposait une contrainte majeure : **Le serpent ne peut voir qu'en ligne droite dans 4 directions (Haut, Bas, Gauche, Droite)**. Interdiction de lui donner les coordonnées absolues (X, Y) sous peine d'un malus de -42 points.

- **L'Ancienne tentative (Catégorielle)** : Au début, le serpent voyait des "blocs" (ex: [Mur, Vide, Pomme]). Mais un réseau de neurones a beaucoup de mal à déduire des distances à partir de listes variables d'objets ou d'identifiants (Embeddings).
- **Le Game Changer (Distance Inverse)** : Nous avons transformé sa vision en **valeurs continues normalisées (Float32 entre 0.0 et 1.0)**. 
  Pour chaque direction, l'agent calcule `1.0 / distance` jusqu'au prochain :
  1. `Mur`
  2. `Corps (Queue)`
  3. `Pomme Verte`
  4. `Pomme Rouge`
  
  *Pourquoi 1/distance ?* Si une pomme est à 1 case, la valeur est `1.0` (signal très fort). Si elle est à 10 cases, la valeur est `0.1`. Si l'objet n'existe pas dans cette direction, la valeur est `0.0`. Le réseau comprend désormais intuitivement la notion de **proximité et de danger immédiat**.

## 3. La Mémoire à Court-Terme : Le Frame Stacking
Le jeu de Snake est un **POMDP** (Partially Observable Markov Decision Process). Si l'on donne au serpent uniquement l'image de l'instant T, il ne peut pas savoir s'il monte ou s'il descend (il ne connaît pas sa vitesse/direction actuelle).
- **Technique** : Nous empilons les **4 dernières frames** (visions) du serpent.
- **Résultat** : L'état d'entrée n'est plus de 16 valeurs (4 directions × 4 caractéristiques), mais de **64 valeurs**. Le réseau de neurones peut déduire le mouvement (la dynamique) à partir de la différence entre ces 4 images temporelles.

## 4. Architecture du Réseau de Neurones (MLP)
Suite à l'abandon de la vision catégorielle, nous avons supprimé la couche `nn.Embedding` (qui ralentissait le CPU et n'était plus adaptée).
- **Entrée** : `nn.Linear(64, 256)` (Prend les 64 floats de distance inverse spatio-temporelle).
- **Couches cachées** : 256 -> 128 -> 64 (avec des activations `ReLU` pour la non-linéarité).
- **Sortie** : `nn.Linear(64, 4)` (Prédit la valeur des 4 actions : Haut, Bas, Gauche, Droite).
Cette structure 100% linéaire ("Fully Connected") est extrêmement rapide à calculer sur CPU, ce qui a permis de contourner les limitations de GPU physique indisponible.

## 5. Le Système de Récompenses (Reward Shaping)
Pour guider le serpent sans le perturber :
- `+10.0` : Manger une pomme verte (objectif principal).
- `-15.0` : Mourir classiquement (mur, propre queue).
- `-10.0` : Manger une pomme rouge ou tourner en boucle infinie (timeout).
- `-0.1` : Pénalité de temps à chaque pas pour forcer à agir vite et ne pas se perdre.
- **L'Astuce d'Apprentissage** : Nous avons retiré les micro-récompenses continues (ex: "se rapprocher de la pomme donne +0.01"). Bien que tentantes, ces récompenses "denses" créent du bruit et poussent souvent l'agent à tourner en rond pour accumuler des micro-points au lieu de manger la pomme.

## 6. Infrastructure & Docker (Contournement Hardware)
Le développement sous GUI Linux / VirtualBox empêchait l'accès natif à l'accélération X11 (interface graphique) et au GPU (Nvidia) depuis Docker.
- **Solution d'entraînement** : Entraînement en mode `headless` (sans interface visuelle) via l'argument `-visual off`. Pygame est désactivé en fond de tâche, ce qui multiplie la vitesse d'apprentissage de l'agent par 100.
- **Solution de débogage visuel** : Ouverture du serveur graphique X11 à Docker localement via `xhost +local:docker`, permettant d'évaluer le modèle `.pth` avec l'argument `-visual on`.

## Commandes Importantes

*Entraîner le Cerveau (1000 sessions, mode rapide) :*
`docker compose run --rm agent python main.py -sessions 1000 -save models/1000sess.pth -visual off`

*Voir l'agent jouer (sans explorer aléatoirement) :*
`docker compose run --rm agent python main.py -visual on load models/1000sess.pth -sessions 5 -dontlearn`

*Personnaliser la taille du plateau de jeu (ex: une grande carte de 20x20) :*
`docker compose run --rm agent python main.py -board_size 20 -sessions 500 -visual off`

*Débogage visuel pas-à-pas (met le jeu en pause après chaque action, idéal pour analyser les décisions de l'agent) :*
`docker compose run --rm agent python main.py -visual on -step-by-step load models/1000sess.pth`
