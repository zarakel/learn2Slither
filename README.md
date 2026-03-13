**Commandes d'Exécution (via Docker & Makefile)**

Le projet est entièrement conteneurisé pour éviter les problèmes de dépendances locales.

*1. Construire l'image Docker :*

   make build

*3. Entraîner un nouveau modèle (Mode invisible et rapide) :*
Exemple pour entraîner l'agent sur 1000 sessions et sauvegarder son cerveau:

    docker compose run --rm agent python main.py -sessions 1000 -save models/1000sess.txt -visual off

*4. Regarder l'agent jouer (Mode Exploitation) :*
Charge un modèle entraîné et désactive l'apprentissage aléatoire (-dontlearn) pour observer son intelligence pure:

    docker compose run --rm agent python main.py -visual on load models/1000sess.txt -sessions 5 -dontlearn

*5. Mode Pas-à-Pas (Debug) :*
Permet de valider les décisions de l'agent frame par frame (appuyez sur Espace pour avancer):

    docker compose run --rm agent python main.py -visual on load models/1000sess.txt -sessions 1 -dontlearn -step-by-step

***Learn2Slither - Reinforcement Learning***

Ce projet implémente un agent d'Intelligence Artificielle capable d'apprendre à jouer au jeu Snake par lui-même en utilisant l'Apprentissage par Renforcement (Reinforcement Learning).

Le Concept Principal : L'Apprentissage par Renforcement (RL)

L'Apprentissage par Renforcement est un paradigme où un agent intelligent apprend des stratégies de décision optimales en interagissant avec son environnement. Contrairement à la programmation classique, l'agent apprend par essais et erreurs.
À chaque action, l'environnement lui renvoie un retour sous forme de récompenses (manger une pomme verte) ou de punitions (heurter un mur, manger une pomme rouge). L'agent adapte ensuite son comportement pour maximiser ses récompenses sur le long terme.

*Les Q-Fonctions et le Deep Q-Learning*

Pour prendre ses décisions, l'agent utilise une Fonction Q (Quality function) qui évalue la pertinence d'une action donnée dans un état spécifique.

Plutôt que d'utiliser une simple "Q-Table" (qui deviendrait obsolète si la taille du plateau change), ce projet utilise le Deep Q-Learning (DQN).

    Le Modèle : Un réseau de neurones artificiels prend en entrée la "vision" du serpent (ce qu'il voit dans les 4 directions depuis sa tête ).

    La Sortie : Le réseau prédit 4 "Q-values" correspondant aux 4 actions possibles (Haut, Bas, Gauche, Droite).

    L'Apprentissage : Le réseau est mis à jour itérativement  grâce à l'équation de Bellman, en utilisant une mémoire des expériences passées (Replay Buffer) et un réseau cible (Target Network) pour stabiliser les mathématiques.

*Librairies Principales*

    gymnasium : Le standard de l'industrie pour les environnements RL. Il structure le code autour d'une boucle simple : l'agent envoie une action via la méthode env.step(action), et l'environnement retourne (observation, reward, terminated, truncated, info).

    PyTorch (torch) : Utilisé pour construire et entraîner le réseau de neurones (le cerveau de l'agent).

    pygame : Utilisé pour générer l'interface graphique du jeu et afficher le plateau, le serpent et les pommes en temps réel.

*Architecture des Modules*

Le code respecte une séparation stricte des responsabilités (Architecture Modulaire):

    environment/board.py (L'Environnement Physique) : Gère uniquement la logique du jeu sur une grille de 10x10. Il gère les déplacements, les collisions (murs, queue) , et l'apparition aléatoire des pommes (2 vertes, 1 rouge).

    environment/env.py (L'Interpréteur Gymnasium) : Fait le pont entre le jeu et l'IA. Il extrait la vision en forme de croix demandée (évitant ainsi la pénalité de -42 points) et calcule les récompenses numériques (Reward Shaping).

    agent/model.py (Le Cerveau / PyTorch) : Contient la définition de l'architecture du Perceptron Multicouche (MLP).

    agent/dqn_agent.py (L'Agent) : Gère la logique de choix d'action (balance entre Exploration et Exploitation)  et l'algorithme d'optimisation du réseau de neurones.

    main.py (Le Point d'Entrée) : Gère le parsing des arguments du terminal , la boucle des sessions de jeu , et le rendu graphique Pygame.
