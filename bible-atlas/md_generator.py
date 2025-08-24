import os
import re
import logging
from node_model import NodeModelCollection
from settings import SUPPORTED_LANGS
from sqlite_atlas_db import SqliteAtlasDB
from associations_lang import ASSOCIATIONS_LANG

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)



# Markdown formatters as a class for easy inheritance/extension
class MdFormatters:

    def format_graph_all_connections(self, node, md, lang):
        """
        Output a mermaid graph of all connections for this node from the db.
        """
        db = SqliteAtlasDB()
        node_id = getattr(node, 'id', None)
        node_type = getattr(node, 'type', None)
        if not node_id or not node_type:
            return md

        node_id = f"{node_type}/{node_id}"
        # Get all edges from or to this node (1 step, both directions)
        edges = db.traverse_edges(node_id, direction="both", types=None, max_depth=None)
        log.info(f"Node {node_id} ({node_type}) has {len(edges)} edges for graph.")
        
        # Collect all node ids/types involved
        node_ids = set()
        
        for source, target, etype, weight in edges:
            node_ids.add(source)
            node_ids.add(target)
        # Get names for all nodes in this graph
        node_labels = {}
        for nodes in node_ids:
            nid, ntype = nodes.split('/')
            name = db.select_name(node_id=nid, node_type=ntype, lang=lang)
            node_labels[(nid, ntype)] = name if name else nid
        # Build mermaid graph
        lines = [] if not md else [md]
        lines.append("## All connections")
        lines.append('```mermaid')
        lines.append('graph LR;')
        for source, target, etype, weight in edges:
            label = ASSOCIATIONS_LANG.get(etype, {}).get(lang, etype)
            s = node_labels.get((source, node_type), source)
            t = node_labels.get((target, node_type), target)
            lines.append(f'    {s} -->|{label}| {t}')
        lines.append('```')
        db.close()
        return "\n".join(lines)
    

    def format_header(self, node, md, lang):
        lines = [] if not md else [md]
        # Main header: name
        name = getattr(node, 'name', None)
        if name and isinstance(name, dict):
            main_title = name.get(lang, next(iter(name.values()), node.id))
        else:
            main_title = getattr(node, 'id', 'Untitled')
        lines.append(f"# {main_title}")
        # Sub-header: name_disambiguous (if present and different from name)
        name_disamb = getattr(node, 'name_disambiguous', None)
        sub_title = None
        if name_disamb and isinstance(name_disamb, dict):
            sub_title = name_disamb.get(lang, next(iter(name_disamb.values()), None))
        if sub_title and sub_title != main_title:
            lines.append(f"## {sub_title}")
        return "\n".join(lines)

    def format_description(self, node, md, lang):
        lines = [] if not md else [md]
        desc = getattr(node, 'description', None)
        if desc and isinstance(desc, dict):
            text = desc.get(lang, next(iter(desc.values()), ''))
        else:
            text = desc or ''
        if text:
            lines.append(text + "\n")
        return "\n".join(lines)

    def format_associations(self, node, md, lang):
        lines = [] if not md else [md]
        if node.edges:
            lines.append("## Associations")
            for edge in node.edges:
                # Turn target into an id link
                target_link = self.format_links(node, f"[[{edge.target}]]", lang)
                # Get the localized association type
                assoc_type = ASSOCIATIONS_LANG.get(edge.type, {}).get(lang, edge.type)
                assoc_type = assoc_type.capitalize()
                lines.append(f"- **{assoc_type}** {target_link}")
            lines.append("")
        return "\n".join(lines)

    def format_footnotes(self, node, md, lang):
        lines = [] if not md else [md]
        if node.footnotes:
            # Find all referenced footnotes in order of appearance
            footnote_order = []
            seen = set()
            def add_footnotes_from_text(text):
                if not text:
                    return
                for match in re.finditer(r"\[\^([a-zA-Z0-9_\-]+)\]", text):
                    key = match.group(1)
                    if key not in seen:
                        footnote_order.append(key)
                        seen.add(key)
            # Description (handle multilingual dict)
            desc = getattr(node, 'description', None)
            if desc and isinstance(desc, dict):
                text = desc.get(lang, next(iter(desc.values()), ''))
            else:
                text = desc or ''
            add_footnotes_from_text(text)
            # Associations/edges
            if node.edges:
                for edge in node.edges:
                    if hasattr(edge, 'refs'):
                        for ref in edge.refs:
                            if isinstance(ref, str):
                                add_footnotes_from_text(ref)
            # Only output referenced footnotes
            for key in footnote_order:
                val = node.footnotes.get(key)
                if val:
                    text = val['text'].get(lang, '')
                    text = self.format_links(node, text, lang)
                    lines.append(f"[^{key}]: {text}")
            # Warn for unused footnotes
            unused = set(node.footnotes.keys()) - set(footnote_order)
            for key in unused:
                log.warning(f"Footnote '{key}' defined but not referenced in node '{node.id}'")
            if footnote_order:
                lines.append("")
        return "\n".join(lines)

    def format_links(self, node, md, lang=None):
        """
        Replace [[bible:Book Chapter:Verse]] with BibleHub links, and [[id]] with /type/id links.
        For internal links, use the localized name from the sqlite db if available.
        """
        db = SqliteAtlasDB()

        def biblehub_link(match):
            ref = match.group(1)
            try:
                book, chapterverse = ref.split(' ', 1)
                book_url = book.lower().replace(' ', '_')
                if book_url == 'psalm':
                    book_url = 'psalms'
                # Handle chapter or chapter:verse
                if ':' in chapterverse:
                    chapter, verse = chapterverse.split(':')
                    if '-' in verse:
                        verse = ''
                    else:
                        verse = f"-{verse}"
                else:
                    chapter = chapterverse
                    verse = ''
                url = f"https://biblehub.com/context/{book_url}/{chapter}{verse}.htm"
                return f"[{ref}]({url}){{:target=\"_blank\"}}"
            except Exception:
                return ref

        def id_link(match):
            page_id = match.group(1)
            # Try to infer type from context (node.type if available)
            node_type, node_id = page_id.split('/')
            # Use relative links for internal pages (add trailing slash for MkDocs)
            url = f"../../{page_id}/"
            # Try to get localized name from db
            link_text = page_id
            if node_type and node_id:
                db_name = db.select_name(node_type=node_type, node_id=node_id, lang=lang or "en")
                if db_name:
                    link_text = db_name
            return f"[{link_text}]({url})"

        md = re.sub(r"\[\[bible:([^\]]+)\]\]", biblehub_link, md)
        md = re.sub(r"\[\[([^\]:]+)\]\]", id_link, md)
        db.close()
        return md

