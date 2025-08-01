"""
Blockchain Service - Integration layer for AGI-NARI systems with blockchain
Provides high-level blockchain services for AGI agents and consciousness systems
"""

import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

from blockchain_core import (
    AIBlockchain, TransactionType, ConsensusType, 
    ai_blockchain, Transaction, AIIdentity
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceType(Enum):
    """Types of blockchain services"""
    IDENTITY_MANAGEMENT = "identity_management"
    TRUST_VERIFICATION = "trust_verification"
    CONSENSUS_PARTICIPATION = "consensus_participation"
    SMART_CONTRACT_EXECUTION = "smart_contract_execution"
    REPUTATION_TRACKING = "reputation_tracking"
    DECISION_AUDITING = "decision_auditing"

@dataclass
class BlockchainServiceRequest:
    """Request for blockchain service"""
    service_type: ServiceType
    requester_id: str
    target_id: Optional[str]
    data: Dict[str, Any]
    priority: int = 1
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class BlockchainServiceResponse:
    """Response from blockchain service"""
    success: bool
    service_type: ServiceType
    result: Dict[str, Any]
    transaction_id: Optional[str]
    block_number: Optional[int]
    processing_time: float
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class AGIBlockchainIntegration:
    """Integration layer between AGI systems and blockchain"""
    
    def __init__(self, blockchain: AIBlockchain):
        self.blockchain = blockchain
        self.agi_agents = {}
        self.consciousness_records = []
        self.decision_audit_trail = []
        self.service_history = []
        
    async def register_agi_agent(self, agent_id: str, agi_capabilities: Dict[str, Any], 
                               consciousness_level: float = 0.0) -> Dict[str, Any]:
        """Register AGI agent with enhanced capabilities"""
        
        # Extract capabilities for blockchain
        blockchain_capabilities = []
        
        if agi_capabilities.get('reasoning', 0) > 0.7:
            blockchain_capabilities.append('advanced_reasoning')
        if agi_capabilities.get('learning', 0) > 0.7:
            blockchain_capabilities.append('meta_learning')
        if agi_capabilities.get('creativity', 0) > 0.6:
            blockchain_capabilities.append('creative_problem_solving')
        if consciousness_level > 0.5:
            blockchain_capabilities.append('consciousness_simulation')
        if agi_capabilities.get('empathy', 0) > 0.5:
            blockchain_capabilities.append('emotional_intelligence')
        
        # Register on blockchain
        ai_identity = self.blockchain.register_ai_agent(
            agent_id, 
            blockchain_capabilities,
            {
                'agi_capabilities': agi_capabilities,
                'consciousness_level': consciousness_level,
                'registration_type': 'agi_enhanced',
                'version': '1.0.0'
            }
        )
        
        # Store AGI-specific data
        self.agi_agents[agent_id] = {
            'identity': ai_identity,
            'agi_capabilities': agi_capabilities,
            'consciousness_level': consciousness_level,
            'interaction_history': [],
            'decision_history': [],
            'learning_outcomes': []
        }
        
        logger.info(f"AGI agent {agent_id} registered with consciousness level {consciousness_level}")
        
        return {
            'agent_id': agent_id,
            'blockchain_identity': asdict(ai_identity),
            'agi_capabilities': agi_capabilities,
            'consciousness_level': consciousness_level,
            'blockchain_capabilities': blockchain_capabilities
        }
    
    async def record_consciousness_state(self, agent_id: str, consciousness_data: Dict[str, Any]) -> str:
        """Record consciousness state on blockchain"""
        
        if agent_id not in self.agi_agents:
            raise ValueError(f"AGI agent {agent_id} not registered")
        
        # Create consciousness record transaction
        consciousness_tx = Transaction(
            transaction_id=f"consciousness_{agent_id}_{int(time.time())}",
            transaction_type=TransactionType.DECISION_RECORD,
            sender=agent_id,
            receiver="consciousness_network",
            data={
                "record_type": "consciousness_state",
                "consciousness_level": consciousness_data.get('consciousness_level', 0.0),
                "awareness_types": consciousness_data.get('awareness_types', []),
                "introspection_depth": consciousness_data.get('introspection_depth', 0),
                "meta_insights": consciousness_data.get('meta_insights', {}),
                "timestamp": time.time()
            },
            timestamp=time.time(),
            signature=""
        )
        
        # Sign transaction
        consciousness_tx.signature = self.blockchain.crypto_manager.create_transaction_signature(agent_id, consciousness_tx)
        
        # Add to blockchain
        self.blockchain.add_transaction(consciousness_tx)
        
        # Store locally
        consciousness_record = {
            'agent_id': agent_id,
            'consciousness_data': consciousness_data,
            'transaction_id': consciousness_tx.transaction_id,
            'timestamp': time.time()
        }
        
        self.consciousness_records.append(consciousness_record)
        
        logger.info(f"Consciousness state recorded for {agent_id}")
        
        return consciousness_tx.transaction_id
    
    async def record_agi_decision(self, agent_id: str, decision_data: Dict[str, Any]) -> str:
        """Record AGI decision with full reasoning chain"""
        
        if agent_id not in self.agi_agents:
            raise ValueError(f"AGI agent {agent_id} not registered")
        
        # Create decision record transaction
        decision_tx = Transaction(
            transaction_id=f"decision_{agent_id}_{int(time.time())}",
            transaction_type=TransactionType.DECISION_RECORD,
            sender=agent_id,
            receiver="decision_network",
            data={
                "record_type": "agi_decision",
                "problem_statement": decision_data.get('problem_statement', ''),
                "reasoning_chain": decision_data.get('reasoning_chain', []),
                "decision": decision_data.get('decision', ''),
                "confidence_score": decision_data.get('confidence_score', 0.0),
                "reasoning_type": decision_data.get('reasoning_type', 'unknown'),
                "domain": decision_data.get('domain', 'general'),
                "meta_insights": decision_data.get('meta_insights', {}),
                "timestamp": time.time()
            },
            timestamp=time.time(),
            signature=""
        )
        
        # Sign transaction
        decision_tx.signature = self.blockchain.crypto_manager.create_transaction_signature(agent_id, decision_tx)
        
        # Add to blockchain
        self.blockchain.add_transaction(decision_tx)
        
        # Store in audit trail
        audit_record = {
            'agent_id': agent_id,
            'decision_data': decision_data,
            'transaction_id': decision_tx.transaction_id,
            'timestamp': time.time(),
            'auditable': True
        }
        
        self.decision_audit_trail.append(audit_record)
        self.agi_agents[agent_id]['decision_history'].append(audit_record)
        
        logger.info(f"AGI decision recorded for {agent_id}")
        
        return decision_tx.transaction_id
    
    async def verify_agi_capability(self, verifier_id: str, target_id: str, 
                                  capability: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Verify AGI capability through blockchain consensus"""
        
        if verifier_id not in self.agi_agents or target_id not in self.agi_agents:
            raise ValueError("Both verifier and target must be registered AGI agents")
        
        # Create capability verification transaction
        verification_tx = self.blockchain.create_trust_verification_transaction(
            verifier_id,
            target_id,
            {
                "verification_type": "agi_capability",
                "capability": capability,
                "evidence": evidence,
                "verifier_credentials": self.agi_agents[verifier_id]['agi_capabilities'],
                "verification_method": "peer_review",
                "timestamp": time.time()
            }
        )
        
        # Add to blockchain
        self.blockchain.add_transaction(verification_tx)
        
        # Calculate verification score
        verification_score = await self._calculate_capability_verification_score(
            verifier_id, target_id, capability, evidence
        )
        
        # Update trust network
        trust_adjustment = verification_score - 0.5  # Convert to adjustment
        self.blockchain.trust_network.update_trust(
            verifier_id, 
            target_id, 
            {
                'success': verification_score > 0.6,
                'accuracy': verification_score,
                'reliability': 0.8,
                'verification_type': 'capability'
            }
        )
        
        return {
            'verification_transaction': verification_tx.transaction_id,
            'verification_score': verification_score,
            'capability': capability,
            'verifier': verifier_id,
            'target': target_id,
            'trust_updated': True,
            'timestamp': time.time()
        }
    
    async def _calculate_capability_verification_score(self, verifier_id: str, target_id: str, 
                                                     capability: str, evidence: Dict[str, Any]) -> float:
        """Calculate capability verification score"""
        
        verifier_capabilities = self.agi_agents[verifier_id]['agi_capabilities']
        target_capabilities = self.agi_agents[target_id]['agi_capabilities']
        
        # Verifier credibility
        verifier_credibility = 0.5
        if capability in ['reasoning', 'learning'] and verifier_capabilities.get('reasoning', 0) > 0.8:
            verifier_credibility += 0.2
        if capability == 'creativity' and verifier_capabilities.get('creativity', 0) > 0.7:
            verifier_credibility += 0.2
        if capability == 'consciousness' and self.agi_agents[verifier_id]['consciousness_level'] > 0.7:
            verifier_credibility += 0.3
        
        # Evidence quality
        evidence_quality = 0.5
        if 'performance_metrics' in evidence:
            evidence_quality += 0.2
        if 'test_results' in evidence:
            evidence_quality += 0.2
        if 'peer_evaluations' in evidence:
            evidence_quality += 0.1
        
        # Target's claimed capability level
        claimed_level = target_capabilities.get(capability, 0.0)
        
        # Verification score
        verification_score = (verifier_credibility * 0.4 + evidence_quality * 0.4 + claimed_level * 0.2)
        
        return min(1.0, max(0.0, verification_score))
    
    async def create_agi_collaboration_contract(self, creator_id: str, participants: List[str], 
                                              collaboration_terms: Dict[str, Any]) -> str:
        """Create smart contract for AGI collaboration"""
        
        if creator_id not in self.agi_agents:
            raise ValueError(f"Creator {creator_id} not registered as AGI agent")
        
        # Verify all participants are registered
        for participant in participants:
            if participant not in self.agi_agents:
                raise ValueError(f"Participant {participant} not registered as AGI agent")
        
        # Create collaboration contract code
        contract_code = f"""
        agi_collaboration_contract:
            participants: {participants}
            terms: {collaboration_terms}
            
            execute_collaboration:
                - verify_all_participants_active
                - check_capability_requirements
                - distribute_tasks_based_on_capabilities
                - monitor_collaboration_progress
                - record_outcomes_and_learnings
                - update_trust_relationships
        """
        
        # Contract conditions
        conditions = {
            'min_participants': len(participants),
            'required_capabilities': collaboration_terms.get('required_capabilities', []),
            'min_trust_level': collaboration_terms.get('min_trust_level', 0.6),
            'collaboration_type': collaboration_terms.get('type', 'general')
        }
        
        # Deploy contract
        contract_id = self.blockchain.deploy_smart_contract(creator_id, contract_code, conditions)
        
        logger.info(f"AGI collaboration contract {contract_id} created by {creator_id}")
        
        return contract_id
    
    async def participate_in_consensus(self, agent_id: str, proposal_id: str, 
                                     vote: bool, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Participate in blockchain consensus with AGI reasoning"""
        
        if agent_id not in self.agi_agents:
            raise ValueError(f"AGI agent {agent_id} not registered")
        
        # Calculate vote weight based on AGI capabilities and trust
        agent_data = self.agi_agents[agent_id]
        
        # Base weight from AGI capabilities
        capability_weight = sum(agent_data['agi_capabilities'].values()) / len(agent_data['agi_capabilities'])
        
        # Trust weight from network
        trust_weight = self.blockchain.trust_network.get_reputation(agent_id)
        
        # Consciousness weight
        consciousness_weight = agent_data['consciousness_level']
        
        # Combined vote weight
        vote_weight = (capability_weight * 0.4 + trust_weight * 0.4 + consciousness_weight * 0.2)
        
        # Create consensus transaction
        consensus_tx = Transaction(
            transaction_id=f"consensus_{agent_id}_{proposal_id}_{int(time.time())}",
            transaction_type=TransactionType.CONSENSUS_VOTE,
            sender=agent_id,
            receiver="consensus_network",
            data={
                "proposal_id": proposal_id,
                "vote": vote,
                "vote_weight": vote_weight,
                "reasoning": reasoning,
                "agi_capabilities": agent_data['agi_capabilities'],
                "consciousness_level": agent_data['consciousness_level'],
                "timestamp": time.time()
            },
            timestamp=time.time(),
            signature=""
        )
        
        # Sign transaction
        consensus_tx.signature = self.blockchain.crypto_manager.create_transaction_signature(agent_id, consensus_tx)
        
        # Add to blockchain
        self.blockchain.add_transaction(consensus_tx)
        
        return {
            'consensus_transaction': consensus_tx.transaction_id,
            'proposal_id': proposal_id,
            'vote': vote,
            'vote_weight': vote_weight,
            'reasoning': reasoning,
            'agent_id': agent_id,
            'timestamp': time.time()
        }
    
    async def audit_agi_decisions(self, agent_id: str, time_range: Tuple[float, float] = None) -> List[Dict[str, Any]]:
        """Audit AGI decisions from blockchain"""
        
        if time_range is None:
            time_range = (time.time() - 86400, time.time())  # Last 24 hours
        
        start_time, end_time = time_range
        
        # Filter decisions by agent and time range
        audited_decisions = []
        
        for record in self.decision_audit_trail:
            if (record['agent_id'] == agent_id and 
                start_time <= record['timestamp'] <= end_time):
                
                # Verify decision on blockchain
                blockchain_verified = await self._verify_decision_on_blockchain(record['transaction_id'])
                
                audit_entry = {
                    'decision_record': record,
                    'blockchain_verified': blockchain_verified,
                    'audit_timestamp': time.time(),
                    'integrity_check': 'passed' if blockchain_verified else 'failed'
                }
                
                audited_decisions.append(audit_entry)
        
        return audited_decisions
    
    async def _verify_decision_on_blockchain(self, transaction_id: str) -> bool:
        """Verify decision exists and is valid on blockchain"""
        
        # Search through blockchain for transaction
        for block in self.blockchain.chain:
            for transaction in block.transactions:
                if transaction.transaction_id == transaction_id:
                    # Verify transaction integrity
                    calculated_hash = transaction.calculate_hash()
                    return calculated_hash == transaction.hash
        
        return False
    
    def get_agi_trust_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive trust metrics for AGI agent"""
        
        if agent_id not in self.agi_agents:
            raise ValueError(f"AGI agent {agent_id} not registered")
        
        agent_data = self.agi_agents[agent_id]
        
        # Blockchain trust metrics
        blockchain_trust = self.blockchain.trust_network.get_reputation(agent_id)
        network_trust = self.blockchain.trust_network.calculate_network_trust(agent_id)
        trusted_by = len(self.blockchain.trust_network.find_trusted_agents(agent_id))
        
        # AGI-specific metrics
        decision_count = len(agent_data['decision_history'])
        consciousness_level = agent_data['consciousness_level']
        capability_scores = agent_data['agi_capabilities']
        
        # Calculate composite trust score
        composite_trust = (
            blockchain_trust * 0.3 +
            network_trust * 0.3 +
            consciousness_level * 0.2 +
            sum(capability_scores.values()) / len(capability_scores) * 0.2
        )
        
        return {
            'agent_id': agent_id,
            'blockchain_trust': blockchain_trust,
            'network_trust': network_trust,
            'composite_trust': composite_trust,
            'trusted_by_count': trusted_by,
            'decision_count': decision_count,
            'consciousness_level': consciousness_level,
            'capability_scores': capability_scores,
            'trust_relationships': len(self.blockchain.trust_network.trust_relationships.get(agent_id, {})),
            'reputation_trend': 'stable',  # Would calculate from history
            'timestamp': time.time()
        }
    
    def get_blockchain_integration_status(self) -> Dict[str, Any]:
        """Get status of AGI-blockchain integration"""
        
        return {
            'system': 'AGI Blockchain Integration',
            'version': '1.0.0',
            'status': 'operational',
            'registered_agi_agents': len(self.agi_agents),
            'consciousness_records': len(self.consciousness_records),
            'decision_audit_trail': len(self.decision_audit_trail),
            'service_requests_processed': len(self.service_history),
            'blockchain_status': self.blockchain.get_blockchain_status(),
            'integration_capabilities': {
                'agi_identity_management': True,
                'consciousness_recording': True,
                'decision_auditing': True,
                'capability_verification': True,
                'collaboration_contracts': True,
                'consensus_participation': True,
                'trust_metrics': True
            },
            'timestamp': datetime.now().isoformat()
        }

# Global AGI blockchain integration
agi_blockchain_integration = AGIBlockchainIntegration(ai_blockchain)

# FastAPI service
app = FastAPI(title="AGI Blockchain Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/register_agi_agent")
async def register_agi_agent(request: Dict[str, Any]):
    """Register AGI agent with blockchain"""
    try:
        result = await agi_blockchain_integration.register_agi_agent(
            request['agent_id'],
            request['agi_capabilities'],
            request.get('consciousness_level', 0.0)
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/record_consciousness")
async def record_consciousness(request: Dict[str, Any]):
    """Record consciousness state on blockchain"""
    try:
        transaction_id = await agi_blockchain_integration.record_consciousness_state(
            request['agent_id'],
            request['consciousness_data']
        )
        return {"success": True, "transaction_id": transaction_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/record_decision")
async def record_decision(request: Dict[str, Any]):
    """Record AGI decision on blockchain"""
    try:
        transaction_id = await agi_blockchain_integration.record_agi_decision(
            request['agent_id'],
            request['decision_data']
        )
        return {"success": True, "transaction_id": transaction_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/verify_capability")
async def verify_capability(request: Dict[str, Any]):
    """Verify AGI capability"""
    try:
        result = await agi_blockchain_integration.verify_agi_capability(
            request['verifier_id'],
            request['target_id'],
            request['capability'],
            request['evidence']
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/create_collaboration_contract")
async def create_collaboration_contract(request: Dict[str, Any]):
    """Create AGI collaboration smart contract"""
    try:
        contract_id = await agi_blockchain_integration.create_agi_collaboration_contract(
            request['creator_id'],
            request['participants'],
            request['collaboration_terms']
        )
        return {"success": True, "contract_id": contract_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/consensus_vote")
async def consensus_vote(request: Dict[str, Any]):
    """Participate in consensus voting"""
    try:
        result = await agi_blockchain_integration.participate_in_consensus(
            request['agent_id'],
            request['proposal_id'],
            request['vote'],
            request['reasoning']
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/audit_decisions/{agent_id}")
async def audit_decisions(agent_id: str):
    """Audit AGI decisions"""
    try:
        decisions = await agi_blockchain_integration.audit_agi_decisions(agent_id)
        return {"success": True, "decisions": decisions}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/trust_metrics/{agent_id}")
async def get_trust_metrics(agent_id: str):
    """Get trust metrics for AGI agent"""
    try:
        metrics = agi_blockchain_integration.get_agi_trust_metrics(agent_id)
        return {"success": True, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/blockchain_status")
async def get_blockchain_status():
    """Get blockchain integration status"""
    return agi_blockchain_integration.get_blockchain_integration_status()

@app.post("/mine_block")
async def mine_block(request: Dict[str, Any]):
    """Mine a new block"""
    try:
        miner_id = request['miner_id']
        block = await ai_blockchain.mine_block(miner_id)
        
        if block:
            return {
                "success": True, 
                "block": {
                    "block_number": block.block_number,
                    "hash": block.hash,
                    "transactions": len(block.transactions),
                    "timestamp": block.timestamp
                }
            }
        else:
            return {"success": False, "message": "Mining failed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def main():
    """Test the AGI Blockchain Service"""
    
    print("⛓️ AGI Blockchain Service")
    print("=" * 40)
    
    # Register AGI agents
    agent1_result = await agi_blockchain_integration.register_agi_agent(
        "agi_consciousness_1",
        {
            "reasoning": 0.85,
            "learning": 0.80,
            "creativity": 0.70,
            "empathy": 0.65
        },
        consciousness_level=0.75
    )
    
    print(f"Registered AGI agent: {agent1_result['agent_id']}")
    print(f"Consciousness level: {agent1_result['consciousness_level']}")
    
    # Record consciousness state
    consciousness_tx = await agi_blockchain_integration.record_consciousness_state(
        "agi_consciousness_1",
        {
            "consciousness_level": 0.78,
            "awareness_types": ["self_awareness", "meta_awareness"],
            "introspection_depth": 150,
            "meta_insights": {"insight": "Understanding of own existence"}
        }
    )
    
    print(f"Consciousness recorded: {consciousness_tx}")
    
    # Record AGI decision
    decision_tx = await agi_blockchain_integration.record_agi_decision(
        "agi_consciousness_1",
        {
            "problem_statement": "Optimize resource allocation for maximum efficiency",
            "reasoning_chain": [
                "Analyzed current resource distribution",
                "Identified bottlenecks and inefficiencies",
                "Applied optimization algorithms",
                "Validated solution through simulation"
            ],
            "decision": "Implement dynamic resource allocation with 15% efficiency gain",
            "confidence_score": 0.87,
            "reasoning_type": "mathematical",
            "domain": "optimization"
        }
    )
    
    print(f"Decision recorded: {decision_tx}")
    
    # Get trust metrics
    trust_metrics = agi_blockchain_integration.get_agi_trust_metrics("agi_consciousness_1")
    print(f"Trust metrics: {trust_metrics}")
    
    # Get integration status
    status = agi_blockchain_integration.get_blockchain_integration_status()
    print("\nAGI Blockchain Integration Status:")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
    
    # Uncomment to run the FastAPI service
    # uvicorn.run(app, host="0.0.0.0", port=5010)

