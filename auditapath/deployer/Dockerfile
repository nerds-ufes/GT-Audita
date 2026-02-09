FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY hardhat.config.js .
COPY ignition/ ./ignition
COPY contracts/ ./contracts

RUN npx hardhat compile

COPY scripts/ ./scripts

CMD ["npx", "hardhat", "run", "scripts/run_ignition_deploy.js", "--network", "besu"]