"""
Campus Navigator - Graphical User Interface

A beautiful GUI application for the Campus Navigator system with
interactive campus map visualization and route planning.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont
import math
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from graph import CampusGraph, Node
from parser import load_campus_data, ParseError
from pathfinding import DijkstraPathfinder, RouteOptions, RoutePreference, PathfindingError


class CampusMapCanvas:
    """Interactive campus map visualization on a canvas."""
    
    def __init__(self, parent, width=800, height=600):
        self.canvas = tk.Canvas(parent, width=width, height=height, bg='#f0f8ff')
        self.width = width
        self.height = height
        self.graph = None
        self.pathfinder = None
        self.current_path = None
        
        # Visual settings
        self.node_colors = {
            'building': '#4a90e2',
            'residence': '#f5a623',
            'recreation': '#7ed321',
            'dining': '#e85d75',
            'services': '#9013fe',
            'parking': '#50e3c2',
            'entrance': '#d0021b',
            'landmark': '#8b572a',
            'general': '#9b9b9b'
        }
        
        self.selected_start = None
        self.selected_end = None
        
        # Bind events
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<Motion>', self.on_hover)
        
    def set_graph(self, graph):
        """Set the campus graph and initialize pathfinder."""
        self.graph = graph
        self.pathfinder = DijkstraPathfinder(graph) if graph else None
        self.draw_campus()
    
    def draw_campus(self):
        """Draw the entire campus map."""
        if not self.graph:
            return
        
        self.canvas.delete("all")
        
        # Calculate scale to fit campus in canvas
        nodes = self.graph.get_all_nodes()
        if not nodes:
            return
        
        # Find bounds
        x_coords = [node.coordinates[0] for node in nodes]
        y_coords = [node.coordinates[1] for node in nodes]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Add padding
        padding = 50
        scale_x = (self.width - 2 * padding) / max(max_x - min_x, 1)
        scale_y = (self.height - 2 * padding) / max(max_y - min_y, 1)
        scale = min(scale_x, scale_y)
        
        # Center the map
        offset_x = padding + (self.width - 2 * padding - (max_x - min_x) * scale) / 2
        offset_y = padding + (self.height - 2 * padding - (max_y - min_y) * scale) / 2
        
        # Draw edges first (so they appear behind nodes)
        self.draw_edges(scale, offset_x, offset_y, min_x, min_y)
        
        # Draw nodes
        self.draw_nodes(scale, offset_x, offset_y, min_x, min_y)
        
        # Draw current path if exists
        if self.current_path:
            self.draw_path(self.current_path, scale, offset_x, offset_y, min_x, min_y)
    
    def draw_edges(self, scale, offset_x, offset_y, min_x, min_y):
        """Draw all edges/connections."""
        for node_id in self.graph.adjacency_list:
            node = self.graph.nodes[node_id]
            x1, y1 = self.world_to_canvas(node.coordinates, scale, offset_x, offset_y, min_x, min_y)
            
            for edge in self.graph.adjacency_list[node_id]:
                target_node = self.graph.nodes[edge.to_node]
                x2, y2 = self.world_to_canvas(target_node.coordinates, scale, offset_x, offset_y, min_x, min_y)
                
                # Draw edge with different styles based on type
                if 'indoor' in edge.edge_type.lower():
                    self.canvas.create_line(x1, y1, x2, y2, fill='#666', width=2, dash=(3, 3), tags='edge')
                else:
                    self.canvas.create_line(x1, y1, x2, y2, fill='#ccc', width=2, tags='edge')
    
    def draw_nodes(self, scale, offset_x, offset_y, min_x, min_y):
        """Draw all nodes/locations."""
        for node in self.graph.get_all_nodes():
            x, y = self.world_to_canvas(node.coordinates, scale, offset_x, offset_y, min_x, min_y)
            
            # Choose color based on node type
            color = self.node_colors.get(node.node_type, self.node_colors['general'])
            
            # Highlight selected nodes
            if node.node_id == self.selected_start:
                color = '#00ff00'  # Green for start
                radius = 14
                outline_color = '#006600'
                outline_width = 3
            elif node.node_id == self.selected_end:
                color = '#ff0000'  # Red for end
                radius = 14
                outline_color = '#660000'
                outline_width = 3
            else:
                radius = 10  # Slightly larger for better visibility
                outline_color = '#333'
                outline_width = 2
            
            # Draw node circle with better visibility
            self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                                  fill=color, outline=outline_color, width=outline_width, 
                                  tags=f'node_{node.node_id}')
            
            # Draw node label with improved visibility
            # Use blue color for better readability with white outline for contrast
            label_color = '#0066cc'  # Blue color for readability
            
            # Draw text with white outline for better visibility
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:  # Create outline effect
                self.canvas.create_text(x+dx, y+radius+15+dy, text=node.name, 
                                      font=('Arial', 9, 'bold'), fill='white', anchor='n',
                                      tags=f'label_outline_{node.node_id}')
            
            # Draw the actual label text in blue on top
            self.canvas.create_text(x, y+radius+15, text=node.name, 
                                  font=('Arial', 9, 'bold'), fill=label_color, anchor='n',
                                  tags=f'label_{node.node_id}')
    
    def draw_path(self, path_nodes, scale, offset_x, offset_y, min_x, min_y):
        """Draw the current route path."""
        if len(path_nodes) < 2:
            return
        
        # Draw path as thick colored line
        for i in range(len(path_nodes) - 1):
            node1 = self.graph.nodes[path_nodes[i]]
            node2 = self.graph.nodes[path_nodes[i + 1]]
            
            x1, y1 = self.world_to_canvas(node1.coordinates, scale, offset_x, offset_y, min_x, min_y)
            x2, y2 = self.world_to_canvas(node2.coordinates, scale, offset_x, offset_y, min_x, min_y)
            
            self.canvas.create_line(x1, y1, x2, y2, fill='#ff6b35', width=5, 
                                  capstyle='round', tags='path')
    
    def world_to_canvas(self, world_coords, scale, offset_x, offset_y, min_x, min_y):
        """Convert world coordinates to canvas coordinates."""
        x = (world_coords[0] - min_x) * scale + offset_x
        y = (world_coords[1] - min_y) * scale + offset_y
        return int(x), int(y)
    
    def find_node_at_position(self, x, y):
        """Find the node at canvas position (x, y)."""
        if not self.graph:
            return None
        
        # Find the closest node within a reasonable distance
        closest_node = None
        min_distance = float('inf')
        
        for item in self.canvas.find_overlapping(x-10, y-10, x+10, y+10):
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith('node_'):
                    node_id = tag[5:]  # Remove 'node_' prefix
                    if node_id in self.graph.nodes:
                        return node_id
        
        return None
    
    def on_click(self, event):
        """Handle mouse clicks on the canvas."""
        node_id = self.find_node_at_position(event.x, event.y)
        
        if node_id:
            if not self.selected_start:
                self.selected_start = node_id
                self.draw_campus()  # Redraw to show selection
            elif not self.selected_end and node_id != self.selected_start:
                self.selected_end = node_id
                self.draw_campus()  # Redraw to show selection
                self.find_route()
            else:
                # Reset selections
                self.selected_start = node_id
                self.selected_end = None
                self.current_path = None
                self.draw_campus()
    
    def on_hover(self, event):
        """Handle mouse hover to show node information."""
        node_id = self.find_node_at_position(event.x, event.y)
        
        if node_id and node_id in self.graph.nodes:
            node = self.graph.nodes[node_id]
            tooltip = f"{node.name} ({node.node_type})"
            if node.description:
                tooltip += f"\\n{node.description}"
            
            # You could implement a tooltip here
            self.canvas.configure(cursor="hand2")
        else:
            self.canvas.configure(cursor="")
    
    def find_route(self):
        """Find and display route between selected nodes."""
        if not self.pathfinder or not self.selected_start or not self.selected_end:
            return
        
        try:
            path_info = self.pathfinder.find_shortest_path(self.selected_start, self.selected_end)
            if path_info:
                self.current_path = path_info.nodes
                self.draw_campus()
                return path_info
            else:
                messagebox.showwarning("No Route", "No route found between selected locations.")
                return None
        except Exception as e:
            messagebox.showerror("Error", f"Error finding route: {e}")
            return None
    
    def clear_selection(self):
        """Clear current selection and path."""
        self.selected_start = None
        self.selected_end = None
        self.current_path = None
        self.draw_campus()


class CampusNavigatorGUI:
    """Main GUI application for Campus Navigator."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Campus Navigator - Graph-Based Pathfinding")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Data
        self.graph = None
        self.pathfinder = None
        
        # Create GUI
        self.setup_styles()
        self.create_widgets()
        self.create_menu()
        
        # Load default data if available
        self.load_default_data()
    
    def setup_styles(self):
        """Configure GUI styles."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure custom styles
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('Info.TLabel', font=('Arial', 10))
    
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🗺️ Campus Navigator", style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        # Content frame
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)
        
        # Left panel for controls
        self.create_control_panel(content_frame)
        
        # Right panel for map
        self.create_map_panel(content_frame)
    
    def create_control_panel(self, parent):
        """Create the control panel."""
        control_frame = ttk.Frame(parent)
        control_frame.pack(side='left', fill='y', padx=(0, 10))
        
        # Campus info section
        info_frame = ttk.LabelFrame(control_frame, text="Campus Information", padding=10)
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=8, width=35, wrap='word')
        info_scroll = ttk.Scrollbar(info_frame, orient='vertical', command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scroll.set)
        
        self.info_text.pack(side='left', fill='both', expand=True)
        info_scroll.pack(side='right', fill='y')
        
        # Route planning section
        route_frame = ttk.LabelFrame(control_frame, text="Route Planning", padding=10)
        route_frame.pack(fill='x', pady=(0, 10))
        
        # Start location
        ttk.Label(route_frame, text="Start Location:").pack(anchor='w')
        self.start_var = tk.StringVar()
        self.start_combo = ttk.Combobox(route_frame, textvariable=self.start_var, state='readonly', width=30)
        self.start_combo.pack(fill='x', pady=(0, 10))
        
        # End location
        ttk.Label(route_frame, text="Destination:").pack(anchor='w')
        self.end_var = tk.StringVar()
        self.end_combo = ttk.Combobox(route_frame, textvariable=self.end_var, state='readonly', width=30)
        self.end_combo.pack(fill='x', pady=(0, 10))
        
        # Route preference
        ttk.Label(route_frame, text="Route Preference:").pack(anchor='w')
        self.preference_var = tk.StringVar(value='Shortest Distance')
        preference_combo = ttk.Combobox(route_frame, textvariable=self.preference_var, 
                                      values=['Shortest Distance', 'Fastest Time', 'Accessible', 'Scenic'],
                                      state='readonly', width=30)
        preference_combo.pack(fill='x', pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(route_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="Find Route", command=self.find_route).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Clear", command=self.clear_route).pack(side='left')
        
        # Route info section
        result_frame = ttk.LabelFrame(control_frame, text="Route Information", padding=10)
        result_frame.pack(fill='both', expand=True)
        
        self.route_text = tk.Text(result_frame, height=10, width=35, wrap='word')
        route_scroll = ttk.Scrollbar(result_frame, orient='vertical', command=self.route_text.yview)
        self.route_text.configure(yscrollcommand=route_scroll.set)
        
        self.route_text.pack(side='left', fill='both', expand=True)
        route_scroll.pack(side='right', fill='y')
    
    def create_map_panel(self, parent):
        """Create the map visualization panel."""
        map_frame = ttk.LabelFrame(parent, text="Campus Map", padding=10)
        map_frame.pack(side='right', fill='both', expand=True)
        
        # Instructions
        instructions = ttk.Label(map_frame, text="Click on locations to select start and destination points", 
                               style='Info.TLabel')
        instructions.pack(pady=(0, 10))
        
        # Canvas for map
        self.map_canvas = CampusMapCanvas(map_frame, width=700, height=500)
        self.map_canvas.canvas.pack(fill='both', expand=True)
        
        # Legend
        self.create_legend(map_frame)
    
    def create_legend(self, parent):
        """Create color legend for node types."""
        legend_frame = ttk.Frame(parent)
        legend_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(legend_frame, text="Legend:", style='Subtitle.TLabel').pack(anchor='w')
        
        legend_items = [
            ('Building', '#4a90e2'), ('Residence', '#f5a623'), ('Recreation', '#7ed321'),
            ('Dining', '#e85d75'), ('Services', '#9013fe'), ('Parking', '#50e3c2'),
            ('Entrance', '#d0021b'), ('Landmark', '#8b572a')
        ]
        
        legend_grid = ttk.Frame(legend_frame)
        legend_grid.pack(fill='x')
        
        for i, (name, color) in enumerate(legend_items):
            row = i // 4
            col = i % 4
            
            item_frame = ttk.Frame(legend_grid)
            item_frame.grid(row=row, column=col, padx=5, pady=2, sticky='w')
            
            # Color box
            color_canvas = tk.Canvas(item_frame, width=12, height=12)
            color_canvas.pack(side='left', padx=(0, 5))
            color_canvas.create_rectangle(0, 0, 12, 12, fill=color, outline='#333')
            
            # Label
            ttk.Label(item_frame, text=name, font=('Arial', 8)).pack(side='left')
    
    def create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Campus Data...", command=self.load_data_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Statistics", command=self.show_statistics)
        view_menu.add_command(label="List All Locations", command=self.list_locations)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def load_default_data(self):
        """Load default campus data if available."""
        default_file = os.path.join("data", "campus.json")
        if os.path.exists(default_file):
            self.load_campus_data(default_file)
    
    def load_data_file(self):
        """Open file dialog to load campus data."""
        filename = filedialog.askopenfilename(
            title="Select Campus Data File",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.load_campus_data(filename)
    
    def load_campus_data(self, filename):
        """Load campus data from file."""
        try:
            self.graph = load_campus_data(filename)
            self.pathfinder = DijkstraPathfinder(self.graph)
            
            # Update GUI
            self.map_canvas.set_graph(self.graph)
            self.update_location_combos()
            self.update_info_display()
            
            messagebox.showinfo("Success", f"Successfully loaded campus data from {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load campus data:\\n{str(e)}")
    
    def update_location_combos(self):
        """Update the location combo boxes."""
        if not self.graph:
            return
        
        locations = [node.name for node in sorted(self.graph.get_all_nodes(), key=lambda n: n.name)]
        
        self.start_combo['values'] = locations
        self.end_combo['values'] = locations
    
    def update_info_display(self):
        """Update the campus information display."""
        self.info_text.delete(1.0, tk.END)
        
        if not self.graph:
            self.info_text.insert(tk.END, "No campus data loaded.\\n\\nUse File → Load Campus Data to load a campus layout file.")
            return
        
        stats = self.graph.get_graph_stats()
        
        info = f"Campus Overview\\n{'='*20}\\n\\n"
        info += f"Total Locations: {stats['total_nodes']}\\n"
        info += f"Total Connections: {stats['total_edges']}\\n"
        info += f"Average Connections: {stats['avg_degree']:.1f}\\n"
        info += f"Total Distance: {stats['total_weight']:.0f}m\\n\\n"
        
        info += "Location Types:\\n"
        for loc_type, count in sorted(stats['node_types'].items()):
            info += f"  • {loc_type.title()}: {count}\\n"
        
        self.info_text.insert(tk.END, info)
    
    def find_route(self):
        """Find route between selected locations."""
        if not self.graph or not self.pathfinder:
            messagebox.showwarning("No Data", "Please load campus data first.")
            return
        
        start_name = self.start_var.get()
        end_name = self.end_var.get()
        
        if not start_name or not end_name:
            messagebox.showwarning("Incomplete Selection", "Please select both start and destination locations.")
            return
        
        # Find node IDs
        start_id = None
        end_id = None
        
        for node in self.graph.get_all_nodes():
            if node.name == start_name:
                start_id = node.node_id
            if node.name == end_name:
                end_id = node.node_id
        
        if not start_id or not end_id:
            messagebox.showerror("Error", "Could not find selected locations in the campus data.")
            return
        
        try:
            # Set route options based on preference
            preference_map = {
                'Shortest Distance': RoutePreference.SHORTEST_DISTANCE,
                'Fastest Time': RoutePreference.FASTEST_TIME,
                'Accessible': RoutePreference.ACCESSIBILITY,
                'Scenic': RoutePreference.SCENIC
            }
            
            preference = preference_map.get(self.preference_var.get(), RoutePreference.SHORTEST_DISTANCE)
            options = RouteOptions(preference=preference)
            
            # Find route
            path_info = self.pathfinder.find_shortest_path(start_id, end_id, options)
            
            if path_info:
                # Update map
                self.map_canvas.selected_start = start_id
                self.map_canvas.selected_end = end_id
                self.map_canvas.current_path = path_info.nodes
                self.map_canvas.draw_campus()
                
                # Update route display
                self.display_route_info(path_info)
            else:
                messagebox.showwarning("No Route", "No route found between the selected locations.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error finding route: {str(e)}")
    
    def display_route_info(self, path_info):
        """Display route information in the text area."""
        self.route_text.delete(1.0, tk.END)
        
        route_text = f"Route Found\\n{'='*15}\\n\\n"
        route_text += f"Distance: {path_info.total_distance:.1f} meters\\n"
        route_text += f"Estimated Time: {path_info.total_time/60:.1f} minutes\\n"
        route_text += f"Route Type: {path_info.route_type.replace('_', ' ').title()}\\n\\n"
        
        if path_info.warnings:
            route_text += "⚠️ Warnings:\\n"
            for warning in path_info.warnings:
                route_text += f"  • {warning}\\n"
            route_text += "\\n"
        
        route_text += "📍 Locations:\\n"
        for i, node_id in enumerate(path_info.nodes):
            if self.graph and node_id in self.graph.nodes:
                node_name = self.graph.nodes[node_id].name
                if i == 0:
                    route_text += f"  🚩 Start: {node_name}\\n"
                elif i == len(path_info.nodes) - 1:
                    route_text += f"  🏁 End: {node_name}\\n"
                else:
                    route_text += f"  📍 {node_name}\\n"
        
        if path_info.path_description:
            route_text += "\\n🧭 Directions:\\n"
            for i, direction in enumerate(path_info.path_description, 1):
                route_text += f"  {i}. {direction}\\n"
        
        self.route_text.insert(tk.END, route_text)
    
    def clear_route(self):
        """Clear the current route and selections."""
        self.start_var.set('')
        self.end_var.set('')
        self.route_text.delete(1.0, tk.END)
        self.map_canvas.clear_selection()
    
    def show_statistics(self):
        """Show detailed campus statistics."""
        if not self.graph:
            messagebox.showwarning("No Data", "Please load campus data first.")
            return
        
        stats = self.graph.get_graph_stats()
        
        stats_text = f"Campus Navigator Statistics\\n{'='*30}\\n\\n"
        stats_text += f"Total Locations: {stats['total_nodes']}\\n"
        stats_text += f"Total Connections: {stats['total_edges']}\\n"
        stats_text += f"Average Connections per Location: {stats['avg_degree']:.2f}\\n"
        stats_text += f"Total Path Distance: {stats['total_weight']:.1f} meters\\n\\n"
        
        stats_text += "Location Types:\\n"
        for loc_type, count in sorted(stats['node_types'].items()):
            stats_text += f"  • {loc_type.title()}: {count}\\n"
        
        stats_text += "\\nConnection Types:\\n"
        for conn_type, count in sorted(stats['edge_types'].items()):
            stats_text += f"  • {conn_type.title()}: {count}\\n"
        
        if self.pathfinder:
            cache_stats = self.pathfinder.get_cache_stats()
            stats_text += f"\\nPathfinding Cache:\\n"
            stats_text += f"  • Cached Routes: {cache_stats['cache_size']}\\n"
            stats_text += f"  • Cache Hit Rate: {cache_stats['hit_rate']:.1%}\\n"
        
        # Show in a new window
        self.show_text_window("Campus Statistics", stats_text)
    
    def list_locations(self):
        """Show a list of all campus locations."""
        if not self.graph:
            messagebox.showwarning("No Data", "Please load campus data first.")
            return
        
        locations = sorted(self.graph.get_all_nodes(), key=lambda n: n.name)
        
        locations_text = f"Campus Locations ({len(locations)} total)\\n{'='*30}\\n\\n"
        
        for node in locations:
            locations_text += f"📍 {node.name}\\n"
            locations_text += f"    Type: {node.node_type.title()}\\n"
            if node.description:
                locations_text += f"    {node.description}\\n"
            locations_text += "\\n"
        
        self.show_text_window("Campus Locations", locations_text)
    
    def show_text_window(self, title, text):
        """Show text in a new window."""
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("500x400")
        
        text_widget = tk.Text(window, wrap='word', padx=10, pady=10)
        scrollbar = ttk.Scrollbar(window, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        text_widget.insert(tk.END, text)
        text_widget.configure(state='disabled')
    
    def show_about(self):
        """Show about dialog."""
        about_text = """Campus Navigator - Graph-Based Pathfinding Tool

A comprehensive campus navigation system featuring:
• Graph-based data structure with adjacency lists
• Optimized Dijkstra's algorithm implementation
• Interactive campus map visualization
• Multiple route optimization preferences
• Professional error handling and validation

Built with Python, Tkinter, and advanced algorithms.

Perfect for demonstrating computer science concepts
and software engineering best practices."""
        
        messagebox.showinfo("About Campus Navigator", about_text)
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for the GUI application."""
    try:
        app = CampusNavigatorGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI application: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")


if __name__ == "__main__":
    main()