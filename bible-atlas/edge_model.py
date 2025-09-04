from typing import Any, Dict, List, Union

class EdgeModel:
    """
    Data Access Object for an edge (relationship) between nodes in the Bible Atlas.
    Each edge connects a source node to a target node with a type, weight, and refs.
    """
    def __init__(self, data: Dict[str, Any]):
        self.target: str = data.get("target")
        self.type: str = data.get("type")
        self.weight: float = float(data.get("weight", 1.0))
        self.refs: List[Union[str, Dict[str, Any]]] = data.get("refs", [])

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
