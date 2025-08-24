import re

class MdValidators:
    """
    Validator utilities for markdown node objects.
    """
    def validate_footnotes(self, node):
        """
        Checks for missing or unused footnotes in a node.
        Returns a dict with 'missing' and 'unused' lists.
        """
        referenced = set()
        # Check description
        referenced.update(self._find_footnote_refs(node.description))
        # Check notes
        if node.notes:
            for note in node.notes:
                referenced.update(self._find_footnote_refs(note))
        # Check edges
        if node.edges:
            for edge in node.edges:
                if hasattr(edge, 'refs'):
                    for ref in edge.refs:
                        if isinstance(ref, str):
                            referenced.update(self._find_footnote_refs(ref))
        defined = set(node.footnotes.keys()) if node.footnotes else set()
        missing = sorted(list(referenced - defined))
        unused = sorted(list(defined - referenced))
        return {'missing': missing, 'unused': unused}

    def _find_footnote_refs(self, text):
        if not text:
            return set()
        # Matches [^footnote_id]
        return set(re.findall(r"\[\^([a-zA-Z0-9_\-]+)\]", text))
