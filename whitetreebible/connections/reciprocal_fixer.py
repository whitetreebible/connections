#!/usr/bin/env python3
"""
Script to check for missing reciprocal links in the database and add them.

This script will:
1. Find all edges that should have reciprocals but are missing them
2. Add the missing reciprocal edges to the database
3. Update the corresponding YAML files with the missing edges and their references
"""

import os
import yaml
from typing import Dict, List, Tuple, Set
from collections import defaultdict

from whitetreebible.connections.logger import log
from whitetreebible.connections.sqlite_db import SqliteDB
from whitetreebible.connections.models.edge_type import EdgeType, RECIPROCALS
from whitetreebible.connections.models.edge_model import EdgeModel
from whitetreebible.connections.models.node_model import NodeModelCollection
from whitetreebible.connections.settings import DB_PATH, DATA_DIR


class ReciprocalFixer:
    def __init__(self, db: SqliteDB, data_dir: str = DATA_DIR):
        self.db = db
        self.data_dir = data_dir
        self.nodes_collection = NodeModelCollection(data_dir)
        self.missing_reciprocals = []
        self.yaml_updates = defaultdict(list)  # filename -> list of edges to add
        
    def find_missing_reciprocals(self) -> List[Tuple[str, str, EdgeType, EdgeType, List[str]]]:
        """
        Find all missing reciprocal relationships.
        Returns list of (source, target, original_type, reciprocal_type, refs)
        """
        log.info("Scanning database for missing reciprocal relationships...")
        
        # Get all edges from database
        cur = self.db.conn.cursor()
        cur.execute("SELECT source, target, type FROM edges")
        all_edges = cur.fetchall()
        
        # Convert to set for fast lookup
        existing_edges = set()
        edge_refs = {}  # (source, target, type) -> refs from original YAML
        
        for source, target, edge_type in all_edges:
            existing_edges.add((source, target, edge_type))
            
        # Load references from YAML files
        log.info("Loading edge references from YAML files...")
        for node in self.nodes_collection.get_nodes():
            node_link = f"{node.type}/{node.id}"
            for edge in node.edges:
                edge_key = (node_link, edge.target, edge.type.value)
                edge_refs[edge_key] = edge.refs
        
        missing = []
        
        for source, target, edge_type_str in all_edges:
            try:
                edge_type = EdgeType(edge_type_str)
                
                # Check if this edge type has a reciprocal
                if edge_type in RECIPROCALS:
                    reciprocal_type = RECIPROCALS[edge_type]
                    reciprocal_edge = (target, source, reciprocal_type.value)
                    
                    # Check if reciprocal exists
                    if reciprocal_edge not in existing_edges:
                        # Get original references
                        original_refs = edge_refs.get((source, target, edge_type_str), [])
                        
                        missing.append((source, target, edge_type, reciprocal_type, original_refs))
                        log.info(f"Missing reciprocal: {source} {edge_type.value} {target} -> need {target} {reciprocal_type.value} {source}")
                        
            except ValueError:
                log.warning(f"Unknown edge type: {edge_type_str}")
                continue
                
        log.info(f"Found {len(missing)} missing reciprocal relationships")
        self.missing_reciprocals = missing
        return missing
    
    def add_reciprocals_to_database(self) -> int:
        """Add missing reciprocal edges to the database."""
        if not self.missing_reciprocals:
            log.info("No missing reciprocals to add to database")
            return 0
            
        log.info(f"Adding {len(self.missing_reciprocals)} reciprocal edges to database...")
        
        added_count = 0
        for source, target, original_type, reciprocal_type, refs in self.missing_reciprocals:
            try:
                # Add reciprocal edge to database
                self.db.conn.execute(
                    "INSERT INTO edges (source, target, type) VALUES (?, ?, ?)",
                    (target, source, reciprocal_type.value)
                )
                added_count += 1
                log.debug(f"Added to DB: {target} {reciprocal_type.value} {source}")
                
            except Exception as e:
                log.error(f"Failed to add reciprocal edge {target} -> {source}: {e}")
                
        self.db.conn.commit()
        log.info(f"Successfully added {added_count} reciprocal edges to database")
        return added_count
    
    def update_yaml_files(self) -> int:
        """Update YAML files with missing reciprocal edges."""
        if not self.missing_reciprocals:
            log.info("No missing reciprocals to add to YAML files")
            return 0
            
        log.info("Preparing YAML file updates...")
        
        # Group missing reciprocals by target node (which needs the reciprocal edge added)
        updates_by_node = defaultdict(list)
        
        for source, target, original_type, reciprocal_type, refs in self.missing_reciprocals:
            # Parse target to get node type and id
            target_parts = target.split('/')
            if len(target_parts) != 2:
                log.warning(f"Invalid target format: {target}")
                continue
                
            target_type, target_id = target_parts
            updates_by_node[(target_type, target_id)].append({
                'target': source,
                'type': reciprocal_type.value,
                'refs': refs  # Use same refs as original edge
            })
        
        updated_files = 0
        
        for (node_type, node_id), edges_to_add in updates_by_node.items():
            yaml_file = os.path.join(self.data_dir, node_type, f"{node_id}.yml")
            
            if not os.path.exists(yaml_file):
                log.warning(f"YAML file not found: {yaml_file}")
                continue
                
            try:
                # Load existing YAML
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if 'edges' not in data:
                    data['edges'] = []
                
                # Add new edges
                for edge_to_add in edges_to_add:
                    # Check if edge already exists (shouldn't happen, but be safe)
                    existing = any(
                        e.get('target') == edge_to_add['target'] and 
                        e.get('type') == edge_to_add['type']
                        for e in data['edges']
                    )
                    
                    if not existing:
                        data['edges'].append(edge_to_add)
                        log.info(f"Adding to {yaml_file}: {edge_to_add['type']} -> {edge_to_add['target']}")
                
                # Write back to file
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                
                updated_files += 1
                log.info(f"Updated {yaml_file} with {len(edges_to_add)} reciprocal edge(s)")
                
            except Exception as e:
                log.error(f"Failed to update {yaml_file}: {e}")
        
        log.info(f"Updated {updated_files} YAML files")
        return updated_files
    
    def run(self, update_yaml: bool = True, update_db: bool = True) -> Dict[str, int]:
        """
        Run the complete reciprocal fixing process.
        
        Args:
            update_yaml: Whether to update YAML files
            update_db: Whether to update database
            
        Returns:
            Dictionary with counts of what was updated
        """
        results = {
            'missing_found': 0,
            'db_updated': 0,
            'yaml_files_updated': 0
        }
        
        # Find missing reciprocals
        missing = self.find_missing_reciprocals()
        results['missing_found'] = len(missing)
        
        if not missing:
            log.info("No missing reciprocals found. Database is consistent!")
            return results
        
        # Update database if requested
        if update_db:
            results['db_updated'] = self.add_reciprocals_to_database()
        
        # Update YAML files if requested
        if update_yaml:
            results['yaml_files_updated'] = self.update_yaml_files()
        
        return results


