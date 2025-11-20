"""
Campus Data Parser Module

This module provides functionality to parse campus data from various file formats
and populate the campus graph structure with comprehensive error handling.
"""

import json
import csv
import os
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from graph import CampusGraph, Node, Edge


class ParseError(Exception):
    """Custom exception for parsing errors."""
    pass


@dataclass
class ParsedData:
    """Container for parsed campus data."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class DataValidator:
    """Validates parsed data for consistency and completeness."""
    
    @staticmethod
    def validate_node_data(node_data: Dict[str, Any]) -> List[str]:
        """
        Validate node data structure.
        
        Args:
            node_data: Dictionary containing node information
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        required_fields = ['id', 'name']
        
        for field in required_fields:
            if field not in node_data or not node_data[field]:
                errors.append(f"Missing or empty required field: {field}")
        
        if 'coordinates' in node_data:
            coords = node_data['coordinates']
            if not isinstance(coords, (list, tuple)) or len(coords) != 2:
                errors.append("Coordinates must be a list/tuple of exactly 2 numbers")
            elif not all(isinstance(x, (int, float)) for x in coords):
                errors.append("Coordinates must be numeric values")
        
        # Validate ID format (alphanumeric with underscores/hyphens)
        if 'id' in node_data and not re.match(r'^[a-zA-Z0-9_-]+$', node_data['id']):
            errors.append("Node ID must contain only alphanumeric characters, underscores, or hyphens")
        
        return errors
    
    @staticmethod
    def validate_edge_data(edge_data: Dict[str, Any]) -> List[str]:
        """
        Validate edge data structure.
        
        Args:
            edge_data: Dictionary containing edge information
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        required_fields = ['from', 'to', 'weight']
        
        for field in required_fields:
            if field not in edge_data:
                errors.append(f"Missing required field: {field}")
        
        if 'weight' in edge_data:
            try:
                weight = float(edge_data['weight'])
                if weight < 0:
                    errors.append("Edge weight cannot be negative")
            except (ValueError, TypeError):
                errors.append("Edge weight must be a valid number")
        
        return errors


class CampusDataParser:
    """
    Comprehensive parser for campus data files with support for multiple formats
    and robust error handling.
    """
    
    def __init__(self):
        """Initialize the parser with validation."""
        self.validator = DataValidator()
        self.supported_formats = ['.json', '.csv']
        
    def parse_file(self, file_path: str) -> ParsedData:
        """
        Parse a campus data file based on its format.
        
        Args:
            file_path: Path to the data file
            
        Returns:
            ParsedData object containing parsed nodes, edges, and metadata
            
        Raises:
            ParseError: If file cannot be parsed or contains invalid data
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.json':
            return self._parse_json_file(file_path)
        elif file_ext == '.csv':
            return self._parse_csv_file(file_path)
        else:
            raise ParseError(f"Unsupported file format: {file_ext}. "
                           f"Supported formats: {self.supported_formats}")
    
    def _parse_json_file(self, file_path: str) -> ParsedData:
        """Parse a JSON format campus data file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ParseError(f"Error reading file: {e}")
        
        # Validate JSON structure
        if not isinstance(data, dict):
            raise ParseError("JSON file must contain a root object")
        
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        metadata = data.get('metadata', {})
        
        if not isinstance(nodes, list):
            raise ParseError("'nodes' must be a list")
        if not isinstance(edges, list):
            raise ParseError("'edges' must be a list")
        
        # Validate each node and edge
        all_errors = []
        
        for i, node in enumerate(nodes):
            errors = self.validator.validate_node_data(node)
            if errors:
                all_errors.extend([f"Node {i}: {error}" for error in errors])
        
        for i, edge in enumerate(edges):
            errors = self.validator.validate_edge_data(edge)
            if errors:
                all_errors.extend([f"Edge {i}: {error}" for error in errors])
        
        if all_errors:
            raise ParseError("Validation errors found:\\n" + "\\n".join(all_errors))
        
        return ParsedData(nodes=nodes, edges=edges, metadata=metadata)
    
    def _parse_csv_file(self, file_path: str) -> ParsedData:
        """
        Parse CSV format campus data file.
        
        Expected format for nodes.csv:
        id,name,type,x,y,description
        
        Expected format for edges.csv:
        from,to,weight,type,description
        """
        try:
            # Determine if it's a nodes or edges file based on headers
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                headers = reader.fieldnames
                
                if not headers:
                    raise ParseError("CSV file has no headers")
                
                data = list(reader)
        
        except Exception as e:
            raise ParseError(f"Error reading CSV file: {e}")
        
        nodes = []
        edges = []
        
        # Check if it's a nodes file
        if 'id' in headers and 'name' in headers:
            for i, row in enumerate(data):
                try:
                    node_data = {
                        'id': row['id'],
                        'name': row['name'],
                        'type': row.get('type', 'general'),
                        'description': row.get('description', '')
                    }
                    
                    # Parse coordinates if present
                    if 'x' in row and 'y' in row:
                        try:
                            x = float(row['x']) if row['x'] else 0.0
                            y = float(row['y']) if row['y'] else 0.0
                            node_data['coordinates'] = [x, y]
                        except ValueError:
                            raise ParseError(f"Invalid coordinates in row {i+1}")
                    
                    errors = self.validator.validate_node_data(node_data)
                    if errors:
                        raise ParseError(f"Row {i+1}: " + ", ".join(errors))
                    
                    nodes.append(node_data)
                    
                except KeyError as e:
                    raise ParseError(f"Missing required column: {e}")
        
        # Check if it's an edges file
        elif 'from' in headers and 'to' in headers and 'weight' in headers:
            for i, row in enumerate(data):
                try:
                    edge_data = {
                        'from': row['from'],
                        'to': row['to'],
                        'weight': float(row['weight']),
                        'type': row.get('type', 'path'),
                        'description': row.get('description', '')
                    }
                    
                    errors = self.validator.validate_edge_data(edge_data)
                    if errors:
                        raise ParseError(f"Row {i+1}: " + ", ".join(errors))
                    
                    edges.append(edge_data)
                    
                except (KeyError, ValueError) as e:
                    raise ParseError(f"Row {i+1}: Invalid data - {e}")
        
        else:
            raise ParseError("CSV file format not recognized. "
                           "Must contain either node data (id,name,...) or "
                           "edge data (from,to,weight,...)")
        
        metadata = {
            'source_file': os.path.basename(file_path),
            'format': 'csv',
            'total_rows': len(data)
        }
        
        return ParsedData(nodes=nodes, edges=edges, metadata=metadata)
    
    def build_graph_from_data(self, parsed_data: ParsedData) -> CampusGraph:
        """
        Build a CampusGraph from parsed data.
        
        Args:
            parsed_data: ParsedData object containing nodes and edges
            
        Returns:
            Fully populated CampusGraph
            
        Raises:
            ParseError: If graph cannot be built due to data issues
        """
        graph = CampusGraph()
        
        # Add all nodes first
        for node_data in parsed_data.nodes:
            coordinates = tuple(node_data.get('coordinates', [0.0, 0.0]))
            
            node = Node(
                node_id=node_data['id'],
                name=node_data['name'],
                coordinates=coordinates,
                node_type=node_data.get('type', 'general'),
                description=node_data.get('description', '')
            )
            
            if not graph.add_node(node):
                raise ParseError(f"Duplicate node ID: {node_data['id']}")
        
        # Add all edges
        missing_nodes = set()
        for edge_data in parsed_data.edges:
            from_node = edge_data['from']
            to_node = edge_data['to']
            
            # Check if referenced nodes exist
            if not graph.node_exists(from_node):
                missing_nodes.add(from_node)
            if not graph.node_exists(to_node):
                missing_nodes.add(to_node)
                
            if missing_nodes:
                continue  # Skip this edge for now
            
            edge = Edge(
                from_node=from_node,
                to_node=to_node,
                weight=edge_data['weight'],
                edge_type=edge_data.get('type', 'path'),
                description=edge_data.get('description', '')
            )
            
            try:
                graph.add_edge(edge)
            except ValueError as e:
                raise ParseError(f"Error adding edge {from_node} -> {to_node}: {e}")
        
        if missing_nodes:
            raise ParseError(f"Edges reference non-existent nodes: {missing_nodes}")
        
        # Validate the final graph
        validation_errors = graph.validate_graph()
        if validation_errors:
            raise ParseError("Graph validation failed:\\n" + "\\n".join(validation_errors))
        
        return graph
    
    def load_campus_from_files(self, *file_paths: str) -> CampusGraph:
        """
        Load campus data from multiple files and combine into a single graph.
        
        Args:
            file_paths: One or more paths to data files
            
        Returns:
            Complete CampusGraph with all data loaded
        """
        all_nodes = []
        all_edges = []
        all_metadata = {}
        
        for file_path in file_paths:
            try:
                parsed_data = self.parse_file(file_path)
                all_nodes.extend(parsed_data.nodes)
                all_edges.extend(parsed_data.edges)
                all_metadata[os.path.basename(file_path)] = parsed_data.metadata
                
            except Exception as e:
                raise ParseError(f"Error processing {file_path}: {e}")
        
        combined_data = ParsedData(
            nodes=all_nodes,
            edges=all_edges,
            metadata=all_metadata
        )
        
        return self.build_graph_from_data(combined_data)
    
    def export_graph_to_json(self, graph: CampusGraph, output_path: str) -> None:
        """
        Export a CampusGraph to JSON format.
        
        Args:
            graph: The graph to export
            output_path: Path where to save the JSON file
        """
        nodes_data = []
        for node in graph.get_all_nodes():
            nodes_data.append({
                'id': node.node_id,
                'name': node.name,
                'type': node.node_type,
                'coordinates': list(node.coordinates),
                'description': node.description
            })
        
        edges_data = []
        for node_id in graph.adjacency_list:
            for edge in graph.adjacency_list[node_id]:
                edges_data.append({
                    'from': edge.from_node,
                    'to': edge.to_node,
                    'weight': edge.weight,
                    'type': edge.edge_type,
                    'description': edge.description
                })
        
        export_data = {
            'metadata': {
                'format_version': '1.0',
                'exported_at': str(os.times()),  # Simple timestamp
                'stats': graph.get_graph_stats()
            },
            'nodes': nodes_data,
            'edges': edges_data
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(export_data, file, indent=2)
        except Exception as e:
            raise ParseError(f"Error exporting graph to {output_path}: {e}")


# Convenience function for quick loading
def load_campus_data(file_path: str) -> CampusGraph:
    """
    Convenience function to quickly load campus data from a file.
    
    Args:
        file_path: Path to the campus data file
        
    Returns:
        Loaded CampusGraph
    """
    parser = CampusDataParser()
    parsed_data = parser.parse_file(file_path)
    return parser.build_graph_from_data(parsed_data)