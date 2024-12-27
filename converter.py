import os
import logging
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from markdown_parser import MarkdownCommentsParser

logger = logging.getLogger(__name__)

# Markdown entry template to be used in the markdown file
md_entry_template = """
### {title} ({ID})
:::{style="font-size: 10pt;"}
@{ID}
:::

::: notes
<!-- {ID} -->

{comment}

:::
"""
# md_entry_template = """
# ### {title} ({ID})
# <br>@{ID}

# ::: notes
# <!-- {ID} -->

# {comment}

# :::
# """


class Converter:
    """
    Converts between bibtex and markdown formats.
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

    def generate_markdown_from_bibtex(self, ID_list=None):
        """
        Creates markdown content from the bibtex entries.

        Args:
            ID_list (list, optional): List of entry IDs to include in the markdown. If None, includes all entries.

        Returns:
            str: The generated markdown content.
        """
        if ID_list is None:
            ID_list = [entry['ID'] for entry in self.bib.entries]

        markdown_list = []
        for entry in self.bib.entries:
            if entry['ID'] in ID_list:
                markdown_list.append(self.build_markdown_entry(entry))
        return "\n".join(markdown_list)

    def build_markdown_entry(self, entry):
        """
        Builds markdown content for a single bibtex entry.

        Args:
            entry (dict): The bibtex entry.

        Returns:
            str: The generated markdown content for the entry.
        """

        title = entry['title']
        ID = entry['ID']
        comment = entry.get('comment', '')

        return md_entry_template.format(title=title, ID=ID, comment=comment)

    def write_initial_markdown(self):
        """
        Writes the full markdown content to the markdown file.
        If the markdown file already exists, logs a message and exits.
        """
        if os.path.exists(self.md_path):
            logger.info(f"Output file {self.md_path} already exists. Exiting.")
            return

        output = ""
        if self.md_template is not None:
            with open(self.md_template, 'r') as f:
                template = f.read()
                output += template.format(
                    bib_file=self.bib_path,
                    bibtex=self.generate_markdown_from_bibtex()
                )

        with open(self.md_path, 'w') as mdfile:
            mdfile.write(output)

    def append_new_entries_to_markdown(self):
        """
        Updates the markdown file with new bibtex entries.
        """
        # Open the markdown file for appending
        with open(self.md_path, 'a') as mdfile:
            # Add only the new entries, if any
            IDs_to_add = [entry['ID'] for entry in self.bib.entries if entry['ID'] not in self.md]
            mdfile.write(
                self.generate_markdown_from_bibtex(IDs_to_add)
            )

    def bibtex_to_markdown(self):
        """
        Converts the bibtex file to markdown format and writes/updates the markdown file.
        """
        # Read the bibtex and markdown files
        self.bib = self.load_bibtex()
        self.md = MarkdownCommentsParser(self.md_path)

        if not os.path.exists(self.md_path):
            logger.debug(f"Output file {self.md_path} does not exist. Creating new file.")
            self.write_initial_markdown()
        else:
            logger.debug(f"Output file {self.md_path} exists. Updating.")
            self.append_new_entries_to_markdown()

    def markdown_to_bibtex(self):
        """
        Converts the markdown file to bibtex format and updates the bibtex file.
        """
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
