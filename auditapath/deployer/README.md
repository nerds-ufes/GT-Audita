# Auditapath Deployer

This service is responsible for the lifecycle of the **Proof of Transit (PoT)** Smart Contracts. It compiles the Solidity code, deploys the contracts to the target blockchain (Local Besu or External Network), and exports the necessary artifacts (ABI and Address) for the API to consume.

## 🚀 Technologies

* **Node.js 18**
* **Hardhat** (Development Environment)
* **Hardhat Ignition** (Deployment System)
* **Solidity 0.8.28**

---

## ⚙️ Configuration

The deployer connects to the blockchain specified by environment variables. This allows the same container to deploy to a local testing node or a remote network without code changes.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `BLOCKCHAIN_HOST` | The RPC URL of the blockchain node. | `http://besu:8545` |
| `HARDHAT_IGNITION_CONFIRM_DEPLOYMENT` | Disables confirmation prompts (essential for Docker). | `false` |

*Note: The private key for deployment is currently configured in `hardhat.config.js`. For production/external networks, ensure the account has enough funds for gas.*

---

## 🔄 Workflow

When the container starts, it executes the script `scripts/run_ignition_deploy.js`. The workflow is as follows:

1.  **Compilation:** Hardhat compiles the `PoT.sol` contract.
2.  **Deployment:** Uses **Hardhat Ignition** (module `ignition/modules/PoT.js`) to deploy the `PoTFactory` contract.
3.  **Export:** * Retrieves the deployed contract address.
    * Reads the ABI (Application Binary Interface) from the artifacts.
    * **Writes a JSON file** to `/data/contract-data.json`.

### Output File (`contract-data.json`)
The API container waits for this file to be created in the shared volume before starting. Its structure is:
```json
{
  "contract_address": "0x123...",
  "abi": [...]
}
```
---

## 🐳 How to Run (Docker)

This service is typically managed by the main `docker-compose.yml` of the project using profiles.

### 1. Local Network (Besu)
Deploys to the local Hyperledger Besu node defined in the compose file.
```bash
docker compose --profile local up deployer-local
```
### 2. External Network (Iliada)
Deploys to the remote Iliada network.
```bash
BLOCKCHAIN_HOST="[http://200.137.0.26:21031](http://200.137.0.26:21031)" docker compose --profile iliada up deployer-iliada
```
---
## 🛠 How to Run (Manual / Development)
If you need to run this locally without Docker:

### 1. Install Dependencies:
```bash
npm install
```
### 2. Compile Contracts:
```bash
npx hardhat compile
```
### 3. Run Deployment Script:
Make sure you have a blockchain running (e.g., Besu or Ganache) and set the host if it's not localhost.
```bash
export BLOCKCHAIN_HOST="http://localhost:8545"
npx hardhat run scripts/run_ignition_deploy.js --network besu
```
