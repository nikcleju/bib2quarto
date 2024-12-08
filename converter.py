import os
import logging
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from markdown_parser import MarkdownCommentsParser

logger = logging.getLogger(__name__)

class Converter:
    def __init__(self, bib_path, md_path, md_template):
        self.bib_path = bib_path
        self.md_path = md_path
        self.md_template = md_template

        # # Load bibtex
        # self.bib = self.load_bibtex()
        # # Load markdown
        # self.md = MarkdownCommentsParser(self.md_path)

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
        template = """
### {title} ({paper})
<br>@{ID}

::: notes
<!-- {ID} -->

{comment}

:::
"""
        title = entry['title']
        ID = entry['ID']
        paper = entry.get('paper', 'Unknown Paper')
        comment = entry.get('comment', '')

        return template.format(title=title, ID=ID, paper=paper, comment=comment)

    def write_full_markdown(self):
        if os.path.exists(self.md_path):
            logger.info(f"Output file {self.md_path} already exists. Exiting.")
            return

        output = ""
        if self.md_template is not None:
            with open(self.md_template, 'r') as f:
                template = f.read()
                output += template.format(
                    bib_file=self.bib_path,
                    bibtex=self.create_bibtex_md()
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

        # Read the bibtex and markdown files
        self.bib = self.load_bibtex()
        self.md = MarkdownCommentsParser(self.md_path)

        if not os.path.exists(self.md_path):
            logger.debug(f"Output file {self.md_path} does not exist. Creating new file.")
            self.write_full_markdown()

        else:
            logger.debug(f"Output file {self.md_path} exists. Updating.")
            self.update_markdown()

    def to_bibtex(self):

        # Read the bibtex and markdown files
        self.bib = self.load_bibtex()
        self.md = MarkdownCommentsParser(self.md_path)

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