def main():
    """Main function to run the reciprocal fixer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check and fix missing reciprocal relationships")
    parser.add_argument('--data-dir', default=DATA_DIR, help='Directory containing YAML data files')
    parser.add_argument('--db-path', default=DB_PATH, help='Path to SQLite database')
    parser.add_argument('--check-only', action='store_true', help='Only check for missing reciprocals, do not fix')
    parser.add_argument('--no-yaml', action='store_true', help='Do not update YAML files')
    parser.add_argument('--no-db', action='store_true', help='Do not update database')
    
    args = parser.parse_args()
    
    # Initialize database
    db = SqliteDB(args.db_path)
    
    try:
        # Create fixer
        fixer = ReciprocalFixer(db, args.data_dir)
        
        if args.check_only:
            # Just check and report
            missing = fixer.find_missing_reciprocals()
            if missing:
                print(f"\nFound {len(missing)} missing reciprocal relationships:")
                for source, target, orig_type, recip_type, refs in missing:
                    print(f"  {source} {orig_type.value} {target} -> missing {target} {recip_type.value} {source}")
            else:
                print("No missing reciprocals found!")
        else:
            # Run the full fix
            results = fixer.run(
                update_yaml=not args.no_yaml,
                update_db=not args.no_db
            )
            
            print(f"\nReciprocal Fixer Results:")
            print(f"  Missing reciprocals found: {results['missing_found']}")
            print(f"  Database edges added: {results['db_updated']}")
            print(f"  YAML files updated: {results['yaml_files_updated']}")
            
    finally:
        db.close()


if __name__ == "__main__":
    main()