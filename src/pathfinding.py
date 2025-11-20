"""
Pathfinding Module - Optimized Dijkstra's Algorithm Implementation

This module provides an efficient implementation of Dijkstra's algorithm
with advanced optimizations for campus navigation pathfinding.
"""

import heapq
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from graph import CampusGraph, Node


class PathfindingError(Exception):
    """Custom exception for pathfinding errors."""
    pass


class RoutePreference(Enum):
    """Enumeration of different route preferences."""
    SHORTEST_DISTANCE = "distance"
    FASTEST_TIME = "time"
    ACCESSIBILITY = "accessible"
    SCENIC = "scenic"


@dataclass
class PathInfo:
    """Container for detailed path information."""
    nodes: List[str]
    total_distance: float
    total_time: float
    path_description: List[str]
    warnings: List[str]
    route_type: str


@dataclass
class RouteOptions:
    """Configuration options for route calculation."""
    preference: RoutePreference = RoutePreference.SHORTEST_DISTANCE
    avoid_stairs: bool = False
    avoid_construction: bool = True
    max_detour_factor: float = 1.5
    include_indoor_paths: bool = True


class PriorityQueue:
    """
    Optimized priority queue implementation using binary heap
    with improved performance for Dijkstra's algorithm.
    """
    
    def __init__(self):
        """Initialize empty priority queue."""
        self._heap: List[Tuple[float, str, Any]] = []
        self._entry_counter = 0
        self._entry_finder: Dict[str, List] = {}
        
    def push(self, node_id: str, priority: float, data: Any = None) -> None:
        """
        Add a node to the priority queue.
        
        Args:
            node_id: Unique identifier for the node
            priority: Priority value (lower = higher priority)
            data: Optional additional data to store with the node
        """
        if node_id in self._entry_finder:
            self._mark_removed(node_id)
        
        entry = [priority, self._entry_counter, node_id, data]
        self._entry_finder[node_id] = entry
        heapq.heappush(self._heap, entry)
        self._entry_counter += 1
    
    def pop(self) -> Tuple[str, float, Any]:
        """
        Remove and return the node with lowest priority.
        
        Returns:
            Tuple of (node_id, priority, data)
            
        Raises:
            IndexError: If queue is empty
        """
        while self._heap:
            priority, _, node_id, data = heapq.heappop(self._heap)
            if node_id != '<removed>':
                del self._entry_finder[node_id]
                return node_id, priority, data
        
        raise IndexError("Priority queue is empty")
    
    def decrease_key(self, node_id: str, new_priority: float, data: Any = None) -> None:
        """
        Decrease the priority of a node (if new priority is lower).
        
        Args:
            node_id: Node identifier
            new_priority: New priority value
            data: Optional new data
        """
        if node_id in self._entry_finder:
            old_entry = self._entry_finder[node_id]
            if new_priority < old_entry[0]:
                self._mark_removed(node_id)
                self.push(node_id, new_priority, data)
    
    def _mark_removed(self, node_id: str) -> None:
        """Mark an existing entry as removed."""
        if node_id in self._entry_finder:
            entry = self._entry_finder.pop(node_id)
            entry[2] = '<removed>'
    
    def is_empty(self) -> bool:
        """Check if the priority queue is empty."""
        return len(self._entry_finder) == 0
    
    def size(self) -> int:
        """Get the current size of the queue."""
        return len(self._entry_finder)


