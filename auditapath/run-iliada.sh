#!/bin/bash

SESSION="projeto-blockchain"

# Inicia nova sessão com um painel
tmux new-session -d -s $SESSION -n main

# Split panels
tmux split-window -h -t $SESSION:0.0

# API: Panel 0
tmux send-keys -t $SESSION:0.0 'cd auditapathAPI && python3 main.py' C-m
sleep 5

# Mininet: Panel 1
tmux send-keys -t $SESSION:0.1 'cd polka-halfsiphash && sudo python3 run_linear_topology.py' C-m
tmux select-pane -t $SESSION:0.1

# Exibe a sessão
tmux attach -t $SESSION
