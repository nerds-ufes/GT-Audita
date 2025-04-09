from flask import Flask, jsonify, request
from flask_restful import Api
from web3 import Web3
from web3.exceptions import Web3RPCError
import json
from http import HTTPStatus

app = Flask(__name__)
api = Api(app)

# Conectar-se ao Ganache (assumindo que o Ganache está rodando na porta padrão 8545)
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Verificar a conexão
if w3.is_connected():
    print("Conectado ao Ganache com sucesso!")
else:
    print("Falha na conexão com Ganache.")

## Endereço do contrato ##

# Endereço da conta que fez a implantação (pode ser obtido no Remix ou Metamask)
deployer_address =  w3.eth.accounts[0]
print("Endereço da conta que realizou deploy: " + deployer_address)

# Função para obter a transação de deploy do contrato
def get_contract_address(deployer_address, start_block=0, end_block='latest'):    
    contract_address = ""
    # Obtem o bloco final (ou o último bloco se 'latest' for passado)
    if end_block == 'latest':
        end_block = w3.eth.block_number
    
    # Iterar pelos blocos entre o intervalo fornecido
    for block_number in range(start_block, end_block + 1):
        block = w3.eth.get_block(block_number, full_transactions=True)
        
        for tx in block.transactions:
            # Verifica se o endereço está envolvido na transação
            if tx['from'].lower() == deployer_address.lower() or tx['to'] and tx['to'].lower() == deployer_address.lower():
                # Obter o recibo da transação (contém o endereço do contrato)
                tx_receipt = w3.eth.get_transaction_receipt(tx['hash'])
                
                # Se a transação for uma implantação de contrato, obtemos o endereço
                if tx_receipt['contractAddress']:
                    contract_address = tx_receipt['contractAddress']
    
    if contract_address == "":
        print("Erro na obtenção do endereço do contrato!")
        exit()

    return contract_address

contract_address = get_contract_address(deployer_address)
print(f"Endereço do contrato implantado: {contract_address}")

## ABI do contrato ## 
 # Path arquivo abi
smart_contract_name = 'PoTFactory'
abi_file_path = f'SmartContract/artifacts/{smart_contract_name}_metadata.json'
 # Carregando a abi do arquivo json
with open(abi_file_path, 'r') as json_file:
    data = json.load(json_file)
    
abi = data['output']['abi']


# Obter instância do contrato
contract = w3.eth.contract(address=contract_address, abi=abi)

## Ganache accounts ##
# Endereço da controller
sender_address = w3.eth.accounts[1]

# Endereço do nó de saída
egress_address = w3.eth.accounts[2]
print('Endereço do nó de saída: ' + egress_address)

# Endereço do auditor
# auditor_address = w3.eth.accounts[3]
# print('Endereço para auditor: ' + auditor_address)

# Função para chamar `echo` e emitir o evento
def call_echo(message):
    # Prepara a transação para chamar a função `echo`
    transaction = contract.functions.echo(message).build_transaction({
        'from': sender_address,
        'gas': 2000000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(sender_address),
    })

    # Envia a transação
    tx_hash = w3.eth.send_transaction(transaction)

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
    # Prepara a transação para chamar a função `newFlow`
    transaction = contract.functions.newFlow(newFlowContract['flowId'], newFlowContract['edgeAddr'], newFlowContract['routeId']).build_transaction({
        'from': sender_address,
        'gas': 2000000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(sender_address),
    })

    # Envia a transação
    tx_hash = w3.eth.send_transaction(transaction)

    return w3.to_hex(tx_hash)


# Função para chamar `setFlowProbeHash` e emitir o evento
def call_setFlowProbeHash(newRefSig):
    # Prepara a transação para chamar a função `setFlowProbeHash`
    transaction = contract.functions.setFlowProbeHash(newRefSig['flowId'], newRefSig['timestamp'], newRefSig['lightMultSig']).build_transaction({
        'from': sender_address,
        'gas': 2000000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(sender_address),
    })

    # Envia a transação
    tx_hash = w3.eth.send_transaction(transaction)

    return w3.to_hex(tx_hash)

# Função para chamar `logProbe` e emitir o evento
def call_logFlowProbeHash(newlogProbe):
    # Prepara a transação para chamar a função `logProbe`
    transaction = contract.functions.logFlowProbeHash(newlogProbe['flowId'], newlogProbe['timestamp'], newlogProbe['lightMultSig']).build_transaction({
        'from': egress_address,
        'gas': 2000000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(egress_address),
    })

    # Envia a transação
    tx_hash = w3.eth.send_transaction(transaction)

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

def verify_tx_status(tx_hash):
    tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
    if tx_receipt:
        if tx_receipt['status'] == 1:
            print("logProbe: A transação foi executada com sucesso.")
            return HTTPStatus.OK
        else:
            print("logProbe: A transação falhou.")
            return HTTPStatus.INTERNAL_SERVER_ERROR
    else:
        print("logProbe: A transação ainda está pendente.")
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


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
