import logging
from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_block_plugin
from mdit_py_plugins.container import container_plugin
from markdown_it.tree import SyntaxTreeNode

logger = logging.getLogger(__name__)

class MarkdownCommentsParser:
    def __init__(self, md_path):
        self.md_path = md_path
        self.md = None
        self.md_text = ''
        self.md_tokens = []
        self.md_tree = None
        self.md_comments = {}

        self.md = MarkdownIt()\
            .use(attrs_block_plugin, allowed=['paper'])\
            .use(container_plugin, name='notes')\
            .use(container_plugin, name='\"{.content-hidden unless-format=\"xxx\"}\"')

        try:
            with open(self.md_path, 'r') as file:
                self.md_text = file.read()
                self.md_tokens = self.md.parse(self.md_text)
                self.md_tree = SyntaxTreeNode(self.md_tokens)
        except FileNotFoundError:
            logger.error(f"File {self.md_path} not found.")
            self.md_tokens = []

        self.parse_comments()

    def parse_comments(self):
        for i, token in enumerate(self.md_tokens):
            if token.type == 'container_notes_open':
                ID, ID_position = self.find_ID(start_position=i)
                comment = self.find_text_between(self.md_tokens[ID_position].content, ':::')
                comment = comment.strip()
                self.md_comments[ID] = comment

    def find_ID(self, start_position):
        for token_position, token in enumerate(self.md_tokens[start_position:], start=start_position):
            if token.type == 'html_block':
                return token.content.strip().strip('<!--').strip('-->').strip(), token_position
        raise ValueError("ID not found")

    def find_text_between(self, start_delimiter, end_delimiter):
        text = self.md_text.split(start_delimiter)[1].split(end_delimiter)[0]
        return text

    def __getitem__(self, key):
        return self.md_comments[key]

    def __setitem__(self, key, value):
        self.md_comments[key] = value

    def __delitem__(self, key):
        del self.md_comments[key]

    def __iter__(self):
        return iter(self.md_comments)
