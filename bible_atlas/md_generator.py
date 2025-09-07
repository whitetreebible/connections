from bible_atlas.logger import log
from bible_atlas.models.edge_type import EdgeGroups, EdgeType, EDGE_GROUPS_ASSOCIATIONS, RECIPROCALS
from bible_atlas.models.edge_model import EdgeModel
from bible_atlas.models.node_model import NodeModelCollection, NodeModel
from bible_atlas.settings import SUPPORTED_LANGS
from bible_atlas.sqlite_db import SqliteDB
import os
import re



# Markdown formatters as a class for easy inheritance/extension
class MdFormatters:

    def filter_edges(self, edges:set[EdgeModel]) -> tuple[list[EdgeModel], list[str]]:
        edge_map = {}
        for edge in edges:
            key = tuple(sorted([edge.source, edge.target]))
            if key not in edge_map:
                edge_map[key] = []
            edge_map[key].append(edge)

        log.info(edge_map)
        filtered_edges = []
        arrows = []
        reciprocal_priority_order = list(RECIPROCALS.keys())
        # For reciprocal filtering, use the order in RECIPROCALS.keys()
        for key, group in edge_map.items():
            edge_lookup = {(e.type, e.source, e.target): e for e in group}
            used = set()
            for edge in group:
                etype = edge.type
                if etype in used:
                    continue
                has_reciprocal = etype in RECIPROCALS
                is_symmetric = RECIPROCALS.get(etype, None) == etype
                # 1. Symmetric: only keep one direction (source < target for determinism)
                if is_symmetric:
                    log.info(f"Symmetric edge {edge.source} {etype} {edge.target}")
                    used.add(etype)
                    filtered_edges.append(edge)
                    arrows.append(self.get_arrow_for_edge(edge, symmetrical=True))
                # 2. Reciprocal: only keep canonical direction (key in RECIPROCALS, source->target)
                elif has_reciprocal:
                    reciprocal_edge = edge_lookup.get((RECIPROCALS.get(etype, None), edge.target, edge.source))
                    log.info(f"Reciprocal edge {edge.source} {etype} {edge.target} (reciprocal: {reciprocal_edge.type if reciprocal_edge else "None found"})")
                    if reciprocal_edge:
                        # check if this is the better one, if so keep it, if not, continue
                        if reciprocal_priority_order.index(etype) < reciprocal_priority_order.index(reciprocal_edge.type):
                            log.info(f"Keeping edge {edge.source} {etype} {edge.target} over {reciprocal_edge.source} {reciprocal_edge.type} {reciprocal_edge.target}")
                            used.add(etype)
                            used.add(reciprocal_edge.type)
                            filtered_edges.append(edge)
                            arrows.append(self.get_arrow_for_edge(edge, symmetrical=False))
                        else:
                            continue
                    else:
                        log.info(f"Reciprocal edge {edge.source} {etype} {edge.target} has no reciprocal defined, keeping it.")
                        # the other side doesn't exist (it probably should), display
                        used.add(etype)
                        filtered_edges.append(edge)
                        arrows.append(self.get_arrow_for_edge(edge, symmetrical=False))
                # 3. Symmetric but no reciprocal defined: collapse into one (like enemy/enemy)
                elif edge_lookup.get((etype, edge.target, edge.source), None):
                    log.info(f"Symmetric (no reciprocal defined) edge {edge.source} {etype} {edge.target}")
                    used.add(etype)
                    filtered_edges.append(edge)
                    arrows.append(self.get_arrow_for_edge(edge, symmetrical=True))
                # 4. All others: keep
                else:
                    log.info(f"Normal edge {edge.source} {etype} {edge.target}, keeping it.")
                    used.add(etype)
                    filtered_edges.append(edge)
                    arrows.append(self.get_arrow_for_edge(edge, symmetrical=False))
        return filtered_edges, arrows



    def get_arrow_for_edge(self, edge:EdgeModel, symmetrical: bool) -> str:
        ARROW_DEFAULT = "--"
        ARROW_THIN = ".-"
        ARROW_THICK = "=="
        arrow_thickness = ARROW_DEFAULT
        if edge.type in [EdgeType.ANCESTOR_OF, EdgeType.DESCENDANT_OF, EdgeType.ASSOCIATED_WITH, EdgeType.VISITED]:
            arrow_thickness = ARROW_THIN
        arrow = f"<{arrow_thickness}>" if symmetrical else f"{arrow_thickness}>"
        return arrow



    def format_graph_connections(self, node:NodeModel, md, lang:str='en', title="Graph Connections", types: list[EdgeType]=None, direction="both", max_depth=None):
        """
        Output a mermaid graph of connections for this node from the db, with customizable parameters.
        """
        db = SqliteDB()
        if not node.link:
            return md

        # Get edges based on parameters
        edges = db.traverse_edges(start_node_link=node.link, direction=direction, types=types, max_depth=max_depth)
        log.info(f"Node {node.link} has {len(edges)} edges for graph.")

        # Collect all node ids/types involved
        node_links = set()
        for edge in edges:
            node_links.add(edge.source)
            node_links.add(edge.target)

        # Get names for all nodes in this graph, using format_links for link formatting
        node_labels = {}
        links = {}
        for node_link in node_links:
            ntype, nid = node_link.split('/')
            # Use format_links to get the formatted link (as markdown)
            name = db.select_name(node_type=ntype, node_id=nid, lang=lang)
            if name:
                node_labels[node_link] = name
                # Also store the formatted link
                partial_node = NodeModel()
                partial_node.type = ntype
                partial_node.id = nid
                links[node_link] = self.format_links(node=partial_node, lang=lang)
            else:
                node_labels[node_link] = node_link  # fallback to id if name not found

        # Build mermaid graph with sort order by edge directionality
        lines = [] if not md else [md]
        lines.append(f"## {title}")
        lines.append('```mermaid')
        lines.append('graph LR;')
        # Style current node
        lines.append(f"    style {node.link} fill:#2fa4e7,stroke:#333,stroke-width:4px;")

        # Add labels
        for node_link, label in node_labels.items():
            if node_link != label:
                lines.append(f'    {node_link}(["{label}"])')

        # Add clickable links
        for node_link, link in links.items():
            link_location = link.split('(')[-1].rstrip('){:target="_blank"}')
            link_location = f'"{link_location}"'
            lines.append(f"    click {node_link} {link_location}")

        # Add edges
        filtered_edges, arrows = self.filter_edges(edges=edges)
        for edge, arrow in zip(filtered_edges, arrows):
            edge_type:EdgeType = edge.type
            label = edge_type.for_lang(lang=lang, capitalize=True)
            edge_str = f'    {edge.source} {arrow}|{label}| {edge.target}'
            lines.append(edge_str)
        lines.append('```')
        db.close()
        log.info(f"Generated mermaid graph with {len(filtered_edges)} edges.")
        return "\n".join(lines)



    def format_graph_family_connections(self, node, md, lang):
        group = EdgeGroups.FAMILY
        title = group.for_lang(lang=lang, capitalize=True)
        types = EDGE_GROUPS_ASSOCIATIONS.get(group, None)
        return self.format_graph_connections(node, md, lang, title=title, direction="both", types=types, max_depth=4)



    def format_graph_all_connections(self, node, md, lang):
        return self.format_graph_connections(node, md, lang, title="All connections", direction="both", types=None, max_depth=None) 



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
                # Show refs in readable format (bible:..., footnote:...)
                ref_strs = []
                for ref in getattr(edge, 'refs', []):
                    if isinstance(ref, str):
                        if ref.startswith('bible:'):
                            ref_strs.append(f"[[{ref}]]")
                        elif ref.startswith('footnote:'):
                            ref_strs.append(f"[^{ref.split(':',1)[1]}]")
                refs_display = f" ({', '.join(ref_strs)})" if ref_strs else ""
                edge_type:EdgeType = edge.type
                label = edge_type.for_lang(lang=lang, capitalize=True)
                lines.append(f"- **{label}** {target_link}{refs_display}")
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
                # Find [^footnote] and footnote:... references
                for match in re.finditer(r"\[\^([a-zA-Z0-9_\-]+)\]", text):
                    key = match.group(1)
                    if key not in seen:
                        footnote_order.append(key)
                        seen.add(key)
                for match in re.finditer(r"footnote:([a-zA-Z0-9_\-]+)", text):
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



    def format_links(self, node=None, md=None, lang='en'):
        """
        Replace [[bible:Book Chapter:Verse]] with BibleHub links, and [[id]] with /type/id links.
        For internal links, use the localized name from the sqlite db if available.
        """
        db = SqliteDB()

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

        response = None
        if md:
            response = re.sub(r"\[\[bible:([^\]]+)\]\]", biblehub_link, md)
            response = re.sub(r"\[\[([^\]:]+)\]\]", id_link, response)
        elif node:
            # create an id_link match for the current node
            id_link_match = re.match(r"\[\[([^\]:]+)\]\]", f"[[{node.type}/{node.id}]]")
            if id_link_match:
                response = id_link(match=id_link_match)
        db.close()
        return response



class MdGenerator:
    def __init__(self, data_dir="data", docs_dir="docs", formatters=None):
        self.data_dir = data_dir
        self.docs_dir = docs_dir
        self.formatter_obj = MdFormatters()
        # Use instance methods as default formatters
        self.formatters = formatters or [
            self.formatter_obj.format_header,
            self.formatter_obj.format_description,
            self.formatter_obj.format_associations,
            self.formatter_obj.format_links,
            self.formatter_obj.format_graph_family_connections,
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



def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate markdown from YAML node data.")
    parser.add_argument('--data-dir', default='data', help='Directory containing YAML node data')
    parser.add_argument('--docs-dir', default='docs', help='Directory to output markdown files')
    args = parser.parse_args()
    generator = MdGenerator(data_dir=args.data_dir, docs_dir=args.docs_dir)
    generator.generate_all()



if __name__ == "__main__":
    main()
