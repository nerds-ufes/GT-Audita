// /deploy/scripts/run_ignition_deploy.js

const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

// 1. Importe seu módulo Ignition simplificado
const PoTModule = require("../ignition/modules/PoT.js");

// 2. Defina o nome do contrato (para encontrar o ABI)
const CONTRACT_NAME = "PoT";

async function main() {
  console.log("Iniciando deploy com Hardhat Ignition (via script)...");

  // 3. Chame o deploy do Ignition e espere o resultado
  const { potFactory } = await hre.ignition.deploy(PoTModule);
  
  // 4. O deploy terminou! Agora temos o contrato.
  const contractAddress = await potFactory.getAddress();
  console.log(`Contrato '${CONTRACT_NAME}' deployado em: ${contractAddress}`);

  // 5. Encontre e leia o ABI (como fizemos antes)
  let abi;
  try {
    const abiPath = path.join(
      hre.config.paths.artifacts, // Ex: /app/artifacts
      `contracts/${CONTRACT_NAME}.sol/${CONTRACT_NAME}Factory.json`
    );
    const abiFile = fs.readFileSync(abiPath, "utf8");
    abi = JSON.parse(abiFile).abi;
  } catch (e) {
    console.error(`ERRO: Não foi possível encontrar o ABI: ${e.message}`);
    process.exit(1);
  }

  // 6. Salve o endereço E o ABI no volume compartilhado
  const outputData = {
    contract_address: contractAddress,
    abi: abi,
  };
  const outputPath = path.join("/data", "contract-data.json");
  
  try {
    fs.writeFileSync(outputPath, JSON.stringify(outputData, null, 2));
    console.log(`Endereço e ABI salvos em: ${outputPath}`);
  } catch (error) {
    console.error(`Falha ao salvar endereço/ABI em ${outputPath}:`, error);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});