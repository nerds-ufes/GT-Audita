# GT-Audita · 🔒📡 Auditoria de Tráfego em Redes com Blockchain

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)]()
[![GitHub Repo stars](https://img.shields.io/github/stars/nerds-ufes/GT-Audita?style=social)]()

## 🧠 Sobre o Projeto

**GT-Audita** é uma solução integrada para a **auditoria e rastreabilidade de acessos e fluxos de dados em redes IP**, combinando ferramentas de observabilidade com tecnologias de blockchain para garantir **transparência, integridade e conformidade regulatória**.

O sistema busca atender aos princípios da Política Nacional de Segurança da Informação (PNSI), oferecendo uma abordagem robusta para gestão de incidentes, investigações forenses e prestação de contas.

---

## 🎯 Objetivos

- 📜 Garantir **auditabilidade** de acessos e eventos de rede.
- 🔐 Assegurar **integridade e imutabilidade** dos registros com blockchain.
- 🕵️ Facilitar **investigações forenses** e análise de incidentes.
- 🌐 Ser aplicável a ambientes diversos como ISPs, redes acadêmicas (ex: eduroam) e instituições públicas.

---

## 🧱 Arquitetura Geral

```plaintext
[ FIREWALL / DHCP / RADIUS ]
            │
       [ Logstash ]
            │
         [ Redis ]
            │
   [ Verificador de Logs ]
            │
  ┌──────────┴──────────┐
  │                     │
[ ElasticSearch ]   [ Blockchain (Besu + Solidity) ]
                        │
            [ Provas de Trânsito / Provas de Conexão <-> Hash dos Logs ]

## 🧭 Auditabilidade de Caminho na Rede

Para garantir **rastreabilidade de fluxos de pacotes**, o GT-Audita estende seu escopo para a **verificação de caminho em redes path-aware**, com foco inicial na arquitetura PolKA[^6]. Este modelo permite a **inserção de identificadores de rota (routeIDs) auditáveis** diretamente nos pacotes, além de prover mecanismos de autenticação por salto e infraestrutura de chaves para assinatura de origem e destino.

> 🎯 **Objetivo**: Implementar um mecanismo de "prova de trânsito" com granularidade por fluxo, de forma eficiente e escalável.

### ⚠️ Desafio de Escalabilidade

As tecnologias blockchain atuais (como Hyperledger Besu) possuem limites práticos de escalabilidade — geralmente até dezenas de milhares de transações por segundo (TPS), o que contrasta com o throughput de switches que podem processar milhões de pacotes por segundo por interface.

Para lidar com isso, propomos uma abordagem baseada em **sondas amostradas** (In-band Network Telemetry[^8]):

- Cada fluxo monitorado tem uma **taxa de sondagem configurável** (ex: 10 sondas por segundo).
- Essas sondas são pacotes reais, modificados para carregar metadados de verificação (routeID, timestamp, assinatura).
- A granularidade da prova de trânsito é ajustável por configuração do fluxo.

---

### 🔄 Processo de Verificação de Caminho

1. **Configuração (Controller)**  
   - O controlador calcula um identificador de fluxo `flowID = H(porto, portd, ipo, ipd)`.
   - Seleciona um caminho auditável `routeID` (ex: R=16d).
   - Define a taxa de amostragem (e.g., 1 pacote/s).
   - Configura o nó de borda de entrada (ingress edge).
   - Implanta um contrato inteligente no Hyperledger Besu para armazenar e validar as sondas.

2. **Configuração do Nó de Borda (Ingress Edge)**  
   - Insere o `routeID` em todos os pacotes do fluxo.
   - Escolhe aleatoriamente pacotes para funcionar como sondas conforme a taxa definida.
   - Gera `timestamp` e campo de assinatura inicial nas sondas.

3. **Assinatura pelos Nós de Núcleo (Core Nodes)**  
   - Cada roteador no caminho computa uma **assinatura leve** dos dados de roteamento.
   - Atualiza o campo de assinatura da sonda em cada salto.

4. **Verificação (Egress Edge)**  
   - Extrai os metadados dos pacotes ao saírem do domínio administrativo.
   - Se o pacote for uma sonda, calcula `flowID`, e chama:
     ```solidity
     log_Probe(flowID, routeID, timestamp, signatureLog)
     ```
   - Essa transação representa a **prova registrada do caminho** seguido pela sonda.

A verificação pode ser feita **em tempo real** (via eventos) ou **offline**, como parte de auditorias ou análises forenses de tráfego.

---

### 🔐 Blockchain e Contratos Inteligentes

- **Hyperledger Besu** será o framework blockchain utilizado.
- Os **contratos em Solidity** armazenarão os registros de sonda e validações.
- A assinatura criptográfica acumulada nos pacotes permite verificar se o fluxo seguiu o caminho esperado.

---
