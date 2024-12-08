import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
import mistune
from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin
from mdit_py_plugins.container import container_plugin
from markdown_it.tree import SyntaxTreeNode
from mdformat.renderer import MDRenderer
import os
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).setLevel(logging.DEBUG)
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
                        .use(container_plugin, name='\"{.content-hidden unless-format="xxx"}\"')

        try:
            with open(self.md_path, 'r') as file:
                self.md_text = file.read()
                self.md_tokens = self.md.parse(self.md_text)
                self.md_tree = SyntaxTreeNode(self.md_tokens)
        except FileNotFoundError:
            logger.error(f"File {self.md_path} not found.")
            self.md_tokens = []

        # Parse comments
        for i, token in enumerate(self.md_tokens):
            if token.type == 'container_notes_open':

                # Find ID
                ID, ID_position = self.find_ID(start_position=i)

                # # Find closing token
                # closing_token, closing_token_position = self.find_closing_token(start_position=ID_position)

                # Get comment
                # comment = self.md.renderer.render(self.md_tokens[ID_position+1:closing_token_position], {}, {})
                comment = self.find_text_between(self.md_tokens[ID_position].content, ':::')
                comment = comment.strip()
                self.md_comments[ID] = comment



    def find_ID(self, start_position):
        # Find the ID of a container
        for token_position, token in enumerate(self.md_tokens[start_position:], start=start_position):
            if token.type == 'html_block':
                return token.content.strip().strip('<!--').strip('-->').strip(), token_position

        # Should never reach here
        raise ValueError(f"ID not found")

    def find_closing_token(self, start_position):
        # Find the closing token of a container
        for token_position, token in enumerate(self.md_tokens[start_position:], start=start_position):
            if token.type == f'container_notes_close':
                return token, token_position

        # Should never reach here
        raise ValueError(f"Closing token not found")

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


class BibTeXConverter:
    def __init__(self, bib_path, md_path, md_template):
        self.bib_path = bib_path
        self.md_path = md_path
        self.md_template = md_template

        # Load bibtex
        self.bib = self.load_bibtex()
        # Load markdown
        self.md = MarkdownCommentsParser(self.md_path)
        pass

    def load_bibtex(self):
        with open(self.bib_path, 'r') as bibfile:
            parser = BibTexParser()
            parser.customization = convert_to_unicode
            return bibtexparser.load(bibfile, parser)

    def create_bibtex_md(self, ID_list=None):

        if ID_list is None:
            ID_list = [entry['ID'] for entry in self.bib.entries]

        markdown_list = []
        for entry in self.bib.entries:
            if entry['ID'] in ID_list:
                markdown_list.append(self.build_paper_md(entry))
        return "\n".join(markdown_list)

    def build_paper_md(self, entry):

        template="""
### {title}
<br>@{ID}

::: notes
<!-- {ID} -->

{comment}

:::

"""
        title = entry['title']
        ID = entry['ID']
        comment = entry['comment'] if 'comment' in entry else ''

        return template.format(title=title, ID=ID, comment=comment)

    def write_full_markdown(self):

        # If output file exists
        if os.path.exists(self.md_path):
            print(f"Output file {self.md_path} already exists. Exiting.")

        # Read the template
        output = ""
        if self.md_template is not None:
            with open(self.md_template, 'r') as f:
                template = f.read()
                output += template.format(
                                    bib_file=self.bib_path,
                                    bibtex = self.create_bibtex_md()
                    )

        with open(self.md_path, 'w') as mdfile:
            mdfile.write(output)

    def update_markdown(self):

        # Open the markdown file for appending
        with open(self.md_path, 'a') as mdfile:
            # Add only the new entries, if any
            IDs_to_add = [entry['ID'] for entry in self.bib.entries if entry['ID'] not in self.md]
            mdfile.write(
                self.create_bibtex_md(IDs_to_add)
            )

    def to_markdown(self):
        if not os.path.exists(self.md_path):
            logger.debug(f"Output file {self.md_path} does not exist. Creating new file.")
            self.write_full_markdown()

        else:
            logger.debug(f"Output file {self.md_path} exists. Updating.")
            self.update_markdown()

    def to_bibtex(self):

        # Update bibtex entries
        for entry in self.bib.entries:
            if entry['ID'] in self.md:
                entry['comment'] = self.md[entry['ID']]
            else:
                logger.debug(f"Comment for {entry['ID']} not found in markdown")

        # JabRef: Get the encoding line
        encoding_line = None
        for index, comment in enumerate(self.bib.comments):
            if comment.startswith('% Encoding:'):
                encoding_line = comment
                del self.bib.comments[index]
                break
        if encoding_line is None:
            logger.info("Encoding line not found")

        with open(self.bib_path, 'w') as bibfile:

            # Write the encoding line
            if encoding_line is not None:
                bibfile.write(encoding_line + '\n')

            bibtexparser.dump(self.bib, bibfile)

# Run
converter = BibTeXConverter(
    "CeCitesc.bib",
    "output.qmd",
    "template.qmd")

#converter.to_markdown()
converter.to_bibtex()
