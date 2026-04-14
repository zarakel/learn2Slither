# Nom du service dans le docker-compose
SERVICE = agent

all: build run

build:
	docker compose build

# Lance le programme principal (main.py)
train10:
	docker compose run --rm $(SERVICE) python main.py -sessions 10 -save models/10sess.pth -visual off

train100:
	docker compose run --rm $(SERVICE) python main.py -sessions 100 -save models/100sess.pth -visual off

train1000:
	docker compose run --rm $(SERVICE) python main.py -sessions 1000 -save models/1000sess.pth -visual off

eval10:
	docker compose run --rm $(SERVICE) python main.py -sessions 5 load models/10sess.pth -visual on -dontlearn

eval100:
	docker compose run --rm $(SERVICE) python main.py -sessions 5 load models/100sess.pth -visual on -dontlearn

eval1000:
	docker compose run --rm $(SERVICE) python main.py -sessions 5 load models/1000sess.pth -visual on -dontlearn

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