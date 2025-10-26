"""
Script to process a CSV with columns: node_type, source, target, edge_type.
For each row, verifies that source and target nodes exist (creates if missing),
adds the specified edge, and adds a reciprocal edge if appropriate.

Usage:
    python import_external.py <edges.csv>
CSV example:
    person, Seth, Enos, parent-of
    person, Enos, Seth, child-of
"""
from whitetreebible.connections.logger import log
from whitetreebible.connections.models.edge_type import EdgeType, RECIPROCALS
from whitetreebible.connections.models.node_model import NodeModel, EdgeModel
from whitetreebible.connections.sqlite_db import SqliteDB
import csv
import inquirer
import os
import sys


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))

_disambig_cache = {}
_name_matches_to_add = []  # Track name-matches relationships to add at the end


def lookup_similar_nodes(node_type: str, name: str) -> list:
    """
    Try to find similar nodes by name using the DB if available, else scan YAML files.
    Returns a list of (id, type, name, name_disambiguous) dicts.
    If name_disambiguous is empty, construct it from name and first edge, or fallback to type/id.
    """
    results = []
    name_norm = name.strip().lower()
    seen_ids = set()
    # Always check DB
    try:
        db = SqliteDB()
        cur = db.conn.cursor()
        cur.execute("SELECT id, type, name FROM nodes WHERE type = ?", (node_type,))
        for row in cur.fetchall():
            node_id, ntype, n_en = row[0], row[1], row[2]
            node_id_norm = str(node_id).strip().lower()
            n_en_norm = str(n_en).strip().lower()
            if name_norm == node_id_norm or name_norm == n_en_norm:
                yaml_path = get_node_yaml_path(ntype, node_id)
                n_disamb = ''
                if os.path.exists(yaml_path):
                    try:
                        node = NodeModel.from_yaml_file(yaml_path)
                        n_disamb = node.name_disambiguous.get('en', '') if hasattr(node, 'name_disambiguous') else ''
                        if not n_disamb:
                            if node.edges:
                                first_edge = node.edges[0]
                                n_disamb = format_disambiguous_from_edge(node_id, n_en, first_edge.type, first_edge.target)
                            else:
                                n_disamb = format_disambiguous_from_edge(node_id, n_en, '', '')
                    except Exception:
                        n_disamb = n_en or f"{ntype}/{node_id}"
                else:
                    n_disamb = n_en or f"{ntype}/{node_id}"
                results.append({"id": node_id, "type": ntype, "name": n_en, "name_disambiguous": n_disamb})
                seen_ids.add((ntype, node_id_norm))
    except Exception as e:
        log.warning(f"DB lookup failed: {e}")
    # Always check YAML files
    data_dir = os.path.join(DATA_DIR, node_type.lower())
    if os.path.exists(data_dir):
        for fname in os.listdir(data_dir):
            if fname.endswith('.yml') or fname.endswith('.yaml'):
                path = os.path.join(data_dir, fname)
                node_id_from_file = os.path.splitext(fname)[0].strip().lower()
                try:
                    node = NodeModel.from_yaml_file(path)
                    n_en = node.name.get('en', '')
                    n_en_norm = n_en.strip().lower()
                    n_disamb = node.name_disambiguous.get('en', '') if hasattr(node, 'name_disambiguous') else ''
                    if not n_disamb:
                        if node.edges:
                            first_edge = node.edges[0]
                            n_disamb = format_disambiguous_from_edge(node.id, n_en, first_edge.type, first_edge.target)
                        else:
                            n_disamb = format_disambiguous_from_edge(node.id, n_en, '', '')
                    # Match on filename or name_en
                    if (name_norm == node_id_from_file or name_norm == n_en_norm) and (node.type, node_id_from_file) not in seen_ids:
                        results.append({"id": node.id, "type": node.type, "name": n_en, "name_disambiguous": n_disamb})
                        seen_ids.add((node.type, node_id_from_file))
                except Exception as e:
                    log.warning(f"YAML lookup failed for {fname}: {e}")
    log.info(f"lookup_similar_nodes('{node_type}', '{name}') found {len(results)} matches: {[r['id'] for r in results]}")
    return results



