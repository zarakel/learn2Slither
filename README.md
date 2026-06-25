# Learn2Slither: Deep Reinforcement Learning (Snake AI)

*An autonomous agent trained via Double Deep Q-Networks (DDQN) on a custom environment under strict vision constraints.*

---

## Project Overview & Key Highlights

This project goes beyond a simple Snake game to serve as a **technical showcase of AI engineering (Reinforcement Learning)**. Faced with strict vision and resource constraints, elegant solutions were implemented to enable a neural network to acquire complex survival reflexes.

* **Robust Modeling (Gymnasium)**: Complete customization of the Gymnasium API for the physical simulation of the board, allowing the agent to learn on any map size (from 10x10 to 40x40).
* **Continuous & Temporal Relative Vision**: The snake perceives the inverse distances of its environment (Walls, Body, Green Apple, Red Apple) in 4 directions, eliminating any absolute coordinate bias. Temporal stacking (Frame Stacking of the last 4 frames) overcomes the loss of temporal dynamics.
* **Double DQN Learning Stability**: Solving the Q-Value overestimation problem (a classic DQN bias) by using two synchronized neural networks (Policy and Target Network).
* **Retro Immersive Interface & Debugging**: A nostalgic Nokia 3310-like graphical interface coded in Pygame, including a custom bitmap font and a step-by-step agent debugging tool.

---

## Techniques & Acquired Skills

Completing this project provided mastery of key modern Artificial Intelligence and software engineering concepts:

* **Deep Reinforcement Learning (DRL)**: Designing and tuning Deep Q-Learning algorithms, managing replay memory (*Replay Buffer*), and balancing Exploration/Exploitation (*Epsilon-greedy decay*).
* **Reward Engineering**: Designing an effective reward function (time penalty at each step, infinite loop punishment, etc.) to guide learning toward optimal and robust behaviors.
* **Deep Learning with PyTorch**: Creating MLP (Multi-Layer Perceptron) neural networks, managing real-time inference and backpropagation (Adam optimizer, MSE Loss).
* **Containerization (Docker & Docker Compose)**: Total isolation of the execution environment, managing the sharing of the local X11 server to display the Pygame interface from a container, and training in *headless* mode (without graphical interface) to multiply learning speed.
* **Unit Testing & Physical Simulations**: Developing interactive test benches to isolate the game engine from machine learning.

---

## Important Commands

*Train the Brain (1000 sessions, fast mode):*
```bash
docker compose run --rm agent python main.py -sessions 1000 -save models/1000sess.pth -visual off
```

*Watch the agent play (without random exploration):*
```bash
docker compose run --rm agent python main.py -visual on load models/1000sess.pth -sessions 5 -dontlearn
```

*Customize the board size (e.g., a large 20x20 map):*
```bash
docker compose run --rm agent python main.py -board_size 20 -sessions 500 -visual off
```

*Visual step-by-step debugging (pauses the game after each action, ideal for analyzing the agent's decisions):*
```bash
docker compose run --rm agent python main.py -visual on -step-by-step load models/1000sess.pth
```

---

## Architecture & Training Details

### 1. The Brain: Double Deep Q-Network (DDQN)
Rather than simple Q-Learning (impossible with a large number of states) or classic DQN, we use a **Double-DQN (DDQN)**.
- **The Classic DQN Problem**: It tends to overestimate Q-Values (the expected reward), which drives the snake to make overly optimistic decisions and crash into walls thinking it will survive.
- **The DDQN Solution**: We use two neural networks. The `Policy Network` selects the best action, and the `Target Network` (updated more slowly) evaluates the value of this action. This considerably stabilizes the mathematical learning process.

### 2. Snake's Vision: Continuous Representation (The Main Trick)
The subject imposed a major constraint: **The snake can only see in a straight line in 4 directions (Up, Down, Left, Right)**. Giving it absolute coordinates (X, Y) was forbidden, under penalty of a -42 point penalty.

- **The Previous Attempt (Categorical)**: Initially, the snake saw "blocks" (e.g., [Wall, Empty, Apple]). But a neural network struggles to deduce distances from variable lists of objects or identifiers (Embeddings).
- **The Game Changer (Inverse Distance)**: We transformed its vision into **normalized continuous values (Float32 between 0.0 and 1.0)**. 
  For each direction, the agent calculates `1.0 / distance` to the nearest:
  1. `Wall`
  2. `Body (Tail)`
  3. `Green Apple`
  4. `Red Apple`
  
  *Why 1/distance?* If an apple is 1 square away, the value is `1.0` (very strong signal). If it is 10 squares away, the value is `0.1`. If the object does not exist in that direction, the value is `0.0`. The network now intuitively understands the concept of **proximity and immediate danger**.

### 3. Short-Term Memory (Frame Stacking)
The Snake game is a **POMDP** (Partially Observable Markov Decision Process). If we only give the snake the image at time T, it cannot know if it is moving up or down (it does not know its current direction).
- **Technique**: We stack the **last 4 frames** (visions) of the snake.
- **Result**: The input state is no longer 16 values (4 directions × 4 features), but **64 values**. The neural network can deduce movement (dynamics) from the difference between these 4 temporal images.

### 4. Neural Network Architecture (MLP)
Following the abandonment of categorical vision, we removed the `nn.Embedding` layer (which slowed down the CPU and was no longer suitable).
- **Input**: `nn.Linear(64, 256)` (Takes the 64 spatio-temporal inverse distance floats).
- **Hidden Layers**: 256 -> 128 -> 64 (with `ReLU` activations for non-linearity).
- **Output**: `nn.Linear(64, 4)` (Predicts the value of the 4 actions: Up, Down, Left, Right).
This 100% linear ("Fully Connected") structure is extremely fast to compute on CPU, which allowed us to bypass the physical GPU limitations.

### 5. Reward System
To guide the snake without confusing it:
- `+10.0`: Eating a green apple (main objective).
- `-15.0`: Classic death (wall, own tail).
- `-10.0`: Eating a red apple or looping infinitely (timeout).
- `-0.1`: Time penalty at each step to force fast action and prevent getting lost.
- **The Learning Trick**: We removed continuous micro-rewards (e.g., "getting closer to the apple gives +0.01"). Although tempting, these "dense" rewards create noise and often lead the agent to run in circles to accumulate micro-points instead of eating the apple.

### 6. Infrastructure & Docker (Hardware Workaround)
Development under GUI Linux / VirtualBox prevented native access to X11 acceleration (graphical interface) and GPU (Nvidia) from Docker.
- **Training Solution**: Training in `headless` mode (without visual interface) via the `-visual off` argument. Pygame is disabled in the background, which multiplies the agent's learning speed by 100.
- **Visual Debugging Solution**: Opening the graphics server X11 to Docker locally via `xhost +local:docker`, allowing the evaluation of the `.pth` model with the `-visual on` argument.
