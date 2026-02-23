"""
Knowledge Graph - Project 4.1
Simple knowledge graph extraction and visualization.
"""

import json
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

from anthropic import Anthropic

from knowledge_base import KnowledgeBase


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    id: str
    label: str
    type: str  # "concept", "entity", "document"
    metadata: dict = field(default_factory=dict)


@dataclass  
class GraphEdge:
    """An edge connecting two nodes."""
    source: str
    target: str
    relationship: str
    weight: float = 1.0


@dataclass
class KnowledgeGraph:
    """A knowledge graph with nodes and edges."""
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "nodes": [
                {"id": n.id, "label": n.label, "type": n.type, **n.metadata}
                for n in self.nodes
            ],
            "edges": [
                {"source": e.source, "target": e.target, 
                 "relationship": e.relationship, "weight": e.weight}
                for e in self.edges
            ]
        }
    
    def to_vis_js(self) -> dict:
        """Convert to vis.js network format."""
        # Color mapping for node types
        colors = {
            "document": "#4CAF50",
            "concept": "#2196F3",
            "entity": "#FF9800",
            "topic": "#9C27B0"
        }
        
        nodes = []
        for node in self.nodes:
            nodes.append({
                "id": node.id,
                "label": node.label,
                "color": colors.get(node.type, "#666666"),
                "title": f"{node.type}: {node.label}",
                "shape": "dot" if node.type == "concept" else "box",
                "size": 20 if node.type == "document" else 15
            })
        
        edges = []
        for edge in self.edges:
            edges.append({
                "from": edge.source,
                "to": edge.target,
                "label": edge.relationship,
                "arrows": "to",
                "width": edge.weight * 2
            })
        
        return {"nodes": nodes, "edges": edges}
    
    def to_mermaid(self) -> str:
        """Convert to Mermaid diagram format."""
        lines = ["graph TD"]
        
        # Add nodes with styling
        for node in self.nodes:
            safe_id = node.id.replace("-", "_").replace(" ", "_")
            if node.type == "document":
                lines.append(f'    {safe_id}["{node.label}"]')
            elif node.type == "concept":
                lines.append(f'    {safe_id}(("{node.label}"))')
            else:
                lines.append(f'    {safe_id}("{node.label}")')
        
        # Add edges
        for edge in self.edges:
            src = edge.source.replace("-", "_").replace(" ", "_")
            tgt = edge.target.replace("-", "_").replace(" ", "_")
            lines.append(f'    {src} -->|{edge.relationship}| {tgt}')
        
        return "\n".join(lines)


