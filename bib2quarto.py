import logging
import argparse
from omegaconf import OmegaConf

from converter import Converter
from syncer import Bib2QuartoSyncer

logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).setLevel(logging.DEBUG)

if __name__ == "__main__":
    """
    Main entry point for the script.
    Parses arguments, loads configuration, and starts the sync observers.
    """
    args = argparse.ArgumentParser(description="Converts a bibtex file to markdown and vice versa.")
    args.add_argument("--config", type=str, default='config.yml', help="Path to the configuration file.")
    args = args.parse_args()
    conf = OmegaConf.load(args.config)

    observers = []
    for pair in conf.sync:
        observers.append(
            Bib2QuartoSyncer(
                Converter(
                    bib_path=pair.bib,
                    md_path=pair.md,
                    md_template=pair.template if hasattr(pair, 'template') else 'template.qmd'  # defaults to template.qmd
                )
            )
        )

    for observer in observers:
        observer.run()

    logging.info("Exiting.")
