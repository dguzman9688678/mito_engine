"""
MITO Engine - Advanced Memory Management System
Implements comprehensive AI memory with state recall, semantic routing, knowledge graphs, and vector search
"""

import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging
import os

@dataclass
class MemoryEntry:
    """Represents a single memory entry"""
    id: str
    content: str
    memory_type: str
    timestamp: str
    context: Dict[str, Any]
    importance: float
    access_count: int
    last_accessed: str
    tags: List[str]
    embedding: Optional[List[float]] = None

@dataclass
class SemanticRoute:
    """Represents a semantic routing pattern"""
    pattern: str
    intent: str
    confidence: float
    action: str
    parameters: Dict[str, Any]
    examples: List[str]

@dataclass
class KnowledgeNode:
    """Represents a node in the knowledge graph"""
    node_id: str
    concept: str
    content: str
    node_type: str
    connections: List[str]
    strength: float
    created_at: str
    updated_at: str

@dataclass
class IdentitySignature:
    """Represents AI identity and branding elements"""
    signature_id: str
    persona_name: str
    traits: List[str]
    communication_style: str
    expertise_domains: List[str]
    personalization_data: Dict[str, Any]
    security_hash: str
    created_at: str

class MemoryStore:
    """Core memory storage and retrieval system"""
    
    def __init__(self, store_path: str = "memory_store.json"):
        self.store_path = store_path
        self.memories: Dict[str, MemoryEntry] = {}
        self.load_memories()
        
    def load_memories(self):
        """Load memories from storage"""
        try:
            if os.path.exists(self.store_path):
                with open(self.store_path, 'r') as f:
                    data = json.load(f)
                    for memory_data in data.get('memories', []):
                        memory = MemoryEntry(**memory_data)
                        self.memories[memory.id] = memory
        except Exception as e:
            logging.error(f"Error loading memories: {e}")
            
    def save_memories(self):
        """Save memories to storage"""
        try:
            data = {
                'memories': [asdict(memory) for memory in self.memories.values()],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.store_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving memories: {e}")
            
    def store_memory(self, content: str, memory_type: str, context: Dict[str, Any], 
                    importance: float = 0.5, tags: List[str] = None) -> str:
        """Store new memory"""
        memory_id = str(uuid.uuid4())
        memory = MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now().isoformat(),
            context=context or {},
            importance=importance,
            access_count=0,
            last_accessed=datetime.now().isoformat(),
            tags=tags or []
        )
        
        self.memories[memory_id] = memory
        self.save_memories()
        return memory_id
        
    def recall_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Recall specific memory by ID"""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            memory.access_count += 1
            memory.last_accessed = datetime.now().isoformat()
            self.save_memories()
            return memory
        return None
        
    def search_memories(self, query: str, memory_type: str = None, 
                       limit: int = 10) -> List[MemoryEntry]:
        """Search memories by content and type"""
        results = []
        query_lower = query.lower()
        
        for memory in self.memories.values():
            if memory_type and memory.memory_type != memory_type:
                continue
                
            if query_lower in memory.content.lower():
                results.append(memory)
                
        # Sort by importance and recency
        results.sort(key=lambda m: (m.importance, m.access_count), reverse=True)
        return results[:limit]

class SemanticRouter:
    """Natural language understanding and routing system"""
    
    def __init__(self, index_path: str = "semantic_index.json"):
        self.index_path = index_path
        self.routes: List[SemanticRoute] = []
        self.model = None
        self.load_routes()
        self.initialize_model()
        
    def initialize_model(self):
        """Initialize simple text similarity model using TF-IDF"""
        self.model = True  # Simple flag for model availability
            
    def load_routes(self):
        """Load semantic routes from storage"""
        try:
            if os.path.exists(self.index_path):
                with open(self.index_path, 'r') as f:
                    data = json.load(f)
                    for route_data in data.get('routes', []):
                        route = SemanticRoute(**route_data)
                        self.routes.append(route)
        except Exception as e:
            logging.error(f"Error loading routes: {e}")
            
    def save_routes(self):
        """Save routes to storage"""
        try:
            data = {
                'routes': [asdict(route) for route in self.routes],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.index_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving routes: {e}")
            
    def add_route(self, pattern: str, intent: str, action: str, 
                 parameters: Dict[str, Any] = None, examples: List[str] = None):
        """Add new semantic route"""
        route = SemanticRoute(
            pattern=pattern,
            intent=intent,
            confidence=0.0,
            action=action,
            parameters=parameters or {},
            examples=examples or []
        )
        self.routes.append(route)
        self.save_routes()
        
    def route_message(self, message: str) -> Optional[SemanticRoute]:
        """Route message to appropriate handler"""
        if not self.model:
            return None
            
        message_embedding = self.model.encode([message])
        best_route = None
        best_score = 0.0
        
        for route in self.routes:
            # Calculate similarity with pattern and examples
            route_texts = [route.pattern] + route.examples
            route_embeddings = self.model.encode(route_texts)
            
            similarities = np.dot(message_embedding, route_embeddings.T).flatten()
            max_similarity = np.max(similarities)
            
            if max_similarity > best_score:
                best_score = max_similarity
                best_route = route
                
        if best_route and best_score > 0.7:  # Confidence threshold
            best_route.confidence = best_score
            return best_route
            
        return None

class KnowledgeGraph:
    """Contextual knowledge graph for concept linking"""
    
    def __init__(self, graph_path: str = "knowledge_graph.json"):
        self.graph_path = graph_path
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.connections: Dict[str, List[str]] = defaultdict(list)
        self.load_graph()
        
    def load_graph(self):
        """Load knowledge graph from storage"""
        try:
            if os.path.exists(self.graph_path):
                with open(self.graph_path, 'r') as f:
                    data = json.load(f)
                    for node_data in data.get('nodes', []):
                        node = KnowledgeNode(**node_data)
                        self.nodes[node.node_id] = node
                        
                    self.connections = defaultdict(list, data.get('connections', {}))
        except Exception as e:
            logging.error(f"Error loading knowledge graph: {e}")
            
    def save_graph(self):
        """Save knowledge graph to storage"""
        try:
            data = {
                'nodes': [asdict(node) for node in self.nodes.values()],
                'connections': dict(self.connections),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.graph_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving knowledge graph: {e}")
            
    def add_node(self, concept: str, content: str, node_type: str = "concept") -> str:
        """Add new knowledge node"""
        node_id = str(uuid.uuid4())
        node = KnowledgeNode(
            node_id=node_id,
            concept=concept,
            content=content,
            node_type=node_type,
            connections=[],
            strength=1.0,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.nodes[node_id] = node
        self.save_graph()
        return node_id
        
    def connect_nodes(self, node1_id: str, node2_id: str, strength: float = 1.0):
        """Create connection between nodes"""
        if node1_id in self.nodes and node2_id in self.nodes:
            self.connections[node1_id].append(node2_id)
            self.connections[node2_id].append(node1_id)
            
            self.nodes[node1_id].connections.append(node2_id)
            self.nodes[node2_id].connections.append(node1_id)
            self.save_graph()
            
    def find_related_concepts(self, concept: str, depth: int = 2) -> List[KnowledgeNode]:
        """Find concepts related to given concept"""
        related_nodes = []
        
        # Find nodes matching concept
        matching_nodes = [node for node in self.nodes.values() 
                         if concept.lower() in node.concept.lower()]
        
        # Traverse connections
        for node in matching_nodes:
            visited = set()
            queue = [(node.node_id, 0)]
            
            while queue and len(related_nodes) < 20:
                current_id, current_depth = queue.pop(0)
                
                if current_id in visited or current_depth > depth:
                    continue
                    
                visited.add(current_id)
                if current_id != node.node_id:
                    related_nodes.append(self.nodes[current_id])
                    
                for connected_id in self.connections.get(current_id, []):
                    if connected_id not in visited:
                        queue.append((connected_id, current_depth + 1))
                        
        return related_nodes

class IdentityManager:
    """AI identity and personalization management"""
    
    def __init__(self, signature_path: str = "identity_signature.json"):
        self.signature_path = signature_path
        self.signatures: Dict[str, IdentitySignature] = {}
        self.load_signatures()
        
    def load_signatures(self):
        """Load identity signatures from storage"""
        try:
            if os.path.exists(self.signature_path):
                with open(self.signature_path, 'r') as f:
                    data = json.load(f)
                    for sig_data in data.get('signatures', []):
                        signature = IdentitySignature(**sig_data)
                        self.signatures[signature.signature_id] = signature
        except Exception as e:
            logging.error(f"Error loading identity signatures: {e}")
            
    def save_signatures(self):
        """Save identity signatures to storage"""
        try:
            data = {
                'signatures': [asdict(sig) for sig in self.signatures.values()],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.signature_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving identity signatures: {e}")
            
    def create_signature(self, persona_name: str, traits: List[str], 
                        communication_style: str, expertise_domains: List[str],
                        personalization_data: Dict[str, Any] = None) -> str:
        """Create new identity signature"""
        signature_id = str(uuid.uuid4())
        
        # Generate security hash
        hash_content = f"{persona_name}:{traits}:{communication_style}:{datetime.now().isoformat()}"
        security_hash = hashlib.sha256(hash_content.encode()).hexdigest()
        
        signature = IdentitySignature(
            signature_id=signature_id,
            persona_name=persona_name,
            traits=traits,
            communication_style=communication_style,
            expertise_domains=expertise_domains,
            personalization_data=personalization_data or {},
            security_hash=security_hash,
            created_at=datetime.now().isoformat()
        )
        
        self.signatures[signature_id] = signature
        self.save_signatures()
        return signature_id
        
    def get_signature(self, signature_id: str) -> Optional[IdentitySignature]:
        """Get identity signature by ID"""
        return self.signatures.get(signature_id)
        
    def update_personalization(self, signature_id: str, 
                             personalization_data: Dict[str, Any]):
        """Update personalization data for signature"""
        if signature_id in self.signatures:
            self.signatures[signature_id].personalization_data.update(personalization_data)
            self.save_signatures()

class CommandLogger:
    """Forensics, audit, and journaling system"""
    
    def __init__(self, log_path: str = "command_log.jsonl"):
        self.log_path = log_path
        
    def log_command(self, command: str, user_id: str, context: Dict[str, Any],
                   result: Any = None, success: bool = True):
        """Log command execution for audit trail"""
        log_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'user_id': user_id,
            'context': context,
            'result': str(result) if result else None,
            'success': success,
            'session_id': context.get('session_id'),
            'ip_address': context.get('ip_address'),
            'user_agent': context.get('user_agent')
        }
        
        try:
            with jsonlines.open(self.log_path, mode='a') as writer:
                writer.write(log_entry)
        except Exception as e:
            logging.error(f"Error logging command: {e}")
            
    def get_audit_trail(self, user_id: str = None, start_date: datetime = None,
                       end_date: datetime = None, limit: int = 100) -> List[Dict]:
        """Retrieve audit trail with filtering"""
        entries = []
        
        try:
            if not os.path.exists(self.log_path):
                return entries
                
            with jsonlines.open(self.log_path) as reader:
                for entry in reader:
                    # Apply filters
                    if user_id and entry.get('user_id') != user_id:
                        continue
                        
                    entry_time = datetime.fromisoformat(entry['timestamp'])
                    if start_date and entry_time < start_date:
                        continue
                    if end_date and entry_time > end_date:
                        continue
                        
                    entries.append(entry)
                    
                    if len(entries) >= limit:
                        break
                        
        except Exception as e:
            logging.error(f"Error reading audit trail: {e}")
            
        return entries

class VectorMemory:
    """Deep search and concept matching with vector embeddings"""
    
    def __init__(self, vector_path: str = "vector_memory.json"):
        self.vector_path = vector_path
        self.vectors: Dict[str, Dict[str, Any]] = {}
        self.model = None
        self.index = None
        self.id_mapping: List[str] = []
        self.load_vectors()
        self.initialize_model()
        
    def initialize_model(self):
        """Initialize sentence transformer and FAISS index"""
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.rebuild_index()
        except Exception as e:
            logging.error(f"Error initializing vector model: {e}")
            
    def load_vectors(self):
        """Load vector memories from storage"""
        try:
            if os.path.exists(self.vector_path):
                with open(self.vector_path, 'r') as f:
                    self.vectors = json.load(f)
        except Exception as e:
            logging.error(f"Error loading vectors: {e}")
            
    def save_vectors(self):
        """Save vector memories to storage"""
        try:
            with open(self.vector_path, 'w') as f:
                json.dump(self.vectors, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving vectors: {e}")
            
    def store_vector_memory(self, content: str, memory_type: str, 
                           metadata: Dict[str, Any] = None) -> str:
        """Store content with vector embedding"""
        if not self.model:
            return None
            
        memory_id = str(uuid.uuid4())
        embedding = self.model.encode([content])[0].tolist()
        
        vector_entry = {
            'id': memory_id,
            'content': content,
            'memory_type': memory_type,
            'embedding': embedding,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'access_count': 0
        }
        
        self.vectors[memory_id] = vector_entry
        self.save_vectors()
        self.rebuild_index()
        return memory_id
        
    def rebuild_index(self):
        """Rebuild FAISS index with current vectors"""
        if not self.vectors or not self.model:
            return
            
        embeddings = []
        self.id_mapping = []
        
        for memory_id, vector_data in self.vectors.items():
            embeddings.append(vector_data['embedding'])
            self.id_mapping.append(memory_id)
            
        if embeddings:
            embeddings_array = np.array(embeddings, dtype=np.float32)
            dimension = embeddings_array.shape[1]
            
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
            self.index.add(embeddings_array)
            
    def search_similar(self, query: str, k: int = 10, 
                      memory_type: str = None) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity"""
        if not self.model or not self.index:
            return []
            
        query_embedding = self.model.encode([query])
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.id_mapping):
                memory_id = self.id_mapping[idx]
                vector_data = self.vectors[memory_id]
                
                # Filter by memory type if specified
                if memory_type and vector_data.get('memory_type') != memory_type:
                    continue
                    
                # Update access count
                vector_data['access_count'] += 1
                
                results.append({
                    'id': memory_id,
                    'content': vector_data['content'],
                    'memory_type': vector_data['memory_type'],
                    'metadata': vector_data['metadata'],
                    'similarity_score': float(score),
                    'access_count': vector_data['access_count']
                })
                
        self.save_vectors()
        return results

