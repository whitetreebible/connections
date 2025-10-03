#!/usr/bin/env python3
"""
Manual tool for adding or renaming nodes and edges in the biblical connections project.
Uses inquirer library for interactive prompts and autocompletion.
"""
from whitetreebible.connections.logger import log
import os
import re
import sys
import yaml
import inquirer
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from whitetreebible.connections.logger import log
from whitetreebible.connections.models.node_model import NodeModel, NodeModelCollection, NodeType
from whitetreebible.connections.models.edge_model import EdgeModel
from whitetreebible.connections.models.edge_type import EdgeType, RECIPROCALS
from whitetreebible.connections.sqlite_db import SqliteDB
from whitetreebible.connections.settings import DATA_DIR, DB_PATH
from whitetreebible.connections.import_external_to_yml import lookup_similar_nodes, get_node_yaml_path


@dataclass
class NodeInfo:
    """Information about a node for autocomplete and validation."""
    type: str
    id: str
    name: str
    name_disambiguous: str
    
    @property
    def link(self) -> str:
        return f"{self.type}/{self.id}"
    
    def __str__(self) -> str:
        return f"{self.name_disambiguous or self.name} ({self.link})"


class ManualEditor:
    def __init__(self, data_dir: str = DATA_DIR, db_path: str = DB_PATH):
        self.data_dir = data_dir
        self.db_path = db_path
        self.db = SqliteDB(db_path)
        self._all_nodes_cache = None
        self._edge_types_cache = None
        
    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def get_all_nodes(self) -> List[NodeInfo]:
        """Get all nodes from database for autocomplete."""
        if self._all_nodes_cache is None:
            nodes = []
            try:
                cur = self.db.conn.cursor()
                cur.execute("SELECT DISTINCT id, type FROM nodes")
                for row in cur.fetchall():
                    node_id, node_type = row
                    # Get name and name_disambiguous from database
                    name = self.db.select_name(node_type, node_id, "en") or node_id
                    yaml_path = get_node_yaml_path(node_type, node_id)
                    name_disamb = ""
                    if os.path.exists(yaml_path):
                        try:
                            node = NodeModel.from_yaml_file(yaml_path)
                            name_disamb = node.name_disambiguous.get('en', '') if hasattr(node, 'name_disambiguous') else ''
                        except Exception:
                            pass
                    nodes.append(NodeInfo(
                        type=node_type,
                        id=node_id,
                        name=name,
                        name_disambiguous=name_disamb or name
                    ))
            except Exception as e:
                log.warning(f"Could not fetch nodes from database: {e}")
                # Fallback to YAML files
                collection = NodeModelCollection(self.data_dir)
                for node in collection.get_nodes():
                    name = node.name.get('en', node.id)
                    name_disamb = node.name_disambiguous.get('en', '') if hasattr(node, 'name_disambiguous') else ''
                    nodes.append(NodeInfo(
                        type=node.type,
                        id=node.id,
                        name=name,
                        name_disambiguous=name_disamb or name
                    ))
            self._all_nodes_cache = sorted(nodes, key=lambda x: x.name.lower())
        return self._all_nodes_cache
    
    def get_edge_types(self) -> List[str]:
        """Get all available edge types."""
        if self._edge_types_cache is None:
            self._edge_types_cache = [et.value for et in EdgeType]
        return self._edge_types_cache
    
    def node_exists(self, node_type: str, node_id: str) -> bool:
        """Check if a node exists."""
        yaml_path = get_node_yaml_path(node_type, node_id)
        return os.path.exists(yaml_path)
    
    def fuzzy_search_nodes(self, query: str, limit: int = 10) -> List[NodeInfo]:
        """Perform fuzzy search on nodes by name or ID."""
        if not query.strip():
            return []
        
        query_lower = query.lower()
        all_nodes = self.get_all_nodes()
        matches = []
        
        for node in all_nodes:
            score = 0
            
            # Exact match on ID or name gets highest score
            if query_lower == node.id.lower() or query_lower == node.name.lower():
                score = 1000
            # Starts with query gets high score
            elif (node.id.lower().startswith(query_lower) or 
                  node.name.lower().startswith(query_lower) or
                  node.name_disambiguous.lower().startswith(query_lower)):
                score = 500
            # Contains query gets medium score
            elif (query_lower in node.id.lower() or 
                  query_lower in node.name.lower() or
                  query_lower in node.name_disambiguous.lower()):
                score = 100
            
            if score > 0:
                matches.append((score, node))
        
        # Sort by score (descending) and take top results
        matches.sort(key=lambda x: x[0], reverse=True)
        return [node for score, node in matches[:limit]]
    
    def select_node_with_search(self, prompt: str, allow_new: bool = True) -> Optional[NodeInfo]:
        """Select a node using text search with fuzzy matching.
        
        Returns:
            NodeInfo: Selected node
            None: User chose to create new node (only if allow_new=True)
            "CANCEL": User cancelled
        """
        while True:
            # Get search query
            prompt_text = "Enter search term (name, ID, or part of either):"
            if prompt.strip():
                prompt_text = f"{prompt}\n{prompt_text}"
            
            search_query = inquirer.text(message=prompt_text)
            
            if not search_query:
                return "CANCEL"
            
            # Special commands
            if search_query.lower() in ['new', 'create']:
                if allow_new:
                    return None  # Signal to create new node
                else:
                    print("❌ Creating new nodes is not allowed in this context")
                    continue
            
            # Search for matching nodes
            matches = self.fuzzy_search_nodes(search_query)
            
            if not matches:
                print(f"❌ No nodes found matching '{search_query}'")
                retry = inquirer.confirm("Try another search?", default=True)
                if not retry:
                    return "CANCEL"
                continue
            
            # Prepare choices for selection (no duplicate display)
            choices = []
            
            for i, node in enumerate(matches, 1):
                display = f"{node.name_disambiguous} ({node.link})"
                choices.append((display, node))
            
            # Add options
            choices.append(("🔍 Search again", "search_again"))
            if allow_new:
                choices.append(("➕ Create new node", None))
            choices.append(("❌ Cancel", "cancel"))
            
            # Let user select from matches
            questions = [
                inquirer.List('selection',
                             message=f"Found {len(matches)} matches for '{search_query}'. Select a node:",
                             choices=choices)
            ]
            
            answers = inquirer.prompt(questions)
            if not answers:
                return "CANCEL"
            
            selection = answers['selection']
            
            if selection == "search_again":
                continue
            elif selection == "cancel":
                return "CANCEL"
            elif selection is None:  # Create new node
                return None
            else:
                return selection
    
    def prompt_for_node_creation(self) -> Optional[NodeInfo]:
        """Prompt user to create a new node."""
        # Get node type
        node_types = [nt.value for nt in NodeType]
        questions = [
            inquirer.List('type',
                         message="Select node type:",
                         choices=node_types),
            inquirer.Text('id',
                         message="Enter node ID (lowercase, use hyphens for spaces):"),
            inquirer.Text('name',
                         message="Enter node name:"),
            inquirer.Text('name_disambiguous',
                         message="Enter disambiguous name (optional):",
                         default="")
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            return None
        
        # Validate ID format
        node_id = answers['id'].strip().lower()
        if not re.match(r'^[a-z0-9\-_]+$', node_id):
            log.error("Node ID must contain only lowercase letters, numbers, hyphens, and underscores")
            return None
        
        # Check if node already exists
        if self.node_exists(answers['type'], node_id):
            log.error(f"Node {answers['type']}/{node_id} already exists")
            return None
        
        name = answers['name'].strip()
        name_disamb = answers['name_disambiguous'].strip() or name
        
        return NodeInfo(
            type=answers['type'],
            id=node_id,
            name=name,
            name_disambiguous=name_disamb
        )
    
    def create_new_node(self, node_info: NodeInfo) -> bool:
        """Create a new node YAML file."""
        try:
            # Create the YAML structure
            node_data = {
                'id': node_info.id,
                'type': node_info.type,
                'name': {'en': node_info.name},
                'name_disambiguous': {'en': node_info.name_disambiguous},
                'description': {'en': ''},
                'footnotes': {},
                'edges': []
            }
            
            # Create directory if it doesn't exist
            type_dir = os.path.join(self.data_dir, node_info.type)
            os.makedirs(type_dir, exist_ok=True)
            
            # Write YAML file
            yaml_path = os.path.join(type_dir, f"{node_info.id}.yml")
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(node_data, f, sort_keys=False, allow_unicode=True)
            
            log.info(f"Created new node: {yaml_path}")
            log.info(f"✅ Created new node at: {yaml_path}")
            log.info(f"📝 Please edit the file to add description and other details")
            
            # Clear cache to include new node
            self._all_nodes_cache = None
            
            return True
            
        except Exception as e:
            log.error(f"Failed to create node: {e}")
            return False
    
    def select_edge_type(self) -> Optional[EdgeType]:
        """Select an edge type with search functionality."""
        edge_types = self.get_edge_types()
        
        while True:
            # Get search query
            search_query = inquirer.text(
                message="Enter edge type search term (or full edge type):"
            )
            
            if not search_query:
                return None
            
            search_lower = search_query.lower()
            
            # Find matching edge types
            matches = []
            for edge_type_str in edge_types:
                edge_type = EdgeType(edge_type_str)
                # Check against both value and human-readable form
                readable = edge_type.for_lang('en')
                
                if (search_lower in edge_type_str.lower() or 
                    search_lower in readable.lower() or
                    edge_type_str.lower().startswith(search_lower) or
                    readable.lower().startswith(search_lower)):
                    matches.append((edge_type_str, readable, edge_type))
            
            if not matches:
                log.info(f"❌ No edge types found matching '{search_query}'")
                log.info("💡 Some examples: married-to, parent-of, member-of, associated-with")
                retry = inquirer.confirm("Try another search?", default=True)
                if not retry:
                    return None
                continue
            
            # Display matches
            log.info(f"\n🔍 Found {len(matches)} edge type(s) matching '{search_query}':")
            choices = []
            
            for edge_type_str, readable, edge_type in matches:
                display = f"{readable} ({edge_type_str})"
                log.info(f"   • {display}")
                choices.append((display, edge_type))
            
            # Add search again option
            choices.append(("🔍 Search again", "search_again"))
            choices.append(("❌ Cancel", "cancel"))
            
            # Let user select
            questions = [
                inquirer.List('selection',
                             message="Select an edge type:",
                             choices=choices)
            ]
            
            answers = inquirer.prompt(questions)
            if not answers:
                return None
            
            selection = answers['selection']
            
            if selection == "search_again":
                continue
            elif selection == "cancel":
                return None
            else:
                return selection
    
    def prompt_for_edge_creation(self, source_node: NodeInfo) -> bool:
        """Prompt user to create a new edge."""
        # Select edge type with search
        edge_type = self.select_edge_type()
        if not edge_type:
            return False
        
        # Select target node
        print(f"\n🎯 Select target for '{edge_type.for_lang('en')}' relationship:")
        target_node = self.select_node_with_search("")
        
        if target_node == "CANCEL":
            return False
        elif target_node is None:
            # User chose to create new node
            target_node = self.prompt_for_node_creation()
            if target_node:
                if not self.create_new_node(target_node):
                    return False
            else:
                return False
        
        # Prompt for reference
        ref_type = inquirer.list_input(
            "Select reference type:",
            choices=['bible', 'footnote', 'none']
        )
        
        refs = []
        footnote_slug = None
        footnote_content = None
        
        if ref_type == 'bible':
            bible_ref = inquirer.text(message="Enter Bible reference (e.g., 'Ruth 1:1'):")
            if bible_ref:
                refs.append(f"bible:{bible_ref}")
        elif ref_type == 'footnote':
            footnote_slug = inquirer.text(message="Enter footnote slug:")
            footnote_content = inquirer.text(message="Enter footnote content:")
            if footnote_slug:
                refs.append(f"footnote:{footnote_slug}")
        
        # Create the edge
        return self.add_edge(source_node, target_node, edge_type, refs, footnote_slug, footnote_content)
    
    def add_edge(self, source: NodeInfo, target: NodeInfo, edge_type: EdgeType, refs: List[str], footnote_slug: Optional[str] = None, footnote_content: Optional[str] = None) -> bool:
        """Add an edge between two nodes."""
        try:
            # Load source node
            source_path = get_node_yaml_path(source.type, source.id)
            if not os.path.exists(source_path):
                log.error(f"Source node file not found: {source_path}")
                return False
            
            source_node = NodeModel.from_yaml_file(source_path)
            
            # Add footnote if provided
            if footnote_slug and footnote_content:
                if not hasattr(source_node, 'footnotes') or source_node.footnotes is None:
                    source_node.footnotes = {}
                source_node.footnotes[footnote_slug] = {"en": footnote_content}
            
            # Check if edge already exists
            target_link = target.link
            existing_edge = None
            for edge in source_node.edges:
                if edge.target == target_link and edge.type == edge_type:
                    existing_edge = edge
                    break
            
            if existing_edge:
                # Add new refs to existing edge
                for ref in refs:
                    if ref not in existing_edge.refs:
                        existing_edge.refs.append(ref)
                log.info(f"Updated existing edge with new refs")
            else:
                # Create new edge
                edge_data = {
                    "target": target_link,
                    "type": edge_type,
                    "refs": refs
                }
                source_node.edges.append(EdgeModel(edge_data))
                log.info(f"Added new edge: {source.link} {edge_type} {target_link}")
            
            # Save source node
            source_node.to_yaml(source_path)
            
            # Handle reciprocal edge
            if edge_type in RECIPROCALS:
                reciprocal_type = RECIPROCALS[edge_type]
                target_path = get_node_yaml_path(target.type, target.id)
                
                if not os.path.exists(target_path):
                    log.warning(f"Target node file not found for reciprocal: {target_path}")
                else:
                    target_node = NodeModel.from_yaml_file(target_path)
                    
                    # Check if reciprocal edge exists
                    source_link = source.link
                    existing_reciprocal = None
                    for edge in target_node.edges:
                        if edge.target == source_link and edge.type == reciprocal_type:
                            existing_reciprocal = edge
                            break
                    
                    # Only mirror bible refs (not footnotes) for reciprocal
                    reciprocal_refs = [ref for ref in refs if ref.startswith("bible:")]
                    
                    if existing_reciprocal:
                        # Add new refs to existing reciprocal edge
                        for ref in reciprocal_refs:
                            if ref not in existing_reciprocal.refs:
                                existing_reciprocal.refs.append(ref)
                    else:
                        # Create new reciprocal edge
                        reciprocal_edge_data = {
                            "target": source_link,
                            "type": reciprocal_type,
                            "refs": reciprocal_refs
                        }
                        target_node.edges.append(EdgeModel(reciprocal_edge_data))
                    
                    # Save target node
                    target_node.to_yaml(target_path)
                    log.info(f"Added reciprocal edge: {target.link} {reciprocal_type} {source_link}")
            
            log.info(f"✅ Added edge: {source.name} {edge_type.for_lang('en')} {target.name}")
            if footnote_slug:
                log.info(f"📝 Added footnote: {footnote_slug}")
            if edge_type in RECIPROCALS:
                log.info(f"🔄 Added reciprocal edge: {target.name} {RECIPROCALS[edge_type].for_lang('en')} {source.name}")
            
            return True
            
        except Exception as e:
            log.error(f"Failed to add edge: {e}")
            return False
    
    def rename_node(self) -> bool:
        """Rename a node and update all references."""
        # Select node to rename
        print("\n✏️ Select node to rename:")
        node = self.select_node_with_search("", allow_new=False)
        if not node or node == "CANCEL":
            return False
        
        log.info(f"\n📝 Renaming node: {node.name_disambiguous} ({node.link})")
        
        # Get new names
        questions = [
            inquirer.Text('new_id',
                         message=f"Enter new ID for {node.link} (current: {node.id}):",
                         default=node.id),
            inquirer.Text('new_name',
                         message=f"Enter new name (current: {node.name}):",
                         default=node.name),
            inquirer.Text('new_name_disambiguous',
                         message=f"Enter new disambiguous name (current: {node.name_disambiguous}):",
                         default=node.name_disambiguous)
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            return False
        
        new_id = answers['new_id'].strip().lower()
        new_name = answers['new_name'].strip()
        new_name_disamb = answers['new_name_disambiguous'].strip()
        
        # Validate new ID
        if not re.match(r'^[a-z0-9\-_]+$', new_id):
            log.error("Node ID must contain only lowercase letters, numbers, hyphens, and underscores")
            return False
        
        # Check if new ID already exists (but allow same ID if just changing names)
        if new_id != node.id and self.node_exists(node.type, new_id):
            log.error(f"Node {node.type}/{new_id} already exists")
            return False
        
        try:
            old_link = node.link
            new_link = f"{node.type}/{new_id}"
            
            # Update the node itself
            old_path = get_node_yaml_path(node.type, node.id)
            node_data = NodeModel.from_yaml_file(old_path)
            
            # Update node data
            node_data.id = new_id
            node_data.name['en'] = new_name
            node_data.name_disambiguous['en'] = new_name_disamb
            
            # Save to new path if ID changed
            if new_id != node.id:
                new_path = get_node_yaml_path(node.type, new_id)
                node_data.to_yaml(new_path)
                os.remove(old_path)
                log.info(f"📁 Moved: {old_path} → {new_path}")
            else:
                node_data.to_yaml(old_path)
                log.info(f"💾 Updated: {old_path}")
            
            # Find and update all references in other nodes
            if new_id != node.id:  # Only if ID changed
                updated_files = self.update_all_references(old_link, new_link)
                print(f"🔗 Updated {len(updated_files)} files with references to {old_link}")
                for file_path in updated_files:
                    print(f"   - {file_path}")
            
            # Update database - reimport the changed files
            print("\n🔄 Updating database...")
            self._update_database_after_rename(node.type, node.id, new_id)
            
            # Clear cache to reflect changes
            self._all_nodes_cache = None
            
            # Print locations to update manually
            print("\n📝 Manual updates needed:")
            print(f"   - Update descriptions containing [[{old_link}]] in all languages")
            print(f"   - Update footnotes containing [[{old_link}]] in all languages")
            print(f"   - Regenerate markdown with: tom md")
            
            return True
            
        except Exception as e:
            log.error(f"Failed to rename node: {e}")
            return False
    
    def update_all_references(self, old_link: str, new_link: str) -> List[str]:
        """Update all edge references from old_link to new_link."""
        updated_files = []
        
        # Walk through all YAML files
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if file.endswith(('.yml', '.yaml')):
                    file_path = os.path.join(root, file)
                    try:
                        node = NodeModel.from_yaml_file(file_path)
                        updated = False
                        
                        # Update edge targets
                        for edge in node.edges:
                            if edge.target == old_link:
                                edge.target = new_link
                                updated = True
                        
                        if updated:
                            node.to_yaml(file_path)
                            updated_files.append(file_path)
                            
                    except Exception as e:
                        log.warning(f"Could not process {file_path}: {e}")
        
        return updated_files
    
    def _update_database_after_rename(self, node_type: str, old_id: str, new_id: str):
        """Update database after renaming a node."""
        try:
            old_link = f"{node_type}/{old_id}"
            new_link = f"{node_type}/{new_id}"
            
            # Update node entry
            cur = self.db.conn.cursor()
            cur.execute("UPDATE nodes SET id = ? WHERE type = ? AND id = ?", (new_id, node_type, old_id))
            
            # Update edges where this node is source
            cur.execute("UPDATE edges SET source = ? WHERE source = ?", (new_link, old_link))
            
            # Update edges where this node is target
            cur.execute("UPDATE edges SET target = ? WHERE target = ?", (new_link, old_link))
            
            self.db.conn.commit()
            print("✅ Database updated successfully")
            
        except Exception as e:
            log.error(f"Failed to update database: {e}")
            print(f"⚠️ Database update failed: {e}")
            print("   Please run 'tom yml' to regenerate the database")
    
    def add_new_node(self) -> bool:
        """Add a new node workflow."""
        node_info = self.prompt_for_node_creation()
        if not node_info:
            return False
        
        if not self.create_new_node(node_info):
            return False
        
        # Ask if user wants to add an edge
        add_edge = inquirer.confirm("Add an edge to this node?", default=True)
        if add_edge:
            return self.prompt_for_edge_creation(node_info)
        
        return True
    
    def add_new_edge(self) -> bool:
        """Add a new edge workflow."""
        # Select source node
        print("\n🔗 Select source node:")
        source_node = self.select_node_with_search("")
        if source_node == "CANCEL":
            return False
        elif source_node is None:
            # User chose to create new node
            source_node = self.prompt_for_node_creation()
            if source_node:
                if not self.create_new_node(source_node):
                    return False
            else:
                return False
        
        return self.prompt_for_edge_creation(source_node)
    
    def show_stats(self):
        """Display statistics about the current dataset."""
        all_nodes = self.get_all_nodes()
        
        # Count by type
        type_counts = {}
        for node in all_nodes:
            type_counts[node.type] = type_counts.get(node.type, 0) + 1
        
        print(f"\n📊 Dataset Statistics:")
        print(f"   Total nodes: {len(all_nodes)}")
        print(f"   Node types:")
        for node_type, count in sorted(type_counts.items()):
            print(f"      {node_type}: {count}")
        
        # Count edges
        total_edges = 0
        try:
            cur = self.db.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM edges")
            result = cur.fetchone()
            if result:
                total_edges = result[0]
        except Exception:
            pass
        
        print(f"   Total edges: {total_edges}")
        
        # Show recent nodes (last 5 created)
        try:
            recent_files = []
            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    if file.endswith(('.yml', '.yaml')):
                        path = os.path.join(root, file)
                        mtime = os.path.getmtime(path)
                        recent_files.append((mtime, path))
            
            recent_files.sort(reverse=True)
            if recent_files:
                print(f"\n📅 Recently modified nodes:")
                for i, (mtime, path) in enumerate(recent_files[:5]):
                    rel_path = os.path.relpath(path, self.data_dir)
                    import datetime
                    date_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                    print(f"      {rel_path} ({date_str})")
        except Exception:
            pass
    
    def main_menu(self):
        """Display main menu and handle user selection."""
        while True:
            log.info("\n" + "="*60)
            log.info("📚 Biblical Connections Manual Editor")
            log.info("="*60)
            
            # Show quick stats
            try:
                node_count = len(self.get_all_nodes())
                log.info(f"📊 Current dataset: {node_count} nodes")
            except Exception:
                log.info(f"📊 Working directory: {self.data_dir}")
            
            choices = [
                ('➕ Add new node', 'add_node'),
                ('🔗 Add new edge', 'add_edge'),
                ('✏️  Rename node', 'rename_node'),
                ('📊 Show statistics', 'stats'),
                ('❌ Exit', 'exit')
            ]
            
            questions = [
                inquirer.List('action',
                             message="What would you like to do?",
                             choices=choices)
            ]
            
            answers = inquirer.prompt(questions)
            if not answers:
                break
            
            action = answers['action']
            
            try:
                if action == 'add_node':
                    self.add_new_node()
                elif action == 'add_edge':
                    self.add_new_edge()
                elif action == 'rename_node':
                    self.rename_node()
                elif action == 'stats':
                    self.show_stats()
                elif action == 'exit':
                    break
                    
            except KeyboardInterrupt:
                log.info("\n\n👋 Goodbye!")
                break
            except Exception as e:
                log.info(f"\n❌ Error: {e}")
                log.error(f"Unexpected error: {e}")


def main():
    """Main entry point."""
    try:
        with ManualEditor() as editor:
            editor.main_menu()
    except KeyboardInterrupt:
        log.info("\n👋 Goodbye!")
    except Exception as e:
        log.info(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()