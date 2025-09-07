from typing import Any, Dict, List, Union
from .edge_type import EdgeType

class EdgeModel:

    """
    Data Access Object for an edge (relationship) between nodes in the Bible Atlas.
    Each edge connects a source node to a target node with a type, and refs.
    """
    def __init__(self, data: Dict[str, Any]):
        self.source: str = data.get("source", "")
        self.target: str = data.get("target", "")
        self.type: EdgeType = EdgeType(data.get("type", ""))
        self.refs: List[Union[str, Dict[str, Any]]] = data.get("refs", [])

    def __eq__(self, other):
        if not isinstance(other, EdgeModel):
            return False
        return (self.target, self.type) == (other.target, other.type)

    def __hash__(self):
        return hash((self.target, self.type))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            # source is implicit in context for yaml so do not serialize it
            "target": self.target,
            "type": self.type.value if hasattr(self.type, 'value') else str(self.type),
            "refs": self.refs
        }



    def __repr__(self):
        return f"Edge {self.source} {self.type} {self.target}"



    @staticmethod
    def from_row(row: tuple) -> "EdgeModel":
        source, target, etype = row
        return EdgeModel({"source": source, "target": target, "type": etype, "refs": []})



    @staticmethod
    def parse_refs(refs: List[Union[str, Dict[str, Any]]]) -> Dict[str, List[str]]:
        """
        Categorize refs into page_ids, bible refs, and footnotes.
        Supports both [[bible:...]] and bible:... (and footnote:...) formats in refs.
        Returns a dict with keys: 'page', 'bible', 'footnote'.
        """
        result = {"page": [], "bible": [], "footnote": []}
        for ref in refs:
            if isinstance(ref, str):
                # New readable format: bible:... or footnote:...
                if ref.startswith("bible:"):
                    result["bible"].append(ref)
                elif ref.startswith("footnote:"):
                    result["footnote"].append(ref)
                # Old format: [[bible:...]]
                elif ref.startswith("[[bible:") and ref.endswith("]]"):
                    result["bible"].append(ref[2:-2])  # strip brackets for consistency
                elif ref.startswith("[[") and ref.endswith("]]"):
                    inner = ref[2:-2]
                    if not inner.startswith("bible:"):
                        result["page"].append(inner)
                elif ref.startswith("[^") and ref.endswith("]"):
                    result["footnote"].append(ref)
            # else: ignore dict/other for now
        return result
