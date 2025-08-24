import os
import re
from node_model import NodeModel, NodeModelCollection


# Markdown formatters as a class for easy inheritance/extension
class MdFormatters:
    def format_header(self, node, md):
        lines = [] if not md else [md]
        lines.append(f"# {node.names.get('en', node.id)}")
        lines.append(f"**{node.type}**\n")
        return "\n".join(lines)

    def format_description(self, node, md):
        lines = [] if not md else [md]
        if node.description:
            lines.append(node.description + "\n")
        return "\n".join(lines)

    def format_associations(self, node, md):
        lines = [] if not md else [md]
        if node.edges:
            lines.append("## Associations")
            for edge in node.edges:
                # TODO: add language support for edge types
                # TODO: lookup target name and use it instead of edge.target
                lines.append(f"- **{edge.type}** → {edge.target}")
            lines.append("")
        return "\n".join(lines)

    def format_footnotes(self, node, md):
        lines = [] if not md else [md]
        if node.footnotes:
            for key, val in node.footnotes.items():
                text = val['text'].get('en', '')
                # Format links inside footnote text
                text = self.format_links(node, text)
                lines.append(f"[^{key}]: {text}")
            lines.append("")
        return "\n".join(lines)

    def format_links(self, node, md):
        """
        Replace [[bible:Book Chapter:Verse]] with BibleHub links, and [[id]] with /type/id links.
        """
        def biblehub_link(match):
            ref = match.group(1)
            try:
                book, chapterverse = ref.split(' ', 1)
                book_url = book.lower().replace(' ', '_')
                if book_url == 'psalm':
                    book_url = 'psalms'
                chapter, verse = chapterverse.split(':')
                if '-' in verse:
                    verse = ''
                else:
                    verse = f"-{verse}"
                url = f"https://biblehub.com/context/{book_url}/{chapter}{verse}.htm"
                return f"[{ref}]({url})"
            except Exception:
                return ref

        def id_link(match):
            page_id = match.group(1)
            url = f"/bible-atlas/{page_id}"
            return f"[{page_id}]({url})"

        md = re.sub(r"\[\[bible:([^\]]+)\]\]", biblehub_link, md)
        md = re.sub(r"\[\[([^\]:]+)\]\]", id_link, md)
        return md

class MarkdownGenerator:
    def __init__(self, data_dir="data", docs_dir="docs", formatters=None):
        self.data_dir = data_dir
        self.docs_dir = docs_dir
        self.formatter_obj = MdFormatters()
        # Use instance methods as default formatters
        self.formatters = formatters or [
            self.formatter_obj.format_header,
            self.formatter_obj.format_description,
            self.formatter_obj.format_associations,
            self.formatter_obj.format_footnotes,
            self.formatter_obj.format_links
        ]
        self.nodes = NodeModelCollection(self.data_dir).get_nodes()

    def ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def generate_all(self):
        for node in self.nodes:
            rel_dir = os.path.join(self.docs_dir, node.type) if node.type else self.docs_dir
            self.ensure_dir(rel_dir)
            md_file = os.path.join(rel_dir, f"{node.id}.md")
            content = self.run_formatters(node)
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Generated {md_file}")

    def run_formatters(self, node):
        md = ""
        for formatter in self.formatters:
            md = formatter(node, md)
        return md


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate markdown from YAML node data.")
    parser.add_argument('--data-dir', default='data', help='Directory containing YAML node data')
    parser.add_argument('--docs-dir', default='docs', help='Directory to output markdown files')
    args = parser.parse_args()
    generator = MarkdownGenerator(data_dir=args.data_dir, docs_dir=args.docs_dir)
    generator.generate_all()
