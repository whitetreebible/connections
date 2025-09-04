
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
import sys
import csv
from node_model import NodeModel, EdgeModel
from associations import RECIPROCALS
import os
from logger import log


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))

def get_node_yaml_path(node_type, node_id):
    # Assumes node_type is pluralized as folder, id is filename
    folder = node_type.lower()
    return os.path.join(DATA_DIR, folder, f"{node_id}.yml")



def get_or_create_node(node_type: str, name: str) -> tuple[NodeModel, str]:
    # TODO: Use a more robust lookup for node existence and disambiguation
    node_id = name.lower()
    yaml_path = get_node_yaml_path(node_type, node_id)
    if os.path.exists(yaml_path):
        node = NodeModel.from_yaml_file(yaml_path)
    else:
        node = NodeModel({"id": node_id, "type": node_type, "name": {"en": name}, "edges": []})
    return node, yaml_path



def main():
    if len(sys.argv) < 2:
        print("Usage: python import_external.py <edges.csv>")
        sys.exit(1)
    file_path = sys.argv[1]
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=["node_type", "source", "target", "edge_type", "bible_ref"])
        for row in reader:
            # skip header
            if row["node_type"] == "node_type":
                continue
            node_type = row["node_type"].strip()
            source = row["source"].strip()
            target = row["target"].strip()
            edge_type = row["edge_type"].strip()
            bible_ref = row["bible_ref"].strip()
            
            # Get or create source and target nodes 
            source_node, source_path = get_or_create_node(node_type, source)
            target_node, target_path = get_or_create_node(node_type, target)
            edge_ref = f"bible:{bible_ref}"
            # Check for existing edge in source_node
            found = False
            for edge in source_node.edges:
                if edge.target == target_node.link and edge.type == edge_type:
                    if edge_ref not in edge.refs:
                        edge.refs.append(edge_ref)
                    found = True
                    break
            if not found:
                edge_data = {"target": target_node.link, "type": edge_type, "weight": 1.0, "refs": [edge_ref]}
                source_node.edges.append(EdgeModel(edge_data))
            # Add reciprocal edge if defined
            if edge_type in RECIPROCALS:
                reciprocal = RECIPROCALS[edge_type]
                recip_found = False
                for edge in target_node.edges:
                    if edge.target == source_node.link and edge.type == reciprocal:
                        if edge_ref not in edge.refs:
                            edge.refs.append(edge_ref)
                        recip_found = True
                        break
                if not recip_found:
                    recip_edge_data = {"target": source_node.link, "type": reciprocal, "weight": 1.0, "refs": [edge_ref]}
                    target_node.edges.append(EdgeModel(recip_edge_data))
            # Save updated YAML
            source_str = source_node.to_yaml()
            target_str = target_node.to_yaml()
            log.info(f"Added edge: {source_node.link} {edge_type} {target_node.link}")
            # write updated YAML back to files
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(source_str)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(target_str)
    print("Nodes and edges updated in YAML files from CSV.")

if __name__ == "__main__":
    main()
