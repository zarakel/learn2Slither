# Nom du service dans le docker-compose
SERVICE = agent

all: build run

build:
	docker compose build

# Lance le programme principal (main.py)
run:
	docker compose run --rm $(SERVICE) python main.py

# Règle sur mesure pour lancer notre test de la Brique 1
test_board:
	docker compose run --rm $(SERVICE) python test_board.py

test_env:
	docker compose run --rm $(SERVICE) python test_env.py

# Règle pour vérifier la norme du code python
norme:
	docker compose run --rm $(SERVICE) flake8 .

# Arrête les conteneurs
clean:
	docker compose down

# Arrête les conteneurs et supprime les images/volumes orphelins
fclean: clean
	docker system prune -af --volumes

# Reconstruit tout de zéro
re: fclean build

.PHONY: all build run test norme clean fclean re