// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.17 <0.9.0;

contract ProofOfTransit{
    address private controller;
    uint private startTime;
    
    mapping(string => string) public probHash;
    logStructure public currentRouteIdAudit;

    struct logStructure{
        uint probeFailAmount;
        uint probeNullAmount;
        uint probeSuccessAmount;

        string routeId;
        address egressEdge;
        uint lastTimestamp;
    }

    logStructure[] public routesHistory;

    event ControllerSet(address indexed oldController, address indexed newController);

    modifier isController(address senderAddr) {
        require(senderAddr == controller, "Caller is not controller");
        _;
    }

    modifier isEgressEdge(address senderAddr) {
        require(senderAddr == currentRouteIdAudit.egressEdge, "Caller is not egress edge");
        _;
    }
    
    constructor(address controllerAddr, address egress_edgeAddr, string memory routeId) {
        controller = controllerAddr;
        startTime = block.timestamp;
        
        currentRouteIdAudit.probeFailAmount = 0;
        currentRouteIdAudit.probeSuccessAmount = 0;
        currentRouteIdAudit.probeNullAmount = 0;

        currentRouteIdAudit.egressEdge = egress_edgeAddr;
        currentRouteIdAudit.routeId = routeId;
   
        emit ControllerSet(address(0), controller);
    }

    /* POT FUNCTIONS */
    function changeController(address newController, address senderAddr) public isController(senderAddr) {
        emit ControllerSet(controller, newController);
        controller = newController;
    }

    function changeRouteIdAndEgressEdge(string memory newRouteId, address newEgressEdge, address senderAddr) public isController(senderAddr) {
        currentRouteIdAudit.lastTimestamp = block.timestamp;

        routesHistory.push(currentRouteIdAudit);

        currentRouteIdAudit.probeFailAmount = 0;
        currentRouteIdAudit.probeSuccessAmount = 0;
        currentRouteIdAudit.probeNullAmount = 0;

        currentRouteIdAudit.egressEdge = newEgressEdge;
        currentRouteIdAudit.routeId = newRouteId;
        currentRouteIdAudit.lastTimestamp = 0;
    }

    function getController() external view returns (address) {
        return controller;
    }

    function setProbeHash(string memory id_x, string memory hash, address senderAddr) public isController(senderAddr) {
        probHash[id_x] = hash;
    }

    event ProbeFail();

    function logProbe(string memory id_x,string memory sig, address senderAddr) public isEgressEdge(senderAddr){
        if (compareStrings(probHash[id_x],"")) {
            currentRouteIdAudit.probeNullAmount += 1;
        } else if (compareStrings(probHash[id_x],sig)){
            currentRouteIdAudit.probeSuccessAmount += 1;
        } else {
            currentRouteIdAudit.probeFailAmount += 1;
            emit ProbeFail();
        }
    }

    function getCompliance() public view returns (uint, uint, uint, string memory) {
        return (currentRouteIdAudit.probeSuccessAmount, 
                currentRouteIdAudit.probeFailAmount,
                currentRouteIdAudit.probeNullAmount,
                currentRouteIdAudit.routeId);
    }

    function getSizeRoutesHistory() public view returns (uint) {
        return routesHistory.length;
    }

    function getComplianceOfRouteHistoryIndex(uint index) public view returns (uint, uint, uint, string memory) {
        return (routesHistory[index].probeSuccessAmount, 
                routesHistory[index].probeFailAmount,
                routesHistory[index].probeNullAmount,
                routesHistory[index].routeId);
    }

    /* AUX FUNCTIONS */
    function compareStrings(string memory a, string memory b) internal pure returns (bool) {
        return (keccak256(abi.encodePacked((a))) == keccak256(abi.encodePacked((b))));
    }

}

contract PoTFactory{
    mapping(string => ProofOfTransit) private flowPOT;
    mapping(string => address) public flowAddr;

    event Echo(string message);

    modifier isFlowRegistered(string memory flowId){
        require(flowAddr[flowId] != address(0), "No flow is registered with the provided flow ID");
        _;
    }

    function echo(string calldata message) external {
        emit Echo(message);
    }

    function newFlow(string memory flowId, address egress_edgeAddr, string memory routeId) public{
        ProofOfTransit new_pot = new ProofOfTransit(msg.sender,egress_edgeAddr,routeId);

        flowPOT[flowId] = new_pot;
        flowAddr[flowId] = address(new_pot);
    }

    function setFlowProbeHash(string memory flowId, string memory id_x, string memory hash) public isFlowRegistered(flowId){
        ProofOfTransit pot = ProofOfTransit(flowPOT[flowId]);
        
        pot.setProbeHash(id_x,hash,msg.sender);
    }

    function logFlowProbeHash(string memory flowId, string memory id_x, string memory hash) public isFlowRegistered(flowId){
        ProofOfTransit pot = ProofOfTransit(flowPOT[flowId]);
        
        pot.logProbe(id_x,hash,msg.sender);
    }

    function setRouteId(string memory flowId, string memory newRouteID, address newEgressEdge) public isFlowRegistered(flowId){
        ProofOfTransit pot = ProofOfTransit(flowPOT[flowId]);
        
        pot.changeRouteIdAndEgressEdge(newRouteID, newEgressEdge, msg.sender);
    }

    function getFlowSizeRoutesHistory(string memory flowId) public view isFlowRegistered(flowId) returns (uint sizeRoutesHistory){
        ProofOfTransit pot = ProofOfTransit(flowPOT[flowId]);

        sizeRoutesHistory = pot.getSizeRoutesHistory();

        return sizeRoutesHistory;
    }     

    function getFlowCompliance(string memory flowId) public view isFlowRegistered(flowId) returns (uint success, uint fail, uint nil, string memory routeId){
        ProofOfTransit pot = ProofOfTransit(flowPOT[flowId]);

        (success, fail, nil, routeId) = pot.getCompliance();

        return (success, fail, nil, routeId);
    }

    function getFlowComplianceOfRouteHistoryIndex(string memory flowId, uint index) public view isFlowRegistered(flowId) returns (uint success, uint fail, uint nil, string memory routeId){
        ProofOfTransit pot = ProofOfTransit(flowPOT[flowId]);

        (success, fail, nil, routeId) = pot.getComplianceOfRouteHistoryIndex(index);

        return (success, fail, nil, routeId);
    }
}