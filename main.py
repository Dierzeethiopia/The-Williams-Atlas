"""
Campus Navigator - Main Application Interface

This module provides the primary user interface for the Campus Navigator
pathfinding system with comprehensive input validation and error handling.
"""

import os
import sys
import json
from typing import Optional, List, Dict, Any
from dataclasses import asdict

# Add the src directory to the Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from graph import CampusGraph, Node
from parser import CampusDataParser, ParseError, load_campus_data
from pathfinding import DijkstraPathfinder, RouteOptions, RoutePreference, PathfindingError


class InputValidator:
    """Validates and sanitizes user input."""
    
    @staticmethod
    def validate_node_name(name: str) -> str:
        """
        Validate and sanitize node name input.
        
        Args:
            name: Raw user input
            
        Returns:
            Cleaned and validated name
            
        Raises:
            ValueError: If input is invalid
        """
        if not name or not name.strip():
            raise ValueError("Location name cannot be empty")
        
        cleaned = name.strip()
        if len(cleaned) > 100:
            raise ValueError("Location name is too long (max 100 characters)")
        
        return cleaned
    
    @staticmethod
    def validate_route_preference(preference: str) -> RoutePreference:
        """
        Validate and convert route preference string.
        
        Args:
            preference: User input string
            
        Returns:
            RoutePreference enum value
            
        Raises:
            ValueError: If preference is invalid
        """
        preference_map = {
            'distance': RoutePreference.SHORTEST_DISTANCE,
            'shortest': RoutePreference.SHORTEST_DISTANCE,
            'time': RoutePreference.FASTEST_TIME,
            'fast': RoutePreference.FASTEST_TIME,
            'fastest': RoutePreference.FASTEST_TIME,
            'accessible': RoutePreference.ACCESSIBILITY,
            'accessibility': RoutePreference.ACCESSIBILITY,
            'scenic': RoutePreference.SCENIC,
            'beautiful': RoutePreference.SCENIC
        }
        
        normalized = preference.lower().strip()
        if normalized not in preference_map:
            valid_options = list(preference_map.keys())
            raise ValueError(f"Invalid route preference. Valid options: {valid_options}")
        
        return preference_map[normalized]


