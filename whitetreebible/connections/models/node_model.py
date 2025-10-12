import yaml
import os
from enum import Enum
from typing import Any, Dict, List, Optional
from whitetreebible.connections.models.edge_model import EdgeModel

class NodeModel:
    """
    Data Access Object for a node (person, place, tribe, etc) in the Connections.
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
        self.footnotes: Dict[str, str] = data.get("footnotes", {})
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
        # Combine edges with the same type and target, keeping unique refs
        edge_map = {}
        for e in self.edges:
            key = (str(e.type), e.target)
            if key not in edge_map:
                edge_map[key] = e.to_dict()
                # Ensure refs is a set for uniqueness
                edge_map[key]['refs'] = set(edge_map[key].get('refs', []))
            else:
                # Merge refs
                edge_map[key]['refs'].update(e.to_dict().get('refs', []))
        # Convert refs back to sorted lists for YAML
        combined_edges = []
        for edge in edge_map.values():
            edge['refs'] = sorted(edge['refs'])
            combined_edges.append(edge)
        data['edges'] = combined_edges
        yaml_str = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(yaml_str)
        return yaml_str
    


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


class NodeType(Enum):
    # Human / kinship / social
    PERSON = "person"
    ROLE = "role"               # offices, titles, vocational roles (king, priest, prophet)
    # Supernatural
    BEING = "being"           # Yahweh, Baal, Molech, gods, spiritual beings

    # Geography / places / structures
    GROUP = "group"             # family, tribe, nation, people, collective, etc.
    PLACE = "place"             # city, region, mountain, river
    STRUCTURE = "structure"     # buildings, temple, altar, city-wall (distinct from abstract place)

    # Material / artifacts / living creatures
    OBJECT = "object"           # artifacts, tools, Ark, tablets
    ANIMAL = "animal"
    PLANT = "plant"
    CONCEPT = "concept"         # abstract ideas, e.g. sin, faith, covenant

    # Events (all kinds)
    EVENT = "event"             # historical, ritual, natural, ceremonial, etc.

    # Textual / conceptual / symbolic
    TEXT = "text"               # Scripture, books, documents
    THEME = "theme"             # abstract theological concepts (covenant, faith, sin)
    SYMBOL = "symbol"           # symbolic items/imagery (e.g., lampstand as symbol)

