import os
import yaml
import re



class NodeProcessor:
    """Handles loading YAML nodes and generating Markdown."""
    def __init__(self, data_dir="data", docs_dir="docs"):
        self.data_dir = data_dir
        self.docs_dir = docs_dir



    def load_yaml(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)



    def replace_links(self, text):
        """Convert [[node]] and [[ref:...]] to Markdown placeholders."""
        text = re.sub(r"\[\[ref:([^\]]+)\]\]", r"[\1](#)", text)
        text = re.sub(r"\[\[([^\]:]+)\]\]", r"[\1](#)", text)
        return text



    def format_reference_bib(self, refs):
        """Create a link to BibleHub for each reference in a comma separated list linking in the format: https://biblehub.com/context/genesis/1-14.htm"""
        links = []
        for ref in refs.get("bib", []):
            book, chapterverse = ref.split(" ")
            book = book.lower().replace(" ", "_")
            if book == "psalm":
                book = "psalms"
            chapter, verse = chapterverse.split(":")
            # if multiple verses, remove verses, link to chapter
            if '-' in verse:
                verse = ''
            else:
                verse = f"-{verse}"
            # create a _blank anchor tag
            links.append(f"<a href='https://biblehub.com/context/{book}/{chapter}{verse}.htm' target='_blank'>{ref}</a>")
        return ", ".join(links)



    def format_edges(self, edges):
        lines = []
        for edge in edges:
            target = edge.get("target")
            etype = edge.get("type")
            strength = edge.get("strength", "")
            refs = edge.get("refs", {})
            ref_str = self.format_reference_bib(refs)
            lines.append(f"- **{etype}** → {target} ({strength}; refs: {ref_str})")
        return "\n".join(lines)



    def format_refs(self, refs):
        lines = []
        for key, ref_list in refs.items():
            if key == 'bib':
                key = 'Biblical'
            if key == 'extra_bib':
                key = 'Extra-Biblical'
            lines.append(f"### {key.capitalize()} references")
            for ref in ref_list:
                if key == 'bib':
                    ref = self.format_reference_bib(ref)
                lines.append(f"- {ref}")
        return "\n".join(lines)



    def generate_markdown(self, node_data):
        md_lines = []
        md_lines.append(f"# {node_data['names'].get('english', node_data['id'])}")
        md_lines.append(f"**{node_data.get('type','')}**")
        
        if node_data.get("flags"):
            md_lines.append("(")
            md_lines.append(", ".join(node_data["flags"]))
            md_lines.append(")")
        md_lines.append("\n")
        md_lines.append(self.replace_links(node_data.get("description","")) + "\n")

        if node_data.get("notes"):
            md_lines.append("## Notes")
            for note in node_data["notes"]:
                md_lines.append(f"- {note}")
            md_lines.append("")

        if node_data.get("edges"):
            md_lines.append("## Associations")
            md_lines.append(self.format_edges(node_data["edges"]))
            md_lines.append("")

        if node_data.get("refs"):
            md_lines.append("## References")
            md_lines.append(self.format_refs(node_data["refs"]))
            md_lines.append("")

        md_lines.append("## Visualizations")
        md_lines.append("_Charts/graphs to be generated here_\n")

        return "\n".join(md_lines)



    def ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)



    def process_nodes(self):
        """Walk through all YAML files and generate Markdown."""
        for root, _, files in os.walk(self.data_dir):
            for file in files:
                if file.endswith((".yml", ".yaml")):
                    yaml_path = os.path.join(root, file)
                    node_data = self.load_yaml(yaml_path)

                    rel_path = os.path.relpath(root, self.data_dir)
                    out_dir = os.path.join(self.docs_dir, rel_path)
                    self.ensure_dir(out_dir)

                    md_file = os.path.join(out_dir, f"{node_data['id']}.md")
                    md_content = self.generate_markdown(node_data)

                    with open(md_file, "w", encoding="utf-8") as f:
                        f.write(md_content)
                    print(f"Generated {md_file}")