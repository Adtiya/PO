"""
Simplified Blockchain Core for AGI Integration Testing
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class TransactionType(Enum):
    """Types of blockchain transactions"""
    IDENTITY_REGISTRATION = "identity_registration"
    TRUST_VERIFICATION = "trust_verification"
    DECISION_RECORD = "decision_record"
    CONSENSUS_VOTE = "consensus_vote"
    SMART_CONTRACT = "smart_contract"
    CAPABILITY_VERIFICATION = "capability_verification"
    COLLABORATION = "collaboration"
    LEARNING_RECORD = "learning_record"

class ConsensusType(Enum):
    """Types of consensus mechanisms"""
    PROOF_OF_TRUST = "proof_of_trust"
    PROOF_OF_INTELLIGENCE = "proof_of_intelligence"
    PROOF_OF_CAPABILITY = "proof_of_capability"
    DELEGATED_CONSENSUS = "delegated_consensus"

@dataclass
class Transaction:
    """Blockchain transaction"""
    transaction_id: str
    transaction_type: TransactionType
    sender: str
    receiver: str
    data: Dict[str, Any]
    timestamp: float
    signature: str
    hash: str = ""
    
    def calculate_hash(self) -> str:
        """Calculate transaction hash"""
        content = f"{self.transaction_id}{self.sender}{self.receiver}{self.timestamp}{json.dumps(self.data, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()

@dataclass
class Block:
    """Blockchain block"""
    block_number: int
    previous_hash: str
    transactions: List[Transaction]
    timestamp: float
    nonce: int
    hash: str = ""
    
    def calculate_hash(self) -> str:
        """Calculate block hash"""
        transactions_hash = hashlib.sha256(
            json.dumps([asdict(tx) for tx in self.transactions], sort_keys=True).encode()
        ).hexdigest()
        content = f"{self.block_number}{self.previous_hash}{transactions_hash}{self.timestamp}{self.nonce}"
        return hashlib.sha256(content.encode()).hexdigest()

@dataclass
class AIIdentity:
    """AI agent identity on blockchain"""
    agent_id: str
    public_key: str
    capabilities: List[str]
    reputation_score: float
    registration_time: float
    metadata: Dict[str, Any]

class CryptoManager:
    """Simplified crypto manager"""
    
    def __init__(self):
        self.keys = {}
    
    def generate_keypair(self, agent_id: str) -> Dict[str, str]:
        """Generate keypair for agent"""
        # Simplified - in real implementation would use proper cryptography
        public_key = f"pub_{agent_id}_{int(time.time())}"
        private_key = f"priv_{agent_id}_{int(time.time())}"
        
        self.keys[agent_id] = {
            'public_key': public_key,
            'private_key': private_key
        }
        
        return self.keys[agent_id]
    
    def create_transaction_signature(self, agent_id: str, transaction: Transaction) -> str:
        """Create transaction signature"""
        # Simplified signature
        if agent_id in self.keys:
            content = f"{transaction.transaction_id}{transaction.sender}{transaction.receiver}"
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        return "unsigned"

class TrustNetwork:
    """Trust network for AI agents"""
    
    def __init__(self):
        self.trust_relationships = {}
        self.reputation_scores = {}
    
    def update_trust(self, verifier: str, target: str, interaction_result: Dict[str, Any]):
        """Update trust relationship"""
        if verifier not in self.trust_relationships:
            self.trust_relationships[verifier] = {}
        
        success = interaction_result.get('success', False)
        accuracy = interaction_result.get('accuracy', 0.5)
        
        current_trust = self.trust_relationships[verifier].get(target, 0.5)
        
        # Simple trust update
        if success:
            new_trust = min(1.0, current_trust + 0.1 * accuracy)
        else:
            new_trust = max(0.0, current_trust - 0.1)
        
        self.trust_relationships[verifier][target] = new_trust
        
        # Update reputation
        if target not in self.reputation_scores:
            self.reputation_scores[target] = 0.5
        
        self.reputation_scores[target] = (
            self.reputation_scores[target] * 0.9 + new_trust * 0.1
        )
    
    def get_reputation(self, agent_id: str) -> float:
        """Get agent reputation"""
        return self.reputation_scores.get(agent_id, 0.5)
    
    def calculate_network_trust(self, agent_id: str) -> float:
        """Calculate network-wide trust for agent"""
        if agent_id not in self.reputation_scores:
            return 0.5
        
        # Simple network trust calculation
        direct_trust = self.reputation_scores[agent_id]
        
        # Factor in trust from other agents
        indirect_trust = 0.5
        trust_count = 0
        
        for verifier, targets in self.trust_relationships.items():
            if agent_id in targets:
                indirect_trust += targets[agent_id]
                trust_count += 1
        
        if trust_count > 0:
            indirect_trust /= trust_count
        
        return (direct_trust * 0.7 + indirect_trust * 0.3)
    
    def find_trusted_agents(self, agent_id: str, min_trust: float = 0.7) -> List[str]:
        """Find agents trusted by given agent"""
        if agent_id not in self.trust_relationships:
            return []
        
        trusted = []
        for target, trust_level in self.trust_relationships[agent_id].items():
            if trust_level >= min_trust:
                trusted.append(target)
        
        return trusted

class AIBlockchain:
    """Main blockchain for AI agents"""
    
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.ai_identities = {}
        self.crypto_manager = CryptoManager()
        self.trust_network = TrustNetwork()
        self.smart_contracts = {}
        
        # Create genesis block
        self._create_genesis_block()
    
    def _create_genesis_block(self):
        """Create the genesis block"""
        genesis_block = Block(
            block_number=0,
            previous_hash="0",
            transactions=[],
            timestamp=time.time(),
            nonce=0
        )
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
    
    def register_ai_agent(self, agent_id: str, capabilities: List[str], 
                         metadata: Dict[str, Any] = None) -> AIIdentity:
        """Register AI agent on blockchain"""
        
        # Generate keypair
        keys = self.crypto_manager.generate_keypair(agent_id)
        
        # Create identity
        identity = AIIdentity(
            agent_id=agent_id,
            public_key=keys['public_key'],
            capabilities=capabilities,
            reputation_score=0.5,  # Starting reputation
            registration_time=time.time(),
            metadata=metadata or {}
        )
        
        self.ai_identities[agent_id] = identity
        
        # Create registration transaction
        registration_tx = Transaction(
            transaction_id=f"reg_{agent_id}_{int(time.time())}",
            transaction_type=TransactionType.IDENTITY_REGISTRATION,
            sender="system",
            receiver=agent_id,
            data={
                "agent_id": agent_id,
                "capabilities": capabilities,
                "public_key": keys['public_key'],
                "metadata": metadata
            },
            timestamp=time.time(),
            signature="system_signature"
        )
        
        registration_tx.hash = registration_tx.calculate_hash()
        self.add_transaction(registration_tx)
        
        return identity
    
    def add_transaction(self, transaction: Transaction):
        """Add transaction to pending pool"""
        if not transaction.hash:
            transaction.hash = transaction.calculate_hash()
        
        self.pending_transactions.append(transaction)
    
    def create_trust_verification_transaction(self, verifier_id: str, target_id: str, 
                                           verification_data: Dict[str, Any]) -> Transaction:
        """Create trust verification transaction"""
        
        transaction = Transaction(
            transaction_id=f"trust_{verifier_id}_{target_id}_{int(time.time())}",
            transaction_type=TransactionType.TRUST_VERIFICATION,
            sender=verifier_id,
            receiver=target_id,
            data=verification_data,
            timestamp=time.time(),
            signature=""
        )
        
        transaction.signature = self.crypto_manager.create_transaction_signature(verifier_id, transaction)
        transaction.hash = transaction.calculate_hash()
        
        return transaction
    
    def deploy_smart_contract(self, creator_id: str, contract_code: str, 
                            conditions: Dict[str, Any]) -> str:
        """Deploy smart contract"""
        
        contract_id = f"contract_{creator_id}_{int(time.time())}"
        
        contract = {
            'contract_id': contract_id,
            'creator': creator_id,
            'code': contract_code,
            'conditions': conditions,
            'state': 'deployed',
            'creation_time': time.time()
        }
        
        self.smart_contracts[contract_id] = contract
        
        # Create deployment transaction
        deployment_tx = Transaction(
            transaction_id=f"deploy_{contract_id}",
            transaction_type=TransactionType.SMART_CONTRACT,
            sender=creator_id,
            receiver="contract_network",
            data=contract,
            timestamp=time.time(),
            signature=""
        )
        
        deployment_tx.signature = self.crypto_manager.create_transaction_signature(creator_id, deployment_tx)
        self.add_transaction(deployment_tx)
        
        return contract_id
    
    async def mine_block(self, miner_id: str) -> Optional[Block]:
        """Mine a new block"""
        
        if not self.pending_transactions:
            return None
        
        # Get previous block
        previous_block = self.chain[-1]
        
        # Create new block
        new_block = Block(
            block_number=len(self.chain),
            previous_hash=previous_block.hash,
            transactions=self.pending_transactions.copy(),
            timestamp=time.time(),
            nonce=0
        )
        
        # Simple proof of work (in real implementation would be more sophisticated)
        while not new_block.calculate_hash().startswith("0"):
            new_block.nonce += 1
            if new_block.nonce > 1000:  # Limit for testing
                break
        
        new_block.hash = new_block.calculate_hash()
        
        # Add to chain
        self.chain.append(new_block)
        
        # Clear pending transactions
        self.pending_transactions = []
        
        return new_block
    
    def get_blockchain_status(self) -> Dict[str, Any]:
        """Get blockchain status"""
        
        return {
            'chain_length': len(self.chain),
            'pending_transactions': len(self.pending_transactions),
            'registered_agents': len(self.ai_identities),
            'smart_contracts': len(self.smart_contracts),
            'trust_relationships': len(self.trust_network.trust_relationships),
            'last_block_hash': self.chain[-1].hash if self.chain else None,
            'timestamp': time.time()
        }

# Global blockchain instance
ai_blockchain = AIBlockchain()

