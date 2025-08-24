import yaml
import os
from typing import Any, Dict, List, Optional
from edge_model import EdgeModel

class NodeModel:
    """
    Data Access Object for a node (person, place, tribe, etc) in the Bible Atlas.
    Loads from YAML and provides access to node data and edge relationships.
    """
    def __init__(self, data: Dict[str, Any]):
        self.id: str = data.get("id")
        self.type: str = data.get("type")
        self.names: Dict[str, str] = data.get("names", {})
        self.description: str = data.get("description", "")
        self.footnotes: Dict[str, Any] = data.get("footnotes", {})
        self.edges: List[EdgeModel] = [EdgeModel(e) for e in data.get("edges", [])]

    @classmethod
    def from_yaml_file(cls, file_path: str) -> "NodeModel":
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data)

class NodeModelCollection:
    """
    Loads all YAML files in a directory tree into NodeModel objects.
    """
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.nodes: List[NodeModel] = []
        self._load_all()

    def _load_all(self):
        for root, _, files in os.walk(self.data_dir):
            for file in files:
                if file.endswith(('.yml', '.yaml')):
                    path = os.path.join(root, file)
                    node = NodeModel.from_yaml_file(path)
                    self.nodes.append(node)

    def get_nodes(self) -> List[NodeModel]:
        return self.nodes