class KnowledgeGraphExtractor:
    """
    Extract knowledge graphs from documents using LLM.
    """
    
    EXTRACTION_PROMPT = """Extract a knowledge graph from the following text.

Identify:
1. Key concepts and entities
2. Relationships between them
3. Document topics

OUTPUT FORMAT (JSON only, no other text):
{
    "nodes": [
        {"id": "concept_1", "label": "Machine Learning", "type": "concept"},
        {"id": "entity_1", "label": "Python", "type": "entity"}
    ],
    "edges": [
        {"source": "concept_1", "target": "entity_1", "relationship": "uses", "weight": 0.8}
    ]
}

Node types: concept, entity, topic
Keep it focused - max 10 nodes and 15 edges.
Relationship labels should be short verbs/phrases."""
    
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic()
        self.model = model
    
    def extract_from_text(self, text: str, document_name: str = "") -> KnowledgeGraph:
        """Extract knowledge graph from text."""
        # Truncate if too long
        if len(text) > 4000:
            text = text[:4000] + "\n[... truncated ...]"
        
        prompt = f"""Document: {document_name}

Text:
{text}

Extract the knowledge graph as JSON."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=self.EXTRACTION_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text
        
        try:
            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            
            nodes = [
                GraphNode(
                    id=n["id"],
                    label=n["label"],
                    type=n.get("type", "concept")
                )
                for n in data.get("nodes", [])
            ]
            
            edges = [
                GraphEdge(
                    source=e["source"],
                    target=e["target"],
                    relationship=e.get("relationship", "related"),
                    weight=e.get("weight", 1.0)
                )
                for e in data.get("edges", [])
            ]
            
            return KnowledgeGraph(nodes=nodes, edges=edges)
            
        except (json.JSONDecodeError, KeyError, TypeError):
            return KnowledgeGraph()
    
    def extract_from_kb(
        self,
        kb: KnowledgeBase,
        include_documents: bool = True,
        max_documents: int = 10
    ) -> KnowledgeGraph:
        """
        Extract a knowledge graph from the entire knowledge base.
        
        Args:
            kb: Knowledge base to analyze
            include_documents: Add document nodes
            max_documents: Max documents to process
        """
        all_nodes = []
        all_edges = []
        node_ids = set()
        
        documents = kb.list_documents()[:max_documents]
        
        for doc_info in documents:
            doc_id = doc_info["id"]
            doc_name = doc_info["name"]
            
            # Add document node
            if include_documents:
                doc_node_id = f"doc_{doc_id[:8]}"
                all_nodes.append(GraphNode(
                    id=doc_node_id,
                    label=doc_name,
                    type="document"
                ))
                node_ids.add(doc_node_id)
            
            # Get document chunks
            chunks = kb.get_document_chunks(doc_id)
            
            if chunks:
                # Combine chunks for analysis (limit size)
                combined = "\n".join([c.content for c in chunks[:5]])
                
                # Extract graph from this document
                doc_graph = self.extract_from_text(combined, doc_name)
                
                # Merge into main graph
                for node in doc_graph.nodes:
                    # Avoid duplicates by checking label
                    existing = [n for n in all_nodes if n.label.lower() == node.label.lower()]
                    if not existing:
                        all_nodes.append(node)
                        node_ids.add(node.id)
                        
                        # Connect to document
                        if include_documents:
                            all_edges.append(GraphEdge(
                                source=f"doc_{doc_id[:8]}",
                                target=node.id,
                                relationship="contains",
                                weight=0.5
                            ))
                
                for edge in doc_graph.edges:
                    if edge.source in node_ids and edge.target in node_ids:
                        all_edges.append(edge)
        
        return KnowledgeGraph(nodes=all_nodes, edges=all_edges)


class DocumentSimilarityGraph:
    """
    Create a graph showing document similarities.
    """
    
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
    
    def build(self, similarity_threshold: float = 0.3) -> KnowledgeGraph:
        """
        Build a similarity graph between documents.
        
        Documents are connected if they share similar content.
        """
        nodes = []
        edges = []
        
        documents = self.kb.list_documents()
        
        # Create document nodes
        doc_ids = []
        for doc in documents:
            node_id = f"doc_{doc['id'][:8]}"
            doc_ids.append((doc["id"], node_id))
            
            nodes.append(GraphNode(
                id=node_id,
                label=doc["name"],
                type="document",
                metadata={
                    "chunks": doc.get("chunk_count", 0),
                    "type": doc.get("type", "unknown")
                }
            ))
        
        # Find similarities between documents
        for i, (doc_id_1, node_id_1) in enumerate(doc_ids):
            chunks_1 = self.kb.get_document_chunks(doc_id_1)
            
            if not chunks_1:
                continue
            
            # Use first chunk as representative
            query = chunks_1[0].content[:500]
            
            # Search for similar content
            results = self.kb.search(query, n_results=len(doc_ids))
            
            for result in results:
                other_doc_id = result.chunk.document_id
                
                # Find the node for this document
                other_node = next(
                    (nid for did, nid in doc_ids if did == other_doc_id),
                    None
                )
                
                if other_node and other_node != node_id_1:
                    # Check if edge already exists
                    existing = [
                        e for e in edges
                        if (e.source == node_id_1 and e.target == other_node) or
                           (e.source == other_node and e.target == node_id_1)
                    ]
                    
                    if not existing and result.score > similarity_threshold:
                        edges.append(GraphEdge(
                            source=node_id_1,
                            target=other_node,
                            relationship="similar",
                            weight=result.score
                        ))
        
        return KnowledgeGraph(nodes=nodes, edges=edges)


if __name__ == "__main__":
    # Test
    extractor = KnowledgeGraphExtractor()
    
    test_text = """
    Machine learning is a subset of artificial intelligence that enables 
    computers to learn from data. Python is the most popular language for 
    machine learning, with libraries like TensorFlow and PyTorch being widely used.
    
    Deep learning, a type of machine learning, uses neural networks with 
    multiple layers. Convolutional Neural Networks (CNNs) are commonly used 
    for image recognition, while Recurrent Neural Networks (RNNs) excel at 
    sequential data like text.
    """
    
    graph = extractor.extract_from_text(test_text, "ML Overview")
    
    print("Nodes:")
    for node in graph.nodes:
        print(f"  - {node.label} ({node.type})")
    
    print("\nEdges:")
    for edge in graph.edges:
        print(f"  - {edge.source} --{edge.relationship}--> {edge.target}")
    
    print("\nMermaid diagram:")
    print(graph.to_mermaid())