class AdvancedMemorySystem:
    """Unified advanced memory management system"""
    
    def __init__(self):
        self.memory_store = MemoryStore()
        self.semantic_router = SemanticRouter()
        self.knowledge_graph = KnowledgeGraph()
        self.identity_manager = IdentityManager()
        self.command_logger = CommandLogger()
        self.vector_memory = VectorMemory()
        
        # Initialize default components
        self.initialize_default_routes()
        self.initialize_default_identity()
        
    def initialize_default_routes(self):
        """Set up default semantic routes"""
        default_routes = [
            {
                'pattern': 'create project',
                'intent': 'project_creation',
                'action': 'create_new_project',
                'examples': ['make a new project', 'start project', 'begin new project']
            },
            {
                'pattern': 'search files',
                'intent': 'file_search',
                'action': 'search_filesystem',
                'examples': ['find files', 'locate file', 'search for file']
            },
            {
                'pattern': 'run command',
                'intent': 'terminal_execution',
                'action': 'execute_terminal_command',
                'examples': ['execute command', 'run in terminal', 'terminal command']
            },
            {
                'pattern': 'deploy application',
                'intent': 'deployment',
                'action': 'deploy_to_platform',
                'examples': ['deploy app', 'publish application', 'launch deployment']
            }
        ]
        
        for route_data in default_routes:
            self.semantic_router.add_route(**route_data)
            
    def initialize_default_identity(self):
        """Set up default MITO identity signature"""
        self.identity_manager.create_signature(
            persona_name="MITO Engine Assistant",
            traits=[
                "intelligent",
                "helpful",
                "efficient",
                "professional",
                "adaptive",
                "security-conscious"
            ],
            communication_style="professional_friendly",
            expertise_domains=[
                "software_development",
                "ai_integration",
                "project_management",
                "database_operations",
                "deployment_automation"
            ],
            personalization_data={
                "creator": "Daniel Guzman",
                "contact": "guzman.danield@outlook.com",
                "version": "1.2.0",
                "capabilities": [
                    "code_generation",
                    "file_management",
                    "terminal_operations",
                    "database_queries",
                    "project_deployment"
                ]
            }
        )
        
    def process_user_input(self, user_input: str, user_id: str, 
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user input through complete memory system"""
        
        # Log the command
        self.command_logger.log_command(
            command=user_input,
            user_id=user_id,
            context=context
        )
        
        # Route the message semantically
        route = self.semantic_router.route_message(user_input)
        
        # Store the interaction in memory
        memory_id = self.memory_store.store_memory(
            content=user_input,
            memory_type="user_interaction",
            context=context,
            importance=0.7,
            tags=["user_input", "interaction"]
        )
        
        # Store in vector memory for semantic search
        vector_id = self.vector_memory.store_vector_memory(
            content=user_input,
            memory_type="user_interaction",
            metadata={
                'user_id': user_id,
                'memory_id': memory_id,
                'context': context
            }
        )
        
        # Find related concepts in knowledge graph
        related_concepts = self.knowledge_graph.find_related_concepts(user_input)
        
        # Search for similar past interactions
        similar_memories = self.vector_memory.search_similar(
            query=user_input,
            k=5,
            memory_type="user_interaction"
        )
        
        return {
            'route': asdict(route) if route else None,
            'memory_id': memory_id,
            'vector_id': vector_id,
            'related_concepts': [asdict(concept) for concept in related_concepts],
            'similar_memories': similar_memories,
            'processing_timestamp': datetime.now().isoformat()
        }
        
    def get_memory_analytics(self) -> Dict[str, Any]:
        """Get comprehensive memory system analytics"""
        return {
            'memory_store': {
                'total_memories': len(self.memory_store.memories),
                'memory_types': list(set(m.memory_type for m in self.memory_store.memories.values())),
                'average_importance': np.mean([m.importance for m in self.memory_store.memories.values()]) if self.memory_store.memories else 0
            },
            'semantic_router': {
                'total_routes': len(self.semantic_router.routes),
                'route_intents': list(set(r.intent for r in self.semantic_router.routes))
            },
            'knowledge_graph': {
                'total_nodes': len(self.knowledge_graph.nodes),
                'total_connections': sum(len(connections) for connections in self.knowledge_graph.connections.values()),
                'node_types': list(set(n.node_type for n in self.knowledge_graph.nodes.values()))
            },
            'identity_manager': {
                'total_signatures': len(self.identity_manager.signatures)
            },
            'vector_memory': {
                'total_vectors': len(self.vector_memory.vectors),
                'index_size': self.vector_memory.index.ntotal if self.vector_memory.index else 0
            }
        }

def main():
    """Demo of advanced memory system"""
    print("Initializing MITO Advanced Memory System...")
    
    memory_system = AdvancedMemorySystem()
    
    # Test user interaction processing
    test_context = {
        'session_id': 'test_session_123',
        'ip_address': '127.0.0.1',
        'user_agent': 'MITO Engine Test'
    }
    
    result = memory_system.process_user_input(
        user_input="Create a new Python web application project",
        user_id="test_user",
        context=test_context
    )
    
    print("Processing Result:")
    print(json.dumps(result, indent=2))
    
    # Get analytics
    analytics = memory_system.get_memory_analytics()
    print("\nMemory System Analytics:")
    print(json.dumps(analytics, indent=2))

if __name__ == "__main__":
    main()