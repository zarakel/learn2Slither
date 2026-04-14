# test_env.py
import os
from environment.env import Learn2SlitherEnv
from environment.board import Action


def main():
    # On crée notre environnement (taille plateau 10x10, padding à 40)
    env = Learn2SlitherEnv(board_size=10, max_board_size=40)

    # reset() renvoie l'observation initiale et un dictionnaire d'infos
    obs, info = env.reset()

    mapping_touches = {
        "z": Action.UP.value,
        "s": Action.DOWN.value,
        "q": Action.LEFT.value,
        "d": Action.RIGHT.value,
    }

    is_dead = False

    while not is_dead:
        # Efface la console pour une animation fluide
        os.system("cls" if os.name == "nt" else "clear")

        # 1. On utilise le rendu de l'environnement pour afficher la vision en
        # croix
        env.render()

        # (Optionnel) Afficher ce que le réseau de neurones reçoit vraiment
        # print(f"Shape du vecteur Numpy : {obs.shape}")

        # 2. Saisie utilisateur
        mouvement = input("Action (z/q/s/d, x=Quitter) : ").lower()

        if mouvement == "x":
            break

        if mouvement in mapping_touches:
            action = mapping_touches[mouvement]

            # 3. La méthode magique de Gymnasium : step()
            # Elle renvoie 5 valeurs : observation, reward, terminated,
            # truncated, info
            obs, reward, is_dead, truncated, info = env.step(action)

            print(f"Récompense reçue pour cette action : {reward}")
            # Pause pour lire la récompense
            input("Appuyez sur Entrée pour continuer...")

        else:
            print("Touche invalide.")
            input("Appuyez sur Entrée...")

    if is_dead:
        os.system("cls" if os.name == "nt" else "clear")
        env.render()
        print("\n GAME OVER ! L'agent a reçu la récompense fatale : -15.0")


if __name__ == "__main__":
    main()
