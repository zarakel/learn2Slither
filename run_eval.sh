#!/bin/bash
echo "=== Running 10 sessions ==="
\docker compose run --rm agent python main.py -sessions 10 -visual off -save models/10sess.pth
echo "=== Running 100 sessions ==="
\docker compose run --rm agent python main.py -sessions 100 -visual off -save models/100sess.pth
echo "=== Running 300 sessions (for quick proxy of 1000) ==="
\docker compose run --rm agent python main.py -sessions 300 -visual off -save models/300sess.pth
