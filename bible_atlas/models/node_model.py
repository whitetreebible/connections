import yaml
import os
from typing import Any, Dict, List, Optional
from bible_atlas.models.edge_model import EdgeModel

class NodeModel:
    """
    Data Access Object for a node (person, place, tribe, etc) in the Bible Atlas.
    Loads from YAML and provides access to node data and edge relationships.
    """
    def __init__(self, data: Dict[str, Any]=None):
        data = data or {}
        self.id: str = data.get("id", "")
        self.type: str = data.get("type", "")
        # Use 'name' (singular, dict of lang:str)
        self.name: Dict[str, str] = data.get("name", {})
        # Use 'name_disambiguous' (dict of lang:str)
        self.name_disambiguous: Dict[str, str] = data.get("name_disambiguous", {})
        # Description can be dict (multilingual) or str
        desc = data.get("description", "")
        self.description: Any = desc if isinstance(desc, dict) else {"en": desc}
        self.footnotes: Dict[str, Any] = data.get("footnotes", {})
        self.edges: List[EdgeModel] = [EdgeModel(e) for e in data.get("edges", [])]

    @property
    def link(self) -> str:
        return f"{self.type}/{self.id}"


    @classmethod
    def from_yaml_file(cls, file_path: str) -> "NodeModel":
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data)



    def to_yaml(self, file_path: str = None) -> str:
        data = self.__dict__.copy()
        # Convert EdgeModel objects to dicts for YAML serialization, ensuring type is a string
        def edge_to_dict(e):
            d = e.__dict__.copy()
            d['type'] = e.type.value if hasattr(e.type, 'value') else str(e.type)
            return d
        data['edges'] = [edge_to_dict(e) for e in self.edges]
        yaml_str = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(yaml_str)
        return yaml_str
    


class NodeType:
    PERSON = "person"
    PLACE = "place"
    TRIBE = "tribe"
    NATION = "nation"
    ARTIFACT = "artifact"
    THEME = "theme"



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
