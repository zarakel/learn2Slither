import argparse
import os
import time
import pygame
from environment.env import Learn2SlitherEnv
from environment.board import Cell
from agent.dqn_agent import DQNAgent
from graphic.display import NokiaUI


def parse_args():
    parser = argparse.ArgumentParser(description="Learn2Slither - RL Snake")
    parser.add_argument('-sessions',    type=int, default=100)
    parser.add_argument('-board_size',  type=int, default=10)
    parser.add_argument('-save',        type=str, default=None)
    parser.add_argument('-visual',      choices=['on', 'off'], default='on')
    parser.add_argument('-dontlearn',   action='store_true')
    parser.add_argument('-step-by-step',action='store_true', dest='step_by_step')
    parser.add_argument('load_cmd',     nargs='?', default=None)
    parser.add_argument('load_path',    nargs='?', default=None)
    return parser.parse_args()


def main():
    args = parse_args()

    # --- UI ---
    ui = NokiaUI(board_size=args.board_size)
    ui.sessions      = args.sessions
    ui.board_size    = args.board_size
    ui.visual_on     = (args.visual == 'on')
    ui.learn_on      = not args.dontlearn
    ui.step_by_step  = args.step_by_step
    ui.save_path     = args.save or ""
    ui.init()

    global_max_length   = 0
    global_max_duration = 0

    # --- OUTER LOOP : handles reset to lobby ---
    while True:
        # --- LOBBY: wait until player launches ---
        if ui.visual_on:
            quit_requested = False
            while ui.screen not in ('game', 'results'):
                quit_requested = ui.draw()
                if quit_requested:
                    ui.quit()
                    return
                ui.tick(30)
            # Re-read config the player may have changed via UI
            board_size = ui.board_size
            sessions   = ui.sessions
        else:
            board_size = ui.board_size
            sessions   = ui.sessions
            ui.go_game()

        # --- Environment & Agent ---
        env = Learn2SlitherEnv(board_size=board_size, max_board_size=40)
        input_dim  = env.observation_space.shape[0]
        output_dim = env.action_space.n
        agent = DQNAgent(input_dim=input_dim, output_dim=output_dim)

        if args.load_cmd == 'load' and args.load_path and os.path.exists(args.load_path):
            agent.load_model(args.load_path)
            print(f"Loaded model from {args.load_path}")

        session_interrupted = False

        # --- MAIN TRAINING LOOP ---
        for session in range(1, sessions + 1):
            if session_interrupted:
                break

            state, _ = env.reset()
            is_dead  = False
            duration = 0
            start_time = time.time()

            while not is_dead:
                # draw / event handling
                if ui.visual_on:
                    ui.current_session  = session
                    ui.current_length   = len(env.board.snake)
                    ui.current_epsilon  = agent.epsilon
                    ui.current_score    = len(env.board.snake) - 3  # rough score
                    ui.current_duration = int(time.time() - start_time)

                    quit_req = ui.draw(env)
                    if quit_req:
                        ui.quit()
                        return

                    # Check if user pressed ESC to return to lobby
                    if ui.screen == 'lobby':
                        session_interrupted = True
                        break

                # action
                action = agent.select_action(state, learn_mode=not args.dontlearn,
                                            frustration_boost=0.0)

                next_state, reward, is_dead, _, _ = env.step(action)
                duration += 1

                # learning
                if not args.dontlearn:
                    agent.memory.push(state, action, reward, next_state, is_dead)
                    if len(agent.memory) > agent.batch_size:
                        agent.optimize_model()

                state = next_state

                if ui.visual_on:
                    if ui.step_by_step:
                        if ui.wait_step():
                            ui.quit()
                            return
                        if ui.screen == 'lobby':
                            session_interrupted = True
                            break
                    else:
                        ui.tick(10)

            if session_interrupted:
                break

            # --- end of session ---
            current_length = len(env.board.snake)
            if current_length > global_max_length:
                global_max_length = current_length
            if duration > global_max_duration:
                global_max_duration = duration

            if not args.dontlearn:
                agent.decay_epsilon()
                agent.update_target_network()

            ui.record_session(session, current_length, int(time.time() - start_time), agent.epsilon)

        if session_interrupted:
            ui.reset()
            continue  # go back to lobby loop

        # show results screen after last session
        if not session_interrupted and ui.visual_on:
            ui.go_results()
            waiting = True
            while waiting and ui.screen == 'results':
                quit_req = ui.draw()
                if quit_req:
                    ui.quit()
                    return
                ui.tick(30)
            ui.reset()
            continue

        if not ui.visual_on:
            break

    # --- done ---
    print(f"Game over — max length = {global_max_length}  max duration = {global_max_duration}")

    if args.save:
        os.makedirs(os.path.dirname(args.save) or '.', exist_ok=True)
        agent.save_model(args.save)
        print(f"Model saved to {args.save}")

    ui.quit()


if __name__ == "__main__":
    main()