class DijkstraPathfinder:
    """
    Optimized Dijkstra's algorithm implementation with advanced features
    for campus navigation and route optimization.
    """
    
    def __init__(self, graph: CampusGraph):
        """
        Initialize pathfinder with a campus graph.
        
        Args:
            graph: The campus graph to use for pathfinding
        """
        self.graph = graph
        self._cache: Dict[Tuple[str, str], PathInfo] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
    def find_shortest_path(self, start_id: str, end_id: str, 
                          options: Optional[RouteOptions] = None) -> Optional[PathInfo]:
        """
        Find the shortest path between two nodes using Dijkstra's algorithm.
        
        Args:
            start_id: Starting node ID
            end_id: Destination node ID
            options: Route calculation options
            
        Returns:
            PathInfo object containing the optimal path, or None if no path exists
            
        Raises:
            PathfindingError: If nodes don't exist or other pathfinding errors occur
        """
        # Input validation
        if not self.graph.node_exists(start_id):
            raise PathfindingError(f"Start node '{start_id}' does not exist")
        if not self.graph.node_exists(end_id):
            raise PathfindingError(f"End node '{end_id}' does not exist")
        
        if start_id == end_id:
            return PathInfo(
                nodes=[start_id],
                total_distance=0.0,
                total_time=0.0,
                path_description=["You are already at your destination"],
                warnings=[],
                route_type="direct"
            )
        
        # Check cache first
        cache_key = (start_id, end_id)
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]
        
        self._cache_misses += 1
        
        # Initialize options
        if options is None:
            options = RouteOptions()
        
        # Run Dijkstra's algorithm
        result = self._dijkstra_search(start_id, end_id, options)
        
        # Cache the result
        if result and len(self._cache) < 1000:  # Limit cache size
            self._cache[cache_key] = result
        
        return result
    
    def _dijkstra_search(self, start_id: str, end_id: str, 
                        options: RouteOptions) -> Optional[PathInfo]:
        """
        Core Dijkstra's algorithm implementation with optimizations.
        
        Args:
            start_id: Starting node ID
            end_id: Destination node ID
            options: Route calculation options
            
        Returns:
            PathInfo object or None if no path exists
        """
        # Initialize data structures
        distances: Dict[str, float] = {start_id: 0.0}
        predecessors: Dict[str, str] = {}
        visited: Set[str] = set()
        pq = PriorityQueue()
        
        # Add start node to priority queue
        pq.push(start_id, 0.0)
        
        while not pq.is_empty():
            current_node, current_distance, _ = pq.pop()
            
            # Skip if already visited (handles duplicate entries)
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # Early termination if we reached the destination
            if current_node == end_id:
                break
            
            # Examine neighbors
            for neighbor_id, base_weight in self.graph.get_neighbors(current_node):
                if neighbor_id in visited:
                    continue
                
                # Apply route preferences and filters
                weight = self._calculate_adjusted_weight(
                    current_node, neighbor_id, base_weight, options
                )
                
                # Skip this edge if it should be avoided
                if weight is None:
                    continue
                
                new_distance = current_distance + weight
                
                # Update if we found a better path
                if neighbor_id not in distances or new_distance < distances[neighbor_id]:
                    distances[neighbor_id] = new_distance
                    predecessors[neighbor_id] = current_node
                    pq.push(neighbor_id, new_distance)
        
        # Reconstruct path if destination was reached
        if end_id not in predecessors and end_id != start_id:
            return None
        
        path = self._reconstruct_path(start_id, end_id, predecessors)
        path_info = self._build_path_info(path, distances[end_id], options)
        
        return path_info
    
    def _calculate_adjusted_weight(self, from_node: str, to_node: str, 
                                 base_weight: float, options: RouteOptions) -> Optional[float]:
        """
        Calculate adjusted weight based on route preferences and constraints.
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
            base_weight: Base edge weight
            options: Route calculation options
            
        Returns:
            Adjusted weight or None if edge should be avoided
        """
        edge_info = self.graph.get_edge_info(from_node, to_node)
        if not edge_info:
            return base_weight
        
        # Check avoidance criteria
        if options.avoid_stairs and 'stairs' in edge_info.edge_type.lower():
            return None
        
        if options.avoid_construction and 'construction' in edge_info.edge_type.lower():
            return None
        
        if not options.include_indoor_paths and 'indoor' in edge_info.edge_type.lower():
            return None
        
        weight = base_weight
        
        # Apply route preference adjustments
        if options.preference == RoutePreference.FASTEST_TIME:
            # Adjust for walking speed on different surface types
            if 'stairs' in edge_info.edge_type.lower():
                weight *= 1.5  # Stairs are slower
            elif 'elevator' in edge_info.edge_type.lower():
                weight += 30  # Fixed time penalty for elevator wait
            elif 'path' in edge_info.edge_type.lower():
                weight *= 0.9  # Paved paths are faster
            
        elif options.preference == RoutePreference.ACCESSIBILITY:
            # Heavily penalize non-accessible routes
            if 'stairs' in edge_info.edge_type.lower():
                weight *= 10.0  # Strong penalty for stairs
            elif 'ramp' in edge_info.edge_type.lower():
                weight *= 0.8  # Prefer ramps
            elif 'elevator' in edge_info.edge_type.lower():
                weight *= 0.9  # Slight preference for elevators
            
        elif options.preference == RoutePreference.SCENIC:
            # Prefer outdoor and scenic routes
            if 'outdoor' in edge_info.edge_type.lower():
                weight *= 0.8
            elif 'garden' in edge_info.edge_type.lower() or 'park' in edge_info.edge_type.lower():
                weight *= 0.7
            elif 'tunnel' in edge_info.edge_type.lower():
                weight *= 1.3
        
        return weight
    
    def _reconstruct_path(self, start_id: str, end_id: str, 
                         predecessors: Dict[str, str]) -> List[str]:
        """
        Reconstruct the path from start to end using predecessors.
        
        Args:
            start_id: Starting node ID
            end_id: Ending node ID
            predecessors: Dictionary mapping each node to its predecessor
            
        Returns:
            List of node IDs representing the path
        """
        path = []
        current = end_id
        
        while current is not None:
            path.append(current)
            current = predecessors.get(current)
        
        path.reverse()
        
        # Verify path integrity
        if path[0] != start_id:
            raise PathfindingError("Path reconstruction failed")
        
        return path
    
    def _build_path_info(self, path: List[str], total_distance: float, 
                        options: RouteOptions) -> PathInfo:
        """
        Build comprehensive path information from the calculated route.
        
        Args:
            path: List of node IDs in the path
            total_distance: Total distance of the path
            options: Route calculation options
            
        Returns:
            Complete PathInfo object
        """
        if len(path) < 2:
            return PathInfo(
                nodes=path,
                total_distance=total_distance,
                total_time=0.0,
                path_description=[],
                warnings=[],
                route_type="direct"
            )
        
        # Generate step-by-step directions
        directions = []
        warnings = []
        total_time = 0.0
        
        for i in range(len(path) - 1):
            from_node_id = path[i]
            to_node_id = path[i + 1]
            
            from_node = self.graph.nodes[from_node_id]
            to_node = self.graph.nodes[to_node_id]
            edge_info = self.graph.get_edge_info(from_node_id, to_node_id)
            
            # Calculate walking time (assume average walking speed of 1.4 m/s)
            if edge_info:
                segment_time = edge_info.weight / 1.4  # Convert distance to time
                total_time += segment_time
                
                # Generate direction text
                direction = f"From {from_node.name} to {to_node.name}"
                if edge_info.edge_type != "path":
                    direction += f" via {edge_info.edge_type}"
                if edge_info.description:
                    direction += f" ({edge_info.description})"
                
                directions.append(direction)
                
                # Add warnings for special path types
                if 'construction' in edge_info.edge_type.lower():
                    warnings.append(f"Construction zone between {from_node.name} and {to_node.name}")
                elif 'stairs' in edge_info.edge_type.lower():
                    warnings.append(f"Stairs required between {from_node.name} and {to_node.name}")
        
        # Determine route type
        route_type = "walking"
        if any('elevator' in direction.lower() for direction in directions):
            route_type = "mixed_indoor"
        elif any('stairs' in direction.lower() for direction in directions):
            route_type = "multi_level"
        
        return PathInfo(
            nodes=path,
            total_distance=total_distance,
            total_time=total_time,
            path_description=directions,
            warnings=warnings,
            route_type=route_type
        )
    
    def find_multiple_paths(self, start_id: str, end_id: str, 
                          num_paths: int = 3) -> List[PathInfo]:
        """
        Find multiple alternative paths between two nodes.
        
        Args:
            start_id: Starting node ID
            end_id: Destination node ID
            num_paths: Number of alternative paths to find
            
        Returns:
            List of PathInfo objects sorted by total distance
        """
        paths = []
        
        # Generate paths with different preferences
        preferences = [
            RoutePreference.SHORTEST_DISTANCE,
            RoutePreference.FASTEST_TIME,
            RoutePreference.ACCESSIBILITY,
            RoutePreference.SCENIC
        ]
        
        for preference in preferences[:num_paths]:
            options = RouteOptions(preference=preference)
            path = self.find_shortest_path(start_id, end_id, options)
            if path and path not in paths:
                paths.append(path)
        
        # Sort by distance
        paths.sort(key=lambda p: p.total_distance)
        
        return paths[:num_paths]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'cache_size': len(self._cache),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': hit_rate
        }
    
    def clear_cache(self) -> None:
        """Clear the path cache."""
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0