class MdGenerator:
    def __init__(self, data_dir="data", docs_dir="docs", formatters=None):
        self.data_dir = data_dir
        self.docs_dir = docs_dir
        self.formatter_obj = MdFormatters()
        # Use instance methods as default formatters
        self.formatters = formatters or [
            self.formatter_obj.format_header,
            self.formatter_obj.format_description,
            self.formatter_obj.format_links,
            self.formatter_obj.format_associations,
            self.formatter_obj.format_graph_all_connections,
            self.formatter_obj.format_footnotes,
        ]
        self.nodes = NodeModelCollection(self.data_dir).get_nodes()

    def ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def generate_all(self):
        supported_langs = SUPPORTED_LANGS
        for node in self.nodes:
            for lang in supported_langs:
                # Set up language-aware title and description for formatters
                node_lang = node
                # Patch name_disambiguous
                name_disamb = getattr(node, 'name_disambiguous', None)
                if name_disamb and isinstance(name_disamb, dict):
                    node_lang.name_disambiguous = {lang: name_disamb.get(lang, next(iter(name_disamb.values()), node.id))}
                # Patch name
                name = getattr(node, 'name', None)
                if name and isinstance(name, dict):
                    node_lang.name = {lang: name.get(lang, next(iter(name.values()), node.id))}
                # Patch description
                desc = getattr(node, 'description', None)
                if desc and isinstance(desc, dict):
                    node_lang.description = {lang: desc.get(lang, next(iter(desc.values()), ''))}
                # Output to language subfolder
                rel_dir = os.path.join(self.docs_dir, lang, node.type) if node.type else os.path.join(self.docs_dir, lang)
                self.ensure_dir(rel_dir)
                md_file = os.path.join(rel_dir, f"{node.id}.md")
                content = self.run_formatters(node_lang, lang)
                with open(md_file, "w", encoding="utf-8") as f:
                    f.write(content)
                log.info(f"Generated {md_file}")

    def run_formatters(self, node, lang):
        md = ""
        for formatter in self.formatters:
            md = formatter(node, md, lang)
        return md


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate markdown from YAML node data.")
    parser.add_argument('--data-dir', default='data', help='Directory containing YAML node data')
    parser.add_argument('--docs-dir', default='docs', help='Directory to output markdown files')
    args = parser.parse_args()
    generator = MdGenerator(data_dir=args.data_dir, docs_dir=args.docs_dir)
    generator.generate_all()
