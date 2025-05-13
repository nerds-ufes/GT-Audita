#!/bin/bash

# Inicializa blockchain e API

cd blockchain

# Abre um terminal com o Hardhat node
gnome-terminal -- bash -c "npx hardhat node; exec bash"

# Aguarda 5 segundos para garantir que o Hardhat node inicialize
sleep 5

# Abre outro terminal para rodar o deploy
gnome-terminal -- bash -c "npx hardhat ignition deploy ignition/modules/PoT.js --network localhost;"

# Aguarda 5 segundos para garantir que o deploy seja realizado
sleep 5

# Inicializa a API
gnome-terminal -- bash -c "
    cd ../auditapathAPI;
    python3 main.py;
    exec bash;" 

# Aguarda 5 segundos para garantir que a API seja inicializada
sleep 5

# Roda o teste com o Mininet
gnome-terminal -- bash -c "
    cd ../polka-halfsiphash;
    sudo python3 run_linear_topology.py;
    exec bash;" 