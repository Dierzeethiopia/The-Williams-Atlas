#!/usr/bin/env python3
"""
Campus Navigator - Demonstration Script

This script showcases the key features of the Campus Navigator system
with a comprehensive demonstration of its capabilities.
"""

import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from graph import CampusGraph, Node, Edge
from parser import load_campus_data, CampusDataParser
from pathfinding import DijkstraPathfinder, RouteOptions, RoutePreference


def print_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title):
    """Print a formatted subsection header."""
    print(f"\n📍 {title}")
    print("-" * 40)


def demo_graph_creation():
    """Demonstrate manual graph creation."""
    print_header("GRAPH DATA STRUCTURE DEMONSTRATION")
    
    print("Creating a campus graph from scratch...")
    
    # Create graph
    graph = CampusGraph()
    
    # Add nodes
    locations = [
        Node("lib", "Library", (0, 100), "building", "Main academic library"),
        Node("gym", "Gymnasium", (200, 50), "recreation", "Sports and fitness center"),
        Node("cafe", "Campus Cafe", (100, 0), "dining", "Student dining facility"),
        Node("park", "Central Park", (100, 100), "landmark", "Campus green space")
    ]
    
    print("Adding locations:")
    for node in locations:
        graph.add_node(node)
        print(f"  ✓ {node.name} ({node.node_type})")
    
    # Add connections
    print("\nAdding connections:")
    connections = [
        ("lib", "park", 100.0, "walkway", "Short path to park"),
        ("park", "cafe", 100.0, "walkway", "Path to dining"),
        ("cafe", "gym", 141.4, "walkway", "Diagonal path to gym"),
        ("gym", "lib", 223.6, "walkway", "Long path back to library")
    ]
    
    for from_node, to_node, weight, edge_type, desc in connections:
        edge = Edge(from_node, to_node, weight, edge_type, desc)
        graph.add_edge(edge)
        from_name = graph.nodes[from_node].name
        to_name = graph.nodes[to_node].name
        print(f"  ✓ {from_name} → {to_name} ({weight}m)")
    
    # Show statistics
    stats = graph.get_graph_stats()
    print(f"\n📊 Graph Statistics:")
    print(f"  • Total locations: {stats['total_nodes']}")
    print(f"  • Total connections: {stats['total_edges']}")
    print(f"  • Average connections per location: {stats['avg_degree']:.1f}")
    print(f"  • Total distance: {stats['total_weight']:.1f} meters")
    
    return graph


def demo_pathfinding(graph):
    """Demonstrate pathfinding capabilities."""
    print_header("DIJKSTRA'S ALGORITHM DEMONSTRATION")
    
    pathfinder = DijkstraPathfinder(graph)
    
    # Test different route preferences
    start = "lib"
    end = "gym"
    
    preferences = [
        (RoutePreference.SHORTEST_DISTANCE, "Shortest Distance"),
        (RoutePreference.FASTEST_TIME, "Fastest Time"),
        (RoutePreference.SCENIC, "Scenic Route")
    ]
    
    for pref, name in preferences:
        print_section(f"{name} Route")
        options = RouteOptions(preference=pref)
        path_info = pathfinder.find_shortest_path(start, end, options)
        
        if path_info:
            start_name = graph.nodes[start].name
            end_name = graph.nodes[end].name
            print(f"Route from {start_name} to {end_name}:")
            print(f"  Distance: {path_info.total_distance:.1f} meters")
            print(f"  Time: {path_info.total_time/60:.1f} minutes")
            print(f"  Path: {' → '.join([graph.nodes[n].name for n in path_info.nodes])}")
            
            if path_info.path_description:
                print("  Directions:")
                for i, direction in enumerate(path_info.path_description, 1):
                    print(f"    {i}. {direction}")


def demo_data_loading():
    """Demonstrate loading data from files."""
    print_header("DATA PARSING DEMONSTRATION")
    
    data_file = os.path.join("data", "campus.json")
    
    if os.path.exists(data_file):
        print(f"Loading campus data from {data_file}...")
        
        try:
            graph = load_campus_data(data_file)
            
            print("✅ Successfully loaded campus data!")
            
            stats = graph.get_graph_stats()
            print(f"\n📊 Campus Data Statistics:")
            print(f"  • Total locations: {stats['total_nodes']}")
            print(f"  • Total connections: {stats['total_edges']}")
            print(f"  • Total distance: {stats['total_weight']:.1f} meters")
            
            print_section("Location Types")
            for loc_type, count in stats['node_types'].items():
                print(f"  • {loc_type.title()}: {count}")
            
            print_section("Connection Types")
            for conn_type, count in stats['edge_types'].items():
                print(f"  • {conn_type.title()}: {count}")
            
            # Find some example routes
            print_section("Example Routes")
            pathfinder = DijkstraPathfinder(graph)
            
            # Get some sample locations
            nodes = list(graph.nodes.keys())
            if len(nodes) >= 2:
                for i in range(min(3, len(nodes)-1)):
                    start_id = nodes[i]
                    end_id = nodes[i+1]
                    
                    path_info = pathfinder.find_shortest_path(start_id, end_id)
                    if path_info:
                        start_name = graph.nodes[start_id].name
                        end_name = graph.nodes[end_id].name
                        print(f"  {start_name} → {end_name}: {path_info.total_distance:.1f}m")
            
            return graph
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            
    else:
        print(f"⚠️  Data file {data_file} not found")
    
    return None


