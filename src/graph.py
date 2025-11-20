"""
Campus Graph Module

This module implements the core graph data structure for the Campus Navigator
using adjacency lists with weighted edges for optimal pathfinding.
"""

from typing import Dict, List, Set, Tuple, Optional
import json


class Node:
    """Represents a node (location) in the campus graph."""
    
    def __init__(self, node_id: str, name: str, coordinates: Tuple[float, float] = (0.0, 0.0), 
                 node_type: str = "general", description: str = ""):
        """
        Initialize a graph node.
        
        Args:
            node_id: Unique identifier for the node
            name: Human-readable name of the location
            coordinates: (x, y) coordinates for visualization
            node_type: Type of location (building, landmark, entrance, etc.)
            description: Additional description of the location
        """
        self.node_id = node_id
        self.name = name
        self.coordinates = coordinates
        self.node_type = node_type
        self.description = description
        
    def __str__(self) -> str:
        return f"Node({self.node_id}: {self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Node):
            return self.node_id == other.node_id
        return False
    
    def __hash__(self) -> int:
        return hash(self.node_id)


class Edge:
    """Represents a weighted edge between two nodes."""
    
    def __init__(self, from_node: str, to_node: str, weight: float, 
                 edge_type: str = "path", description: str = ""):
        """
        Initialize a graph edge.
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
            weight: Weight of the edge (distance, time, etc.)
            edge_type: Type of connection (walkway, road, stairs, etc.)
            description: Additional description of the path
        """
        if weight < 0:
            raise ValueError("Edge weight cannot be negative")
            
        self.from_node = from_node
        self.to_node = to_node
        self.weight = weight
        self.edge_type = edge_type
        self.description = description
    
    def __str__(self) -> str:
        return f"Edge({self.from_node} -> {self.to_node}, weight: {self.weight})"
    
    def __repr__(self) -> str:
        return self.__str__()