def format_disambiguous_from_edge(node_id, name, edge_type:EdgeType, edge_target) -> str:
    if not name:
        name = node_id.capitalize()
    
    # Capitalize the base name for persons
    name = name.title()
    
    if not edge_type:
        return name
    
    # Special handling for parent/child relationships
    if hasattr(edge_type, 'value'):
        edge_type_str = edge_type.value
    else:
        edge_type_str = str(edge_type)
    
    # Extract target name from the link (remove type prefix)
    if '/' in edge_target:
        target_type, target_name = edge_target.split('/', 1)
        # Capitalize if it's a person type
        if target_type.lower() == 'person':
            target_name = target_name.replace('-', ' ').replace('_', ' ').title()
        else:
            target_name = target_name.replace('-', ' ').replace('_', ' ')
    else:
        target_name = edge_target
        target_name = target_name.replace('-', ' ').replace('_', ' ').title()
    
    # Format parent/child relationships specially
    if edge_type_str == "child-of":
        # This node is the child, so format as "Child (son of Parent)"
        return f"{name} (son of {target_name})"
    elif edge_type_str == "parent-of":
        # This node is the parent, so format as "Parent (father of Child)"
        return f"{name} (father of {target_name})"
    else:
        # Keep existing format for other edge types
        edge_type_display = edge_type_str.replace('-', ' ')
        return f"{name} ({edge_type_display} {target_name})"



def get_node_yaml_path(node_type, node_id):
    """Helper to get the YAML file path for a node by type and id."""
    data_dir = os.path.join(DATA_DIR, node_type.lower())
    for ext in ('.yml', '.yaml'):
        path = os.path.join(data_dir, f"{node_id}{ext}")
        if os.path.exists(path):
            return path
    return os.path.join(data_dir, f"{node_id}.yml")


def add_name_matches_relationship(base_name: str, node1: NodeModel, node2: NodeModel):
    """Track a name-matches relationship to be added later."""
    _name_matches_to_add.append((base_name, node1, node2))


def create_name_matches_edges():
    """Create all pending name-matches edges between nodes with the same base name."""
    log.info(f"Creating {len(_name_matches_to_add)} name-matches relationships...")
    
    for base_name, node1, node2 in _name_matches_to_add:
        # Add name-matches edge from node1 to node2
        found = False
        for edge in node1.edges:
            if edge.target == node2.link and edge.type == EdgeType.NAME_MATCHES:
                found = True
                break
        if not found:
            edge_data = {
                "target": node2.link,
                "type": EdgeType.NAME_MATCHES,
                "refs": []
            }
            node1.edges.append(EdgeModel(edge_data))
            log.info(f"Added name-matches: {node1.link} -> {node2.link}")

        # Add name-matches edge from node2 to node1 (symmetric relationship)
        found = False
        for edge in node2.edges:
            if edge.target == node1.link and edge.type == EdgeType.NAME_MATCHES:
                found = True
                break
        if not found:
            edge_data = {
                "target": node1.link,
                "type": EdgeType.NAME_MATCHES,
                "refs": []
            }
            node2.edges.append(EdgeModel(edge_data))
            log.info(f"Added name-matches: {node2.link} -> {node1.link}")

        # Save both nodes
        node1_path = get_node_yaml_path(node1.type, node1.id)
        node2_path = get_node_yaml_path(node2.type, node2.id)
        
        os.makedirs(os.path.dirname(node1_path), exist_ok=True)
        os.makedirs(os.path.dirname(node2_path), exist_ok=True)
        
        with open(node1_path, 'w', encoding='utf-8') as f:
            f.write(node1.to_yaml())
        with open(node2_path, 'w', encoding='utf-8') as f:
            f.write(node2.to_yaml())



