## Audita Path API: API for Comunication Between Path-Aware Network and Ethereum Blockchain
 
### API Endpoints
* `POST deployFlowContract(String flowId, String routeId, String edgeAddr)`
* `POST setRefSig(String flowId, String routeId, String refSig`
* `POST logProbe(String flowId, String routeId, String timestamp, String lightMultSig)`
* `GET getFlowCompliance(String flowId)`

### Technologies Used for Implementation and Testing
* Python
* Web3.py
* Flask
* Remix IDE
* Ganache

### How to Run in a Local Test Environment
* Clone the repository
* Open the "Smart Contract" folder in Remix IDE
* Compile and deploy the smart contrct via the Remix IDE. 
    * Connect to the Ganache environment.
* Start Ganache locally on port 8454.
* Install the requirements by running the command `pip3 install -r requirements.txt`.
* Run the Python server script with the command `python3 main.py`
* The web server will be running on port 5000 and ready to accept HTTP requests.

