from flask import Flask, jsonify, request
from flask_restful import Api
from web3 import Web3
from web3.exceptions import Web3RPCError
import json
from http import HTTPStatus
from dotenv import load_dotenv
import os

app = Flask(__name__)
api = Api(app)

load_dotenv()

# Conectar-se ao Ganache (assumindo que o Ganache está rodando na porta padrão 8545)
w3 = Web3(Web3.HTTPProvider('http://200.137.0.26:21031'))

# Verificar a conexão
if w3.is_connected():
    print("Conectado à blockchain com sucesso!")
else:
    print("Não foi possível conectar-se à blockchain")
    exit()

# Endereço da conta que fez a implantação
deployer_address = "0x627306090abaB3A6e1400e9345bC60c78a8BEf57"  # Conta padrão de testes
deployer_private_key = "0xc87509a1c067bbde78beb793e6fa76530b6382a4c0241e5e4a9ec0a0f44dc0d3"
print("Endereço da conta que realizou deploy: " + deployer_address)

## Endereço do contrato ##
# Path arquivo abi
smart_contract_name = 'PoTFactory'
field_json = f'{smart_contract_name}Module#{smart_contract_name}'
abi_file_path = '../blockchain/ignition/deployments/chain-10001/deployed_addresses.json'
# Carregando a abi do arquivo json
with open(abi_file_path, 'r') as json_file:
    data = json.load(json_file)

contract_address = data[field_json]
print(f"Endereço do contrato implantado: {contract_address}")

## ABI do contrato ## 
# Path arquivo abi
smart_contract_name = 'PoTFactory'
abi_file_path = f'../blockchain/artifacts/contracts/PoT.sol/{smart_contract_name}.json'
# Carregando a abi do arquivo json
with open(abi_file_path, 'r') as json_file:
    data = json.load(json_file)
    
abi = data['abi']


# Obter instância do contrato
contract = w3.eth.contract(address=contract_address, abi=abi)

## Contas padrão de testes do Besu ##
# Endereço da controller
controller_address = "0x627306090abaB3A6e1400e9345bC60c78a8BEf57"
controller_private_key = "0xc87509a1c067bbde78beb793e6fa76530b6382a4c0241e5e4a9ec0a0f44dc0d3"
print('Endereço do nó de controle: ' + controller_address)

# Endereço do nó de saída
egress_address = "0xf17f52151EbEF6C7334FAD080c5704D77216b732"
egress_private_key = "0xae6ae8e5ccbfb04590405997ee2d52d2b330726137b875053c36d94e974d162f"
print('Endereço do nó de saída: ' + egress_address)

# Endereço do auditor
# auditor_address = w3.eth.accounts[3]
# print('Endereço para auditor: ' + auditor_address)

# Função para chamar `echo` e emitir o evento
def call_echo(message):
    # Prepara a transação para chamar a função `echo`
    transaction = contract.functions.echo(message).build_transaction({
        'from': controller_address,
        'gas': 2000000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(controller_address),
    })

    # Assinar transacao
    signed_tx = w3.eth.account.sign_transaction(transaction, controller_private_key)

    # Envia a transação
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Espera a transação ser minerada
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Captura os logs do evento Echo
    logs = contract.events.Echo.create_filter(from_block=tx_receipt['blockNumber'], to_block=tx_receipt['blockNumber']).get_all_entries()

    # Extrai a mensagem do evento
    for log in logs:
        print(f"Mensagem do evento Echo: {log['args']['message']}")

    return w3.to_hex(tx_hash)

# Função para chamar `newFlow`
def call_newFlow(newFlowContract):

    # Prepara a transação
    nonce = w3.eth.get_transaction_count(controller_address)

    tx = contract.functions.newFlow(
        newFlowContract['flowId'],
        newFlowContract['edgeAddr'],
        newFlowContract['routeId']
    ).build_transaction({
        'from': controller_address,
        'gas': 2000000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': nonce,
        'chainId': w3.eth.chain_id  
    })

    # Assina a transação
    signed_tx = w3.eth.account.sign_transaction(tx, controller_private_key)

    # Envia a transação assinada
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    return w3.to_hex(tx_hash)