def get_or_create_node(node_type: str, name: str, bible_ref: str, context: str, edge_type: EdgeType = None, target_link: str = None) -> tuple[NodeModel, str]:
    cache_key = (node_type, name, bible_ref)
    if cache_key in _disambig_cache:
        node_id = _disambig_cache[cache_key]
        yaml_path = get_node_yaml_path(node_type, node_id)
        node = NodeModel.from_yaml_file(yaml_path) if os.path.exists(yaml_path) else NodeModel({"id": node_id, "type": node_type, "name": {"en": name}, "edges": []})
        return node, yaml_path
    # Look for similar nodes
    matches = lookup_similar_nodes(node_type, name)
    log.info(f"Looking up {node_type} named '{name}' found {len(matches)} matches.")
    node_id = name.lower()
    
    if matches:
        choices = []
        create_new_label = f"Create new: {name} ({node_type}/{node_id})"
        for m in matches:
            label = f"{m['type']}/{m['id']}"
            if m.get('name_disambiguous'):
                label = f"{m['name_disambiguous']}"
            choices.append((label, m['id']))
        choices.append((create_new_label, None))
        answer = inquirer.list_input(
            f"Which {name} is in {bible_ref} ({context})?",
            choices=choices,
            default=choices[0][1] if choices else None
        )
        # Robustly detect 'Create new' selection (None or label string)
        if answer in [m['id'] for m in matches]:
            node_id = answer
            _disambig_cache[cache_key] = node_id
            yaml_path = get_node_yaml_path(node_type, node_id)
            node = NodeModel.from_yaml_file(yaml_path)
            return node, yaml_path
        if answer is None or (isinstance(answer, str) and answer.startswith('Create new:')):
            default_id = f"{node_id}_{bible_ref.lower().replace(' ', '_').replace(':', '_')}"
            new_id = inquirer.text(message=f"Please provide a disambiguated id for new '{name}' in {node_type} (e.g., lamech_murderer):")
            if new_id:
                node_id = new_id.strip()
                _disambig_cache[cache_key] = node_id
                
                # Track name-matches relationships when creating disambiguated nodes
                for match in matches:
                    if match['name'].lower() == name.lower():
                        # Load the existing node to add name-matches relationship
                        existing_yaml_path = get_node_yaml_path(match['type'], match['id'])
                        if os.path.exists(existing_yaml_path):
                            try:
                                existing_node = NodeModel.from_yaml_file(existing_yaml_path)
                                # We'll create the new node below, then add the relationship
                                # Store for later processing
                                add_name_matches_relationship(name, None, existing_node)  # placeholder for new node
                            except Exception as e:
                                log.warning(f"Could not load existing node for name-matches: {e}")
            else:
                node_id = default_id
    # Default: create new node
    _disambig_cache[cache_key] = node_id
    yaml_path = get_node_yaml_path(node_type, node_id)
    
    # Capitalize names for person types
    display_name = name.title() if node_type.lower() in ['person', 'place', 'group'] else name
    
    # Set a meaningful disambiguated name if possible
    if edge_type and target_link and node_type.lower() == 'person':
        # Use the edge-based formatting for parent/child relationships
        disamb = format_disambiguous_from_edge(node_id, display_name, edge_type, target_link)
    elif context:
        # Capitalize the disambiguous name too for person types
        if node_type.lower() == 'person':
            disamb = f"{display_name} ({context})"
        else:
            disamb = f"{name} ({context})"
    else:
        disamb = display_name
    
    node = NodeModel({
        "id": node_id,
        "type": node_type,
        "name": {"en": display_name},
        "name_disambiguous": {"en": disamb},
        "edges": []
    })
    
    # Update any pending name-matches relationships with the actual new node
    for i, (base_name, placeholder_node, existing_node) in enumerate(_name_matches_to_add):
        if placeholder_node is None and base_name == name:
            _name_matches_to_add[i] = (base_name, node, existing_node)
    
    log.info(f"New node: {node_type}/{node_id}")
    return node, yaml_path