class CampusGraph:
    """
    Optimized graph implementation using adjacency lists for campus navigation.
    
    This class provides efficient storage and retrieval of campus locations and
    their connections, optimized for pathfinding algorithms.
    """
    
    def __init__(self):
        """Initialize an empty campus graph."""
        self.nodes: Dict[str, Node] = {}
        self.adjacency_list: Dict[str, List[Edge]] = {}
        self._node_lookup: Dict[str, str] = {}  # name -> node_id mapping for fast lookup
        
    def add_node(self, node: Node) -> bool:
        """
        Add a node to the graph.
        
        Args:
            node: The node to add
            
        Returns:
            bool: True if node was added, False if it already exists
        """
        if node.node_id in self.nodes:
            return False
            
        self.nodes[node.node_id] = node
        self.adjacency_list[node.node_id] = []
        self._node_lookup[node.name.lower()] = node.node_id
        return True
    
    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node and all its connections from the graph.
        
        Args:
            node_id: ID of the node to remove
            
        Returns:
            bool: True if node was removed, False if it didn't exist
        """
        if node_id not in self.nodes:
            return False
        
        # Remove from lookup
        node_name = self.nodes[node_id].name.lower()
        if node_name in self._node_lookup:
            del self._node_lookup[node_name]
        
        # Remove all edges pointing to this node
        for neighbor_id in self.adjacency_list:
            self.adjacency_list[neighbor_id] = [
                edge for edge in self.adjacency_list[neighbor_id]
                if edge.to_node != node_id
            ]
        
        # Remove the node itself
        del self.nodes[node_id]
        del self.adjacency_list[node_id]
        return True
    
    def add_edge(self, edge: Edge) -> bool:
        """
        Add an edge to the graph.
        
        Args:
            edge: The edge to add
            
        Returns:
            bool: True if edge was added successfully
            
        Raises:
            ValueError: If either node doesn't exist
        """
        if edge.from_node not in self.nodes:
            raise ValueError(f"Source node '{edge.from_node}' does not exist")
        if edge.to_node not in self.nodes:
            raise ValueError(f"Destination node '{edge.to_node}' does not exist")
        
        # Check if edge already exists
        for existing_edge in self.adjacency_list[edge.from_node]:
            if existing_edge.to_node == edge.to_node:
                # Update existing edge
                existing_edge.weight = edge.weight
                existing_edge.edge_type = edge.edge_type
                existing_edge.description = edge.description
                return True
        
        # Add new edge
        self.adjacency_list[edge.from_node].append(edge)
        return True
    
    def add_bidirectional_edge(self, node1: str, node2: str, weight: float,
                             edge_type: str = "path", description: str = "") -> bool:
        """
        Add a bidirectional edge between two nodes.
        
        Args:
            node1: First node ID
            node2: Second node ID
            weight: Weight of the edge
            edge_type: Type of connection
            description: Description of the path
            
        Returns:
            bool: True if both edges were added successfully
        """
        edge1 = Edge(node1, node2, weight, edge_type, description)
        edge2 = Edge(node2, node1, weight, edge_type, description)
        
        success1 = self.add_edge(edge1)
        success2 = self.add_edge(edge2)
        
        return success1 and success2
    
    def get_neighbors(self, node_id: str) -> List[Tuple[str, float]]:
        """
        Get all neighbors of a node with their weights.
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of (neighbor_id, weight) tuples
        """
        if node_id not in self.adjacency_list:
            return []
        
        return [(edge.to_node, edge.weight) for edge in self.adjacency_list[node_id]]
    
    def get_edge_info(self, from_node: str, to_node: str) -> Optional[Edge]:
        """
        Get detailed information about an edge.
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
            
        Returns:
            Edge object if found, None otherwise
        """
        if from_node not in self.adjacency_list:
            return None
        
        for edge in self.adjacency_list[from_node]:
            if edge.to_node == to_node:
                return edge
        
        return None
    
    def node_exists(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self.nodes
    
    def find_node_by_name(self, name: str) -> Optional[str]:
        """
        Find a node ID by its name (case-insensitive).
        
        Args:
            name: Name to search for
            
        Returns:
            Node ID if found, None otherwise
        """
        return self._node_lookup.get(name.lower())
    
    def get_all_nodes(self) -> List[Node]:
        """Get all nodes in the graph."""
        return list(self.nodes.values())
    
    def get_node_count(self) -> int:
        """Get the total number of nodes."""
        return len(self.nodes)
    
    def get_edge_count(self) -> int:
        """Get the total number of edges."""
        return sum(len(edges) for edges in self.adjacency_list.values())
    
    def get_graph_stats(self) -> Dict:
        """
        Get comprehensive statistics about the graph.
        
        Returns:
            Dictionary containing various graph metrics
        """
        total_weight = sum(
            edge.weight for edges in self.adjacency_list.values()
            for edge in edges
        )
        
        node_types = {}
        for node in self.nodes.values():
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
        
        edge_types = {}
        for edges in self.adjacency_list.values():
            for edge in edges:
                edge_types[edge.edge_type] = edge_types.get(edge.edge_type, 0) + 1
        
        return {
            'total_nodes': self.get_node_count(),
            'total_edges': self.get_edge_count(),
            'total_weight': total_weight,
            'avg_degree': self.get_edge_count() / max(self.get_node_count(), 1),
            'node_types': node_types,
            'edge_types': edge_types
        }
    
    def validate_graph(self) -> List[str]:
        """
        Validate the graph for consistency and return any issues found.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check for orphaned nodes
        for node_id in self.nodes:
            if node_id not in self.adjacency_list:
                errors.append(f"Node '{node_id}' has no adjacency list entry")
        
        # Check for broken edges
        for from_node, edges in self.adjacency_list.items():
            if from_node not in self.nodes:
                errors.append(f"Adjacency list contains unknown node '{from_node}'")
            
            for edge in edges:
                if edge.to_node not in self.nodes:
                    errors.append(f"Edge points to unknown node '{edge.to_node}'")
                if edge.weight < 0:
                    errors.append(f"Negative weight edge: {edge}")
        
        return errors
    
    def __str__(self) -> str:
        return f"CampusGraph({self.get_node_count()} nodes, {self.get_edge_count()} edges)"
    
    def __repr__(self) -> str:
        return self.__str__()