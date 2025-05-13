# GT-Audita · 🔒📡 Auditoria de Tráfego em Redes com Blockchain

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)]()
[![GitHub Repo stars](https://img.shields.io/github/stars/nerds-ufes/GT-Audita?style=social)]()

## 🧠 Sobre o Projeto

**GT-Audita** é uma solução integrada para a **auditoria e rastreabilidade de acessos e fluxos de dados em redes**, combinando ferramentas de observabilidade com tecnologias de blockchain para garantir **transparência, integridade e conformidade regulatória**.

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