# Função para chamar `setFlowProbeHash` e emitir o evento
def call_setFlowProbeHash(newRefSig):

    tx = contract.functions.setFlowProbeHash(
        newRefSig['flowId'],
        newRefSig['timestamp'],
        newRefSig['lightMultSig']
    ).build_transaction({
        'from': controller_address,
        'gas': 2000000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(controller_address),
        'chainId': w3.eth.chain_id  
    })

    # Assina a transação
    signed_tx = w3.eth.account.sign_transaction(tx, controller_private_key)

    # Envia a transação assinada
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    return w3.to_hex(tx_hash)

# Função para chamar `logProbe` e emitir o evento
def call_logFlowProbeHash(newlogProbe):

    # Prepara a transação para chamar a função `logProbe
    tx = contract.functions.logFlowProbeHash(
        newlogProbe['flowId'], 
        newlogProbe['timestamp'], 
        newlogProbe['lightMultSig']
    ).build_transaction({
        'from': egress_address,
        'gas': 2000000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(egress_address),
        'chainId': w3.eth.chain_id  
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, egress_private_key)

    # Envia a transação assinada
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    return w3.to_hex(tx_hash)

def call_setRouteId(newRouteAndEdge):

    # Prepara a transação
    nonce = w3.eth.get_transaction_count(controller_address)

    tx = contract.functions.setRouteId(
        newRouteAndEdge['flowId'],
        newRouteAndEdge['newRouteId'],
        newRouteAndEdge['newEdgeAddr']
    ).build_transaction({
        'from': controller_address,
        'gas': 2000000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': nonce,
        'chainId': w3.eth.chain_id  
    })

    # Assina a transação
    signed_tx = w3.eth.account.sign_transaction(tx, controller_private_key)

    # Envia a transação assinada
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    return w3.to_hex(tx_hash)

def call_getFlowCompliance(flowId):
    # Chama a função `getFlowCompliance`

    result = {}
    try:
        success, fail, nil, routeId = contract.functions.getFlowCompliance(flowId).call()   
        status = HTTPStatus.OK

        result["success"] = success
        result["fail"] = fail
        result["nil"] = nil
        result["routeId"] = routeId

    except Web3RPCError as e:
        status = HTTPStatus.INTERNAL_SERVER_ERROR
        result = e.rpc_response['error']['message']
    
    return status, result

def call_getFlowSizeRoutesHistory(flowId):
    # Chama a função `getFlowSizeRoutesHistory`

    result = 0
    try:
        result = contract.functions.getFlowSizeRoutesHistory(flowId).call()
        status = HTTPStatus.OK

    except Web3RPCError as e:
        status = HTTPStatus.INTERNAL_SERVER_ERROR
        result = e.rpc_response['error']['message']
    
    return status, result

def call_getFlowComplianceOfRouteHistoryIndex(flowId, index):
    # Chama a função `getFlowComplianceOfRouteHistoryIndex`

    result = {}
    try:
        success, fail, nil, routeId = contract.functions.getFlowComplianceOfRouteHistoryIndex(flowId, index).call()   
        status = HTTPStatus.OK

        result["success"] = success
        result["fail"] = fail
        result["nil"] = nil
        result["routeId"] = routeId

    except Web3RPCError as e:
        status = HTTPStatus.INTERNAL_SERVER_ERROR
        result = e.rpc_response['error']['message']
    
    return status, result

def verify_tx_status(tx_hash):
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if tx_receipt:
        if tx_receipt['status'] == 1:
            print("--> A transação foi executada com sucesso.")
            return HTTPStatus.OK
        else:
            print("--> A transação falhou.")
            return HTTPStatus.INTERNAL_SERVER_ERROR
    else:
        print("--> A transação ainda está pendente.")
        return HTTPStatus.ACCEPTED


@app.route('/')
def home():
    return jsonify("Working")

@app.route('/hello')
def hello():
    data = call_echo("Hello")
    return jsonify(data)

@app.route('/deployFlowContract', methods=['POST'])
def deployFlowContract():
    data = request.get_json()

    if 'flowId' not in data or 'routeId' not in data or 'edgeAddr' not in data:
        return jsonify({"error": "Invalid Data"}), HTTPStatus.BAD_REQUEST
    
    newFlowContract = {
        "flowId": data['flowId'],
        "routeId": data['routeId'],
        "edgeAddr": data['edgeAddr']
    }

    tx_hash = call_newFlow(newFlowContract)

    verify_tx_status(tx_hash)

    return jsonify(tx_hash), HTTPStatus.CREATED

@app.route('/setRefSig', methods=['POST'])
def setRefSig():
    data = request.get_json()

    required_keys = ['flowId', 'routeId', 'timestamp', 'lightMultSig']
    if not all(key in data for key in required_keys):   
        return jsonify({"error": "Invalid Data"}), HTTPStatus.BAD_REQUEST
    
    print(data)
    
    newRefSig = {
        "flowId": data['flowId'],
        "routeId": data['routeId'],
        "timestamp": data['timestamp'],
        "lightMultSig": data['lightMultSig'],
    }

    tx_hash = call_setFlowProbeHash(newRefSig)

    status_http = verify_tx_status(tx_hash)

    if(status_http == HTTPStatus.OK):
        message = tx_hash
    else: 
        try:
            tx = w3.eth.get_transaction(tx_hash) 
            w3.eth.call({
                'to': tx['to'],
                'data': tx['input']
            })
        except Web3RPCError as e:
            message = e.rpc_response['error']['message']
    
    return jsonify(message), status_http

@app.route('/logProbe', methods=['POST'])
def logProbe():
    data = request.get_json()

    required_keys = ['flowId', 'routeId', 'timestamp', 'lightMultSig']
    if not all(key in data for key in required_keys):   
        return jsonify({"error": "Invalid Data"}), HTTPStatus.BAD_REQUEST
    
    print(data)

    newlogProbe = {
        "flowId": data['flowId'],
        "routeId": data['routeId'],
        "timestamp": data['timestamp'],
        "lightMultSig": data['lightMultSig'],
    }

    tx_hash = call_logFlowProbeHash(newlogProbe)

    status_http = verify_tx_status(tx_hash)

    if(status_http == HTTPStatus.OK):
        message = tx_hash
    else: 
        try:
            tx = w3.eth.get_transaction(tx_hash) 
            w3.eth.call({
                'to': tx['to'],
                'data': tx['input']
            })
        except Web3RPCError as e:
            message = e.rpc_response['error']['message']
    
    return jsonify(message), status_http


@app.route('/setRouteId', methods=['POST'])
def setRouteId():
    data = request.get_json()

    if 'flowId' not in data or 'newRouteId' not in data or 'newEdgeAddr' not in data:
        return jsonify({"error": "Invalid Data"}), HTTPStatus.BAD_REQUEST
    
    newRouteAndEdge = {
        "flowId": data['flowId'],
        "newRouteId": data['newRouteId'],
        "newEdgeAddr": data['newEdgeAddr']
    }

    tx_hash = call_setRouteId(newRouteAndEdge)

    verify_tx_status(tx_hash)

    return jsonify(tx_hash), HTTPStatus.CREATED

@app.route('/getFlowCompliance/<flowId>', methods=['GET'])
def getFlowCompliance(flowId):
    status, result = call_getFlowCompliance(flowId)

    if status == HTTPStatus.OK:
        response = [
            {
                "success": result["success"], 
                "fail": result["fail"],
                "nil": result["nil"], 
            }, 
            result["routeId"] 
        ]
    else:
        response = result

    
    return jsonify(response), status

@app.route('/getFlowSizeRoutesHistory/<flowId>', methods=['GET'])
def getFlowSizeRoutesHistory(flowId):
    status, result = call_getFlowSizeRoutesHistory(flowId)

    if status == HTTPStatus.OK:
        response = [result]
    else:
        response = result

    return jsonify(response), status

@app.route('/getFlowComplianceOfRouteHistoryIndex/<flowId>/<index>', methods=['GET'])
def getFlowComplianceOfRouteHistoryIndex(flowId, index):

    index = int(index)
    status, result = call_getFlowComplianceOfRouteHistoryIndex(flowId, index)

    if status == HTTPStatus.OK:
        response = [
            {
                "success": result["success"], 
                "fail": result["fail"],
                "nil": result["nil"], 
            }, 
            result["routeId"] 
        ]
    else:
        response = result

    
    return jsonify(response), status

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