class CampusNavigator:
    """
    Main application class for the Campus Navigator system.
    
    Provides a user-friendly interface for campus pathfinding with
    comprehensive error handling and input validation.
    """
    
    def __init__(self, data_directory: Optional[str] = None):
        """
        Initialize the Campus Navigator.
        
        Args:
            data_directory: Directory containing campus data files
        """
        self.graph: Optional[CampusGraph] = None
        self.pathfinder: Optional[DijkstraPathfinder] = None
        self.data_directory = data_directory or os.path.join(
            os.path.dirname(__file__), '..', 'data'
        )
        self.validator = InputValidator()
        
        # Load campus data if available
        self._load_default_data()
    
    def _load_default_data(self) -> None:
        """Load default campus data if available."""
        try:
            if os.path.exists(self.data_directory):
                data_files = [
                    os.path.join(self.data_directory, 'campus.json'),
                    os.path.join(self.data_directory, 'nodes.csv'),
                    os.path.join(self.data_directory, 'edges.csv')
                ]
                
                # Find available data files
                available_files = [f for f in data_files if os.path.exists(f)]
                
                if available_files:
                    self.load_campus_data(available_files[0])
                    
        except Exception as e:
            print(f"Warning: Could not load default campus data: {e}")
    
    def load_campus_data(self, file_path: str) -> bool:
        """
        Load campus data from a file.
        
        Args:
            file_path: Path to the campus data file
            
        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            self.graph = load_campus_data(file_path)
            self.pathfinder = DijkstraPathfinder(self.graph)
            
            stats = self.graph.get_graph_stats()
            print(f"Successfully loaded campus data:")
            print(f"  • {stats['total_nodes']} locations")
            print(f"  • {stats['total_edges']} connections")
            print(f"  • Average connections per location: {stats['avg_degree']:.1f}")
            
            return True
            
        except (FileNotFoundError, ParseError) as e:
            print(f"Error loading campus data: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error loading data: {e}")
            return False
    
    def find_location(self, query: str) -> Optional[str]:
        """
        Find a location by name or partial name match.
        
        Args:
            query: Search query
            
        Returns:
            Node ID if found, None otherwise
        """
        if not self.graph:
            return None
        
        query = query.lower().strip()
        
        # Try exact match first
        exact_match = self.graph.find_node_by_name(query)
        if exact_match:
            return exact_match
        
        # Try partial matches
        matches = []
        for node in self.graph.get_all_nodes():
            if query in node.name.lower():
                matches.append(node.node_id)
        
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            print(f"Multiple locations found matching '{query}':")
            for node_id in matches:
                node = self.graph.nodes[node_id]
                print(f"  • {node.name} (ID: {node_id})")
            return None
        
        return None
    
    def list_locations(self, location_type: Optional[str] = None) -> List[Node]:
        """
        List all available locations.
        
        Args:
            location_type: Optional filter by location type
            
        Returns:
            List of nodes matching the criteria
        """
        if not self.graph:
            return []
        
        nodes = self.graph.get_all_nodes()
        
        if location_type:
            nodes = [node for node in nodes 
                    if node.node_type.lower() == location_type.lower()]
        
        # Sort by name for better user experience
        return sorted(nodes, key=lambda n: n.name)
    
    def get_route(self, start: str, end: str, 
                  preference: str = "distance", **options) -> Optional[Dict[str, Any]]:
        """
        Get a route between two locations.
        
        Args:
            start: Starting location name
            end: Destination location name
            preference: Route preference (distance, time, accessible, scenic)
            **options: Additional route options
            
        Returns:
            Dictionary containing route information or None if no route found
        """
        if not self.graph or not self.pathfinder:
            print("Error: No campus data loaded. Please load data first.")
            return None
        
        try:
            # Validate and find locations
            start = self.validator.validate_node_name(start)
            end = self.validator.validate_node_name(end)
            
            start_id = self.find_location(start)
            if not start_id:
                print(f"Error: Starting location '{start}' not found.")
                self._suggest_similar_locations(start)
                return None
            
            end_id = self.find_location(end)
            if not end_id:
                print(f"Error: Destination '{end}' not found.")
                self._suggest_similar_locations(end)
                return None
            
            # Validate route preference
            route_pref = self.validator.validate_route_preference(preference)
            
            # Build route options
            route_options = RouteOptions(
                preference=route_pref,
                avoid_stairs=options.get('avoid_stairs', False),
                avoid_construction=options.get('avoid_construction', True),
                include_indoor_paths=options.get('include_indoor', True)
            )
            
            # Find the route
            path_info = self.pathfinder.find_shortest_path(start_id, end_id, route_options)
            
            if not path_info:
                print(f"No route found between '{start}' and '{end}'.")
                return None
            
            return self._format_route_output(path_info)
            
        except ValueError as e:
            print(f"Input validation error: {e}")
            return None
        except PathfindingError as e:
            print(f"Pathfinding error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def get_multiple_routes(self, start: str, end: str, 
                           num_routes: int = 3) -> Optional[List[Dict[str, Any]]]:
        """
        Get multiple alternative routes between two locations.
        
        Args:
            start: Starting location name
            end: Destination location name
            num_routes: Number of alternative routes to find
            
        Returns:
            List of route dictionaries or None if no routes found
        """
        if not self.graph or not self.pathfinder:
            print("Error: No campus data loaded. Please load data first.")
            return None
        
        try:
            start_id = self.find_location(start)
            end_id = self.find_location(end)
            
            if not start_id or not end_id:
                print("Error: One or both locations not found.")
                return None
            
            paths = self.pathfinder.find_multiple_paths(start_id, end_id, num_routes)
            
            if not paths:
                print(f"No routes found between '{start}' and '{end}'.")
                return None
            
            return [self._format_route_output(path) for path in paths]
            
        except Exception as e:
            print(f"Error finding alternative routes: {e}")
            return None
    
    def _format_route_output(self, path_info) -> Dict[str, Any]:
        """Format path information for output."""
        if not path_info:
            return {}
        
        # Get location names
        location_names = []
        for node_id in path_info.nodes:
            if self.graph and node_id in self.graph.nodes:
                location_names.append(self.graph.nodes[node_id].name)
            else:
                location_names.append(node_id)
        
        return {
            'locations': location_names,
            'total_distance_m': round(path_info.total_distance, 1),
            'estimated_time_min': round(path_info.total_time / 60, 1),
            'directions': path_info.path_description,
            'warnings': path_info.warnings,
            'route_type': path_info.route_type
        }
    
    def _suggest_similar_locations(self, query: str) -> None:
        """Suggest similar location names based on partial matches."""
        if not self.graph:
            return
        
        query = query.lower()
        suggestions = []
        
        for node in self.graph.get_all_nodes():
            name_lower = node.name.lower()
            # Simple similarity based on common substrings
            if any(word in name_lower for word in query.split()):
                suggestions.append(node.name)
        
        if suggestions:
            print("Did you mean one of these locations?")
            for suggestion in suggestions[:5]:  # Limit to 5 suggestions
                print(f"  • {suggestion}")
    
    def display_stats(self) -> None:
        """Display comprehensive system statistics."""
        if not self.graph:
            print("No campus data loaded.")
            return
        
        stats = self.graph.get_graph_stats()
        
        print("\\n=== Campus Navigator Statistics ===")
        print(f"Total Locations: {stats['total_nodes']}")
        print(f"Total Connections: {stats['total_edges']}")
        print(f"Average Connections per Location: {stats['avg_degree']:.2f}")
        print(f"Total Path Distance: {stats['total_weight']:.1f} meters")
        
        print("\\nLocation Types:")
        for loc_type, count in stats['node_types'].items():
            print(f"  • {loc_type.title()}: {count}")
        
        print("\\nConnection Types:")
        for conn_type, count in stats['edge_types'].items():
            print(f"  • {conn_type.title()}: {count}")
        
        if self.pathfinder:
            cache_stats = self.pathfinder.get_cache_stats()
            print(f"\\nPathfinding Cache:")
            print(f"  • Cached Routes: {cache_stats['cache_size']}")
            print(f"  • Cache Hit Rate: {cache_stats['hit_rate']:.1%}")
    
    def interactive_mode(self) -> None:
        """Start interactive command-line interface."""
        print("\\n=== Welcome to Campus Navigator ===")
        print("Type 'help' for available commands, or 'quit' to exit.")
        
        while True:
            try:
                command = input("\\nNavigator> ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                elif command in ['help', 'h']:
                    self._show_help()
                
                elif command in ['stats', 'statistics']:
                    self.display_stats()
                
                elif command in ['list', 'locations']:
                    self._interactive_list_locations()
                
                elif command in ['route', 'find', 'navigate']:
                    self._interactive_find_route()
                
                elif command in ['load', 'loaddata']:
                    self._interactive_load_data()
                
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\\nGoodbye!")
                break
            except EOFError:
                print("\\nGoodbye!")
                break
    
    def _show_help(self) -> None:
        """Display help information."""
        print("\\n=== Available Commands ===")
        print("  route     - Find a route between two locations")
        print("  list      - List all available locations")
        print("  stats     - Show system statistics")
        print("  load      - Load campus data from file")
        print("  help      - Show this help message")
        print("  quit      - Exit the program")
    
    def _interactive_list_locations(self) -> None:
        """Interactive location listing."""
        locations = self.list_locations()
        if not locations:
            print("No locations available.")
            return
        
        print(f"\\nAvailable Locations ({len(locations)}):")
        for i, node in enumerate(locations, 1):
            type_info = f" ({node.node_type})" if node.node_type != "general" else ""
            print(f"  {i:3d}. {node.name}{type_info}")
    
    def _interactive_find_route(self) -> None:
        """Interactive route finding."""
        try:
            start = input("Starting location: ").strip()
            if not start:
                return
            
            end = input("Destination: ").strip()
            if not end:
                return
            
            print("Route preferences:")
            print("  1. Shortest distance (default)")
            print("  2. Fastest time")
            print("  3. Accessible route")
            print("  4. Scenic route")
            
            pref_input = input("Choose preference (1-4, or press Enter for default): ").strip()
            
            preferences = {
                '1': 'distance',
                '2': 'time',
                '3': 'accessible',
                '4': 'scenic',
                '': 'distance'
            }
            
            preference = preferences.get(pref_input, 'distance')
            
            route = self.get_route(start, end, preference)
            
            if route:
                self._display_route(route)
                
        except KeyboardInterrupt:
            print("\\nRoute finding cancelled.")
    
    def _interactive_load_data(self) -> None:
        """Interactive data loading."""
        try:
            file_path = input("Enter path to campus data file: ").strip()
            if file_path and os.path.exists(file_path):
                success = self.load_campus_data(file_path)
                if success:
                    print("Data loaded successfully!")
                else:
                    print("Failed to load data.")
            else:
                print("File not found.")
        except KeyboardInterrupt:
            print("\\nData loading cancelled.")
    
    def _display_route(self, route: Dict[str, Any]) -> None:
        """Display formatted route information."""
        print(f"\\n=== Route Found ===")
        print(f"Distance: {route['total_distance_m']} meters")
        print(f"Estimated Time: {route['estimated_time_min']} minutes")
        print(f"Route Type: {route['route_type'].replace('_', ' ').title()}")
        
        if route['warnings']:
            print("\\nWarnings:")
            for warning in route['warnings']:
                print(f"  ⚠️  {warning}")
        
        print("\\nDirections:")
        for i, direction in enumerate(route['directions'], 1):
            print(f"  {i}. {direction}")
        
        print(f"\\nYou will pass through {len(route['locations'])} locations:")
        for i, location in enumerate(route['locations']):
            if i == 0:
                print(f"  🚩 Start: {location}")
            elif i == len(route['locations']) - 1:
                print(f"  🏁 End: {location}")
            else:
                print(f"  📍 {location}")


def main():
    """Main entry point for the Campus Navigator application."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Campus Navigator - Graph-Based Pathfinding Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --interactive
  python main.py --load data/campus.json --from "Library" --to "Student Center"
  python main.py --stats
        """
    )
    
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Start interactive mode')
    parser.add_argument('--load', '-l', metavar='FILE',
                       help='Load campus data from file')
    parser.add_argument('--from', '-f', dest='start', metavar='LOCATION',
                       help='Starting location for route finding')
    parser.add_argument('--to', '-t', dest='end', metavar='LOCATION',
                       help='Destination for route finding')
    parser.add_argument('--preference', '-p', choices=['distance', 'time', 'accessible', 'scenic'],
                       default='distance', help='Route preference')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='Show system statistics')
    parser.add_argument('--list', action='store_true',
                       help='List all locations')
    
    args = parser.parse_args()
    
    # Initialize navigator
    navigator = CampusNavigator()
    
    # Load data if specified
    if args.load:
        navigator.load_campus_data(args.load)
    
    # Handle different modes
    if args.interactive:
        navigator.interactive_mode()
    elif args.stats:
        navigator.display_stats()
    elif args.list:
        locations = navigator.list_locations()
        print(f"Available locations ({len(locations)}):")
        for node in locations:
            print(f"  • {node.name}")
    elif args.start and args.end:
        route = navigator.get_route(args.start, args.end, args.preference)
        if route:
            navigator._display_route(route)
    else:
        navigator.interactive_mode()


if __name__ == '__main__':
    main()