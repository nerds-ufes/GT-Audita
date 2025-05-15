require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  networks: {
    besu: {
      url: "http://localhost:8545", 
      accounts: ["0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63"], 
    }
  },
  solidity: "0.8.28",
};
