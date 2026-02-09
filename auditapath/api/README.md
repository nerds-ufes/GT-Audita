# Auditapath API

The **Auditapath API** serves as the bridge between the path-aware network elements (like P4 switches or Mininet simulations) and the Ethereum Blockchain (Hyperledger Besu or External Networks). It handles transaction signing, smart contract interaction, and event logging for flow proofs.

## 🚀 Technologies

* **Python 3.10+**
* **Flask** (Web Framework)
* **Web3.py** (Blockchain Interaction)
* **Docker & Docker Compose**

---

## ⚙️ Configuration

The API behavior is controlled mainly by environment variables. When running via Docker, these are handled automatically by the profiles.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `BLOCKCHAIN_HOST` | The RPC URL of the blockchain node. | `http://besu:8545` (Docker) or `http://localhost:8545` (Local private blockchain) |

---

## 🐳 How to Run (Docker)

This project uses Docker Compose profiles to switch between environments easily.

### 1. Local Development (Local)
This starts the API connected to a local Hyperledger Besu node and the local Deployer.

```bash
# Run from the root of the repository
docker compose --profile local up --build
```

### 2. External Network (Iliada)
This starts the API connected to an external blockchain RPC.

```bash
# Run from the root of the repository
docker compose --profile iliada up --build
```
## 🛠 How to Run (Manual / Standalone)
If you prefer to run the API without Docker for debugging purposes:

### 1. Install Dependencies:

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables (Optional): Create a .env file or export the variable:

```bash
export BLOCKCHAIN_HOST="http://localhost:8545"
```

### 3. Run the Server:

```bash
python main.py
```
The server will start at http://0.0.0.0:5000

## 📡 API Endpoints

### General
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check. Returns "Working". |
| `GET` | `/hello` | Tests contract interaction by calling the `echo` function. |

### Flow Management
| Method | Endpoint | Description | Body Params (JSON) |
| :--- | :--- | :--- | :--- |
| `POST` | `/deployFlowContract` | Registers a new flow in the smart contract. | `flowId`, `routeId`, `edgeAddr` |
| `POST` | `/setRouteId` | Updates the active route ID for a flow. | `flowId`, `newRouteId`, `newEdgeAddr` |

### Audit & Logs
| Method | Endpoint | Description | Body Params (JSON) |
| :--- | :--- | :--- | :--- |
| `POST` | `/setRefSig` | Sets the reference signature (Probe Hash) by the Controller. | `flowId`, `routeId`, `timestamp`, `lightMultSig` |
| `POST` | `/logProbe` | Logs a probe verification from the Egress node. | `flowId`, `routeId`, `timestamp`, `lightMultSig` |

### Analytics
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/getFlowCompliance/<flowId>` | Returns the current success/fail/nil count for a flow. |
| `GET` | `/getFlowSizeRoutesHistory/<flowId>` | Returns the number of route changes in history. |
| `GET` | `/getFlowComplianceOfRouteHistoryIndex/<flowId>/<index>` | Returns compliance data for a specific historical route index. |
