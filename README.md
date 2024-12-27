# BibTeX / Markdown Converter

Convert BibTeX entries into a Quarto/Markdown file and vice-versa, keeping the `.bib` file in sync with the Markdown file.

**Goal**: keep all papers in a `.bib` file, but edit notes in a Markdown file for a nice reading experience,
while keeping the two files in sync.

1. Create a Markdown file with papers & notes from a BibTeX .bib file.
2. When new references are added to the BibTeX file, the Markdown file is automatically updated (new entries are appended).
3. When paper notes are added to the Markdown file, the BibTeX file is automatically updated.

Limitations:

- Only new references added to the BibTeX file are appended to the Markdown file.
- Only paper comments in the Markdown file are updated in the BibTeX file.

For now, the app only supports the IEEE citation style.

The `.bib` file follows the JabRef format, i.e. the comments are stored in the `comment` field.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/nikcleju/bib2quarto
    cd bib2quarto
    ```

2. Install the required Python packages (preferrably in a virtual environment):
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Edit the `config.yml` file to specify the paths to the BibTeX and Markdown files, and optionally the Markdown template
    ```yaml
    - bib: "database.bib"
      md: "database.qmd"
    ```
    - `bib`: Path to the BibTeX file.
    - `md`: Path to the Markdown file.
    - `template`: Optional path to a Markdown template (i.e. containing the front matter). If not given, the default template `template.qmd` will be used.

2. Customize the `template.qmd` file if needed.

3. Run the app:
    ```sh
    python bib2quarto.py
    ```

    Pass the optional `--config` argument to specify a different configuration file:
    ```sh
    python bib2quarto.py --config <config-file>
    ```
    The default configuration file is `config.yml`.

    You can also modify the shell script `bib2quarto.sh` to run the app.

4. The app watches for changes in the BibTeX and Markdown files:
    - If the BibTeX file is updated, the Markdown file will be automatically updated.
    - If the Markdown file is updated, the BibTeX file will be updated accordingly.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
