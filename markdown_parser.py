import logging
import re
from dataclasses import dataclass
from markdown_it import MarkdownIt
from mdit_py_plugins.container import container_plugin
from markdown_it.tree import SyntaxTreeNode

logger = logging.getLogger(__name__)

# Markdown entry template to be used in the markdown file
md_entry_template = """
### {title}
::: {{style="font-size: 10pt;"}}
\@{ID}
<br>@{ID}
:::

::: notes

{comment}

:::
"""

@dataclass
class MarkdownPaperSection:
    """
    Represents a section in a markdown file.
    """
    title: str
    key: str
    notes: str
    heading_node: SyntaxTreeNode
    notes_node: SyntaxTreeNode

class MarkdownParser:
    """
    Parses paper section from a markdown file and provides methods to access and modify its contents.
    """
    def __init__(self, md_path):
        self.md_path = md_path
        self.md = None
        self.md_textlines = []
        self.md_tree = None
        self.md_sections = {}

        self.md = MarkdownIt()\
            .use(container_plugin, name='info') \
            .use(container_plugin, name='notes')

        self.load_md()

    def load_md(self):
        md_text = ""
        try:
            with open(self.md_path, 'r') as file:
                md_text = file.read()
        except FileNotFoundError:
            logger.info(f"File {self.md_path} not found.")

        self.md_textlines = md_text.splitlines()
        self.md_tree = SyntaxTreeNode(self.md.parse(md_text))
        self.md_sections = self.find_sections()

    def __getitem__(self, key):
        return self.md_sections[key]

    def __contains__(self, key):
        return key in self.md_sections

    def _is_paper_node(self, node):
        return node.type == 'heading' and node.tag == 'h3' and \
                    node[0].type == 'inline' and \
                    node.next_sibling.type == 'paragraph' and node.next_sibling[0].type == 'inline' and re.search(r'@(\w+)', node.next_sibling[0].content) is not None and\
                    node.next_sibling.next_sibling.type == 'container_notes'

    def find_sections(self):
        sections = {}
        for node in self.md_tree.walk():
            if self._is_paper_node(node):

                # Title = the heading
                title = node[0].content
                heading_node = node

                # Key = first group preceded by a @ in the next paragraph
                match = re.search(r'@(\w+)', node.next_sibling[0].content)
                if match:
                    key = match.group(1)
                else:
                    continue

                # Notes = the content of the notes container
                notes_node = node.next_sibling.next_sibling
                notes_start = notes_node.map[0]
                notes_end = notes_node.map[1]
                notes = '\n'.join(self.md_textlines[notes_start+1:notes_end-1])

                section = MarkdownPaperSection(
                    title=title,
                    key=key,
                    notes=notes,
                    heading_node=heading_node,
                    notes_node=notes_node
                )
                sections[key] = section
        return sections

    def update_section_notes(self, key, new_text):

        # Update the SyntaxTree
        notes_node = self.md_sections[key].notes_node
        notes_node.children = self.md.parse(new_text)

        # Update the textlines
        notes_start = notes_node.map[0]
        notes_end = notes_node.map[1]
        self.md_textlines[notes_start+1:notes_end-1] = new_text.splitlines()

        # Update the sections
        self.md_sections[key].notes = new_text
        # notes_node is unchanged

        # Refresh
        self.save()
        self.load_md()

    def regenerate_section(self, key, title=None, notes=None):
        """Replace section completely"""

        # Regenerate the section
        new_text = md_entry_template.format(title=title, ID=key, comment=notes)
        new_tokens = self.md.parse(new_text)
        new_tree = SyntaxTreeNode(new_tokens)

        # Find the old section nodes
        old_section = self.md_sections[key]
        old_heading_node = old_section.heading_node
        old_notes_node = old_section.notes_node

        # Update the SyntaxTree
        old_heading_node.replace(new_tree.children[0])
        old_notes_node.replace(new_tree.children[2])

        # Update the textlines
        heading_start = old_heading_node.map[0]
        notes_end = old_notes_node.map[1]
        self.md_textlines[heading_start:notes_end] = new_text.splitlines()

        # Update the sections
        self.md_sections[key] = MarkdownPaperSection(
            title=title,
            key=key,
            notes=notes,
            heading_node=new_tree.children[0],
            notes_node=new_tree.children[2]
        )

        # Refresh
        self.save()
        self.load_md()

    def add_section(self, key, title, notes, after_key=None):
        """Add a new section"""

        # Generate the section
        new_text = md_entry_template.format(title=title, ID=key, comment=notes)
        new_tokens = self.md.parse(new_text)
        new_tree = SyntaxTreeNode(new_tokens)

        # Find the position to insert the new section, both in the SyntaxTree and in the textlines
        if len(self.md_sections) == 0:
            last_section = None
            last_index = len(self.md_tree.children) -1
            last_index_textlines = self.md_tree.children[-1].map[1]
        else:
            if after_key is not None:
                last_section = self.md_sections[after_key]
            else:
                last_section = list(self.md_sections.values())[-1]
            last_section_notes = last_section.notes_node
            last_index = self.md_tree.children.index(last_section_notes)
            last_index_textlines = last_section_notes.map[1]

        # Insert the new section
        self.md_tree.children.insert(last_index+1, new_tree.children[0])
        self.md_tree.children.insert(last_index+2, new_tree.children[1])
        self.md_tree.children.insert(last_index+3, new_tree.children[2])

        # Update the textlines
        for line in new_text.splitlines():
            self.md_textlines.insert(last_index_textlines+1, line)
            last_index_textlines += 1

        # Update the sections
        self.md_sections[key] = MarkdownPaperSection(
            title=title,
            key=key,
            notes=notes,
            heading_node=new_tree.children[0],
            notes_node=new_tree.children[2]
        )

        # Refresh
        self.save()
        self.load_md()


    def save(self):
        with open(self.md_path, 'w') as file:
            file.write('\n'.join(self.md_textlines))
