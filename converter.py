import os
import logging
from itertools import pairwise, chain
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from markdown_parser import MarkdownParser

logger = logging.getLogger(__name__)

class Converter:
    """
    Converts bibtex files to markdown and vice versa.
    Uses MarkdownParser to parse and update markdown files.
    """

    def __init__(self, bib_path, md_path, md_template):
        """
        Initializes the Converter with paths to the bibtex file, markdown file, and markdown template.

        Args:
            bib_path (str): Path to the bibtex file.
            md_path (str): Path to the markdown file.
            md_template (str): Path to the markdown template file.
        """
        self.bib_path = bib_path
        self.md_path = md_path
        self.md_template = md_template

    def load_bibtex(self):
        """
        Loads the bibtex file.

        Returns:
            BibDatabase: The loaded bibtex database.
        """
        with open(self.bib_path, 'r') as bibfile:
            parser = BibTexParser()
            parser.customization = convert_to_unicode
            return bibtexparser.load(bibfile, parser)

    def initialize_markdown(self):
        """
        Initializes the markdown file with the template content.
        """
        with open(self.md_template, 'r') as f:
            template = f.read()
            with open(self.md_path, 'w') as mdfile:
                mdfile.write(template.format(
                    bib_file=self.bib_path,
                    bibtex=""
                ))

    def bibtex_to_markdown(self):
        """
        Converts the bibtex file to markdown format and writes/updates the markdown file.
        """
        # Read the bibtex file
        self.bib = self.load_bibtex()

        # Read/initialize the markdown file
        if not os.path.exists(self.md_path):
            logger.debug(f"Output file {self.md_path} does not exist. Creating new file.")
            self.initialize_markdown()
        self.md = MarkdownParser(self.md_path)

        # Update the markdown file, adding only the new entries, if any
        IDs_to_add = []
        Ids_to_add_prev = []
        # Go in pairs of two, to keep previous ID.
        for prev_entry, entry in pairwise(chain([None], self.bib.entries)):
            if entry['ID'] not in self.md:
                IDs_to_add.append(entry['ID'])
                Ids_to_add_prev.append(prev_entry['ID'] if prev_entry is not None else None)

        for prev_ID, ID in zip(Ids_to_add_prev, IDs_to_add):
            self.md.add_section(key=ID,
                                title=self.bib.entries_dict[ID]['title'],
                                notes=self.bib.entries_dict[ID].get('comment', ''),
                                after_key=prev_ID)

    def markdown_to_bibtex(self):
        """
        Converts the markdown file to bibtex format and updates the bibtex file.
        """
        # Read the bibtex and markdown files
        self.bib = self.load_bibtex()
        self.md = MarkdownParser(self.md_path)

        # Compare the keys in the bibtex and markdown files
        bibtex_keys = set([entry['ID'] for entry in self.bib.entries])
        md_keys = set(self.md.md_sections.keys())
        bibtex_not_in_md = bibtex_keys - md_keys
        md_not_in_bibtex = md_keys - bibtex_keys
        common_keys = bibtex_keys & md_keys

        # Warn about missing keys
        if bibtex_not_in_md:
            logger.info(f"Keys in bibtex but not in markdown: {bibtex_not_in_md}")
        if md_not_in_bibtex:
            logger.info(f"Keys in markdown but not in bibtex: {md_not_in_bibtex}")

        # Update common entries in the bibtex file
        for key in common_keys:
            self.bib.entries_dict[key]['comment'] = self.md[key].notes

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
