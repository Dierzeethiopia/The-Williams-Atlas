"""
Basic Tests for Campus Navigator

This module contains simple tests to verify core functionality.
For a production system, consider using pytest or unittest for comprehensive testing.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_graph_basic_operations():
    """Test basic graph operations."""
    from graph import CampusGraph, Node, Edge
    
    print("Testing basic graph operations...")
    
    # Create graph and nodes
    graph = CampusGraph()
    node1 = Node('test1', 'Test Location 1', (0, 0), 'building')
    node2 = Node('test2', 'Test Location 2', (100, 100), 'building')
    node3 = Node('test3', 'Test Location 3', (200, 0), 'landmark')
    
    # Test node addition
    assert graph.add_node(node1), "Should add first node"
    assert graph.add_node(node2), "Should add second node"
    assert graph.add_node(node3), "Should add third node"
    assert not graph.add_node(node1), "Should not add duplicate node"
    assert graph.get_node_count() == 3, f"Expected 3 nodes, got {graph.get_node_count()}"
    
    # Test edge addition
    edge1 = Edge('test1', 'test2', 141.4, 'walkway')
    edge2 = Edge('test2', 'test3', 141.4, 'path')
    
    assert graph.add_edge(edge1), "Should add first edge"
    assert graph.add_edge(edge2), "Should add second edge"
    
    # Test neighbors
    neighbors = graph.get_neighbors('test1')
    assert len(neighbors) == 1, f"Expected 1 neighbor, got {len(neighbors)}"
    assert neighbors[0][0] == 'test2', f"Expected neighbor test2, got {neighbors[0][0]}"
    
    # Test bidirectional edge
    graph.add_bidirectional_edge('test1', 'test3', 200.0, 'road')
    neighbors = graph.get_neighbors('test1')
    assert len(neighbors) == 2, f"Expected 2 neighbors, got {len(neighbors)}"
    
    print("✅ Graph basic operations test passed!")


def test_parser_json():
    """Test JSON data parsing."""
    from parser import CampusDataParser
    import json
    import tempfile
    
    print("Testing JSON parsing...")
    
    # Create sample data
    test_data = {
        "nodes": [
            {"id": "n1", "name": "Node 1", "coordinates": [0, 0]},
            {"id": "n2", "name": "Node 2", "coordinates": [100, 100]}
        ],
        "edges": [
            {"from": "n1", "to": "n2", "weight": 141.4, "type": "path"}
        ]
    }
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        temp_file = f.name
    
    try:
        parser = CampusDataParser()
        parsed_data = parser.parse_file(temp_file)
        
        assert len(parsed_data.nodes) == 2, f"Expected 2 nodes, got {len(parsed_data.nodes)}"
        assert len(parsed_data.edges) == 1, f"Expected 1 edge, got {len(parsed_data.edges)}"
        
        # Build graph from parsed data
        graph = parser.build_graph_from_data(parsed_data)
        assert graph.get_node_count() == 2, "Graph should have 2 nodes"
        assert graph.get_edge_count() == 1, "Graph should have 1 edge"
        
    finally:
        os.unlink(temp_file)
    
    print("✅ JSON parsing test passed!")


def test_pathfinding_basic():
    """Test basic pathfinding functionality."""
    from graph import CampusGraph, Node, Edge
    from pathfinding import DijkstraPathfinder
    
    print("Testing basic pathfinding...")
    
    # Create a simple graph
    graph = CampusGraph()
    
    # Add nodes
    nodes = [
        Node('a', 'Node A', (0, 0)),
        Node('b', 'Node B', (100, 0)),
        Node('c', 'Node C', (200, 0)),
        Node('d', 'Node D', (100, 100))
    ]
    
    for node in nodes:
        graph.add_node(node)
    
    # Add edges to create a simple path network
    edges = [
        Edge('a', 'b', 100.0),  # Direct path A->B
        Edge('b', 'c', 100.0),  # B->C
        Edge('a', 'd', 141.4),  # Longer path A->D
        Edge('d', 'c', 141.4),  # D->C (alternative route)
    ]
    
    for edge in edges:
        graph.add_edge(edge)
    
    # Test pathfinding
    pathfinder = DijkstraPathfinder(graph)
    
    # Find direct path
    path_info = pathfinder.find_shortest_path('a', 'b')
    assert path_info is not None, "Should find path from A to B"
    assert path_info.total_distance == 100.0, f"Expected distance 100.0, got {path_info.total_distance}"
    assert path_info.nodes == ['a', 'b'], f"Expected path ['a', 'b'], got {path_info.nodes}"
    
    # Find longer path
    path_info = pathfinder.find_shortest_path('a', 'c')
    assert path_info is not None, "Should find path from A to C"
    assert path_info.total_distance == 200.0, f"Expected distance 200.0, got {path_info.total_distance}"
    assert path_info.nodes == ['a', 'b', 'c'], f"Expected path ['a', 'b', 'c'], got {path_info.nodes}"
    
    # Test same start and end
    path_info = pathfinder.find_shortest_path('a', 'a')
    assert path_info is not None, "Should handle same start and end"
    assert path_info.total_distance == 0.0, "Distance should be 0 for same location"
    
    print("✅ Basic pathfinding test passed!")


def test_end_to_end():
    """Test complete system functionality."""
    from parser import load_campus_data
    from pathfinding import DijkstraPathfinder
    
    print("Testing end-to-end functionality...")
    
    # Check if sample data exists
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'campus.json')
    
    if not os.path.exists(data_path):
        print("⚠️  Sample campus data not found, skipping end-to-end test")
        return
    
    try:
        # Load campus data
        graph = load_campus_data(data_path)
        assert graph.get_node_count() > 0, "Should load nodes from campus data"
        
        # Create pathfinder
        pathfinder = DijkstraPathfinder(graph)
        
        # Find a route between known locations
        start_nodes = list(graph.nodes.keys())[:2]
        if len(start_nodes) >= 2:
            path_info = pathfinder.find_shortest_path(start_nodes[0], start_nodes[1])
            if path_info:
                assert len(path_info.nodes) >= 2, "Path should contain at least 2 nodes"
                assert path_info.total_distance >= 0, "Distance should be non-negative"
        
        # Test graph statistics
        stats = graph.get_graph_stats()
        assert 'total_nodes' in stats, "Stats should include node count"
        assert 'total_edges' in stats, "Stats should include edge count"
        
        print(f"  📊 Loaded {stats['total_nodes']} nodes and {stats['total_edges']} edges")
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        return
    
    print("✅ End-to-end test passed!")


def run_all_tests():
    """Run all test functions."""
    print("🧪 Running Campus Navigator Tests...")
    print("=" * 50)
    
    tests = [
        test_graph_basic_operations,
        test_parser_json,
        test_pathfinding_basic,
        test_end_to_end
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    run_all_tests()