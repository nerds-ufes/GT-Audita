#!/bin/bash

SESSION="projeto-blockchain"

# Inicia nova sessão com um painel
tmux new-session -d -s $SESSION -n main

# Painel 0: Hardhat node
tmux send-keys -t $SESSION:0.0 'cd blockchain && docker compose up' C-m
sleep 15

# Split panels
tmux split-window -h -t $SESSION:0.0
tmux split-window -v -t $SESSION:0.0

# Deploy Contract: Panel 1
tmux send-keys -t $SESSION:0.1 'cd blockchain && npx hardhat ignition deploy ignition/modules/PoT.js --network besu' C-m
tmux send-keys -t $SESSION:0.1 'y' C-m
sleep 10

# API: Panel 1
tmux send-keys -t $SESSION:0.1 'cd ../auditapathAPI && python3 main.py' C-m
sleep 5

# Mininet: Panel 2
tmux send-keys -t $SESSION:0.2 'cd polka-halfsiphash && sudo python3 run_linear_topology.py' C-m
tmux select-pane -t $SESSION:0.2

# Exibe a sessão
tmux attach -t $SESSION