def demo_performance():
    """Demonstrate performance optimizations."""
    print_header("PERFORMANCE OPTIMIZATION DEMONSTRATION")
    
    print("Creating a larger graph for performance testing...")
    
    # Create a larger graph
    graph = CampusGraph()
    
    # Add many nodes
    num_nodes = 100
    for i in range(num_nodes):
        node = Node(f"node_{i}", f"Location {i}", (i*10, (i*7) % 200), "building")
        graph.add_node(node)
    
    # Add connections in a grid-like pattern
    for i in range(num_nodes - 1):
        # Connect to next node
        edge = Edge(f"node_{i}", f"node_{i+1}", 50.0, "walkway")
        graph.add_edge(edge)
        
        # Add some cross connections
        if i % 10 == 0 and i + 10 < num_nodes:
            edge = Edge(f"node_{i}", f"node_{i+10}", 100.0, "walkway")
            graph.add_edge(edge)
    
    print(f"✅ Created graph with {graph.get_node_count()} nodes and {graph.get_edge_count()} edges")
    
    # Test pathfinding performance
    pathfinder = DijkstraPathfinder(graph)
    
    print("\nTesting pathfinding performance...")
    start_time = time.time()
    
    # Run multiple pathfinding operations
    test_pairs = [
        ("node_0", "node_50"),
        ("node_10", "node_90"),
        ("node_25", "node_75")
    ]
    
    for start, end in test_pairs:
        path_info = pathfinder.find_shortest_path(start, end)
        if path_info:
            print(f"  ✓ {start} → {end}: {path_info.total_distance:.1f}m, {len(path_info.nodes)} steps")
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Pathfinding completed in {elapsed:.3f} seconds")
    
    # Test caching
    print("\nTesting cache performance...")
    start_time = time.time()
    
    # Repeat the same searches to test caching
    for start, end in test_pairs * 2:  # Run twice
        pathfinder.find_shortest_path(start, end)
    
    elapsed = time.time() - start_time
    cache_stats = pathfinder.get_cache_stats()
    
    print(f"⏱️  Cached searches completed in {elapsed:.3f} seconds")
    print(f"📈 Cache hit rate: {cache_stats['hit_rate']:.1%}")


def main():
    """Run the complete demonstration."""
    print("🚀 Campus Navigator - Graph-Based Pathfinding Tool")
    print("   Comprehensive Demonstration")
    print("\nThis demonstration showcases:")
    print("  • Object-oriented graph data structure")
    print("  • Optimized Dijkstra's algorithm implementation")
    print("  • Multi-format data parsing")
    print("  • Advanced route optimization")
    print("  • Performance optimizations with caching")
    
    # Wait for user to start
    input("\nPress Enter to begin the demonstration...")
    
    # Demo 1: Manual graph creation
    demo_graph = demo_graph_creation()
    input("\nPress Enter to continue to pathfinding demonstration...")
    
    # Demo 2: Pathfinding
    demo_pathfinding(demo_graph)
    input("\nPress Enter to continue to data loading demonstration...")
    
    # Demo 3: Data loading
    campus_graph = demo_data_loading()
    input("\nPress Enter to continue to performance demonstration...")
    
    # Demo 4: Performance
    demo_performance()
    
    print_header("DEMONSTRATION COMPLETE")
    print("🎉 Campus Navigator demonstration finished!")
    print("\nKey achievements demonstrated:")
    print("  ✅ Graph-based data structure with adjacency lists")
    print("  ✅ Dijkstra's algorithm implementation from scratch")
    print("  ✅ Multi-format data parsing with validation")
    print("  ✅ Route optimization with different preferences")
    print("  ✅ Performance improvements through caching")
    print("  ✅ Comprehensive error handling and input validation")
    print("\nTo explore more features, run:")
    print("  python main.py --interactive")


if __name__ == "__main__":
    main()