def main():
    if len(sys.argv) < 2:
        print("Usage: python import_external.py <edges.csv>")
        sys.exit(1)
    file_path = sys.argv[1]
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=[
            "source", "edge_type", "target",
            "ref_bible", "ref_footnote_anchor", "ref_footnote_text"
        ])
        for row in reader:
            # skip header
            if row["source"] == "source":
                continue
            s_type, s_name = row["source"].strip().split('/')
            edge_type = EdgeType(row["edge_type"].strip())
            t_type, t_name = row["target"].strip().split('/')
            ref_bible = None
            if row["ref_bible"] is not None:
                ref_bible = row["ref_bible"].strip()
            ref_footnote_anchor = None
            if row["ref_footnote_anchor"] is not None:
                ref_footnote_anchor = row["ref_footnote_anchor"].strip()
            ref_footnote_text = None
            if row["ref_footnote_text"] is not None:
                ref_footnote_text = row["ref_footnote_text"].strip()

            # Get or create source and target nodes
            readable_edge = edge_type.for_lang(lang="en")
            context = f"{s_name} {readable_edge} {t_name}"
            
            # First create target node (needed for source node's disambiguous name)
            reciprocal_edge = RECIPROCALS.get(edge_type) if edge_type in RECIPROCALS else None
            target_node, target_path = get_or_create_node(t_type, t_name, ref_bible, context=context, 
                                                        edge_type=reciprocal_edge, target_link=f"{s_type}/{s_name}")
            
            # Then create source node with target info
            source_node, source_path = get_or_create_node(s_type, s_name, ref_bible, context=context, 
                                                        edge_type=edge_type, target_link=target_node.link)


            # Build refs, including bible and footnote refs
            edge_refs = []
            if ref_bible:
                # remove quotes if present
                ref_bible = ref_bible.strip('"').strip("'")
                edge_refs.append(f"bible:{ref_bible}")

            # Add footnote to node's footnotes dict if anchor/text present
            anchor = ref_footnote_anchor if ref_footnote_anchor else ''
            text = ref_footnote_text if ref_footnote_text else ''
            if anchor:
                # Add to source_node.footnotes (create if missing)
                if not hasattr(source_node, 'footnotes') or source_node.footnotes is None:
                    source_node.footnotes = {}
                if anchor not in source_node.footnotes:
                    source_node.footnotes[anchor] = {"en": text} if text else {}
                elif text:
                    # Update text if anchor exists but text is missing
                    if not source_node.footnotes[anchor].get("en"):
                        source_node.footnotes[anchor]["en"] = text
                # Add footnote:<anchor> to refs
                edge_refs.append(f"footnote:{anchor}")

            # Check for existing edge in source_node
            found = False
            for edge in source_node.edges:
                if edge.target == target_node.link and edge.type == edge_type:
                    for ref in edge_refs:
                        if ref and ref not in edge.refs:
                            edge.refs.append(ref)
                    found = True
                    break
            if not found:
                edge_data = {
                    "target": target_node.link,
                    "type": edge_type,
                    "refs": edge_refs
                }
                source_node.edges.append(EdgeModel(edge_data))

            # Add reciprocal edge if defined
            if edge_type in RECIPROCALS:
                reciprocal = RECIPROCALS[edge_type]
                recip_found = False
                # Only mirror non-footnote refs (e.g., bible refs) to reciprocal edge
                mirrored_refs = [ref for ref in edge_refs if not (isinstance(ref, str) and ref.startswith("footnote:"))]
                for edge in target_node.edges:
                    edge_type_val = edge.type.value if hasattr(edge.type, 'value') else edge.type
                    if edge.target == source_node.link and edge_type_val == reciprocal:
                        for ref in mirrored_refs:
                            if ref and ref not in edge.refs:
                                edge.refs.append(ref)
                        recip_found = True
                        break
                if not recip_found:
                    recip_edge_data = {
                        "target": source_node.link,
                        "type": reciprocal,
                        "refs": mirrored_refs
                    }
                    target_node.edges.append(EdgeModel(recip_edge_data))

            # Save updated YAML (write only once after all edge modifications)
            source_str = source_node.to_yaml()
            target_str = target_node.to_yaml()
            log.info(f"New edge: {source_node.link} {edge_type} {target_node.link}")
            # Ensure parent directories exist before writing
            os.makedirs(os.path.dirname(source_path), exist_ok=True)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(source_str)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(target_str)
    
    # Create all pending name-matches relationships
    create_name_matches_edges()
    
    print("Nodes and edges updated in YAML files from CSV.")
    print(f"Added {len(_name_matches_to_add)} name-matches relationships.")

if __name__ == "__main__":
    main()
