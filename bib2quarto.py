import logging
import time
import os
import argparse
from omegaconf import OmegaConf
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from converter import Converter
import threading

logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).setLevel(logging.DEBUG)


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, converter):
        self.converter = converter

        # If output file doesn't exist, create it
        if not os.path.exists(self.converter.md_path):
            logging.info(f"Output file {self.converter.md_path} does not exist. Creating it.")
            self.converter.to_markdown()

    def on_modified(self, event):
        if event.src_path.endswith(".bib"):
            logging.info(f"{event.src_path} has been modified. Updating markdown {self.converter.md_path}.")
            self.converter.to_markdown()
        elif event.src_path.endswith(".qmd"):
            logging.info(f"{event.src_path} has been modified. Updating bibtex {self.converter.bib_path}.")
            self.converter.to_bibtex()

# Run observers in separate threads
def run_observer(observer):
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    converter = Converter(
        "database.bib",
        "database.qmd",
        "template.qmd"
    )

    args = argparse.ArgumentParser(description="Converts a bibtex file to markdown and vice versa.")
    args.add_argument("--config", type=str, default='config.yml', help="Path to the configuration file.")
    args = args.parse_args()

    conf = OmegaConf.load(args.config)

    # Call the desired operation
    # converter.to_markdown()
    # converter.to_bibtex()

    event_handlers = []
    observers = []
    threads = []

    for pair in conf.sync:
        converter = Converter(
            bib_path=pair.bib,
            md_path=pair.md,
            md_template=pair.template if hasattr(pair, 'template') else 'template.qmd'  # defauls to template.qmd
        )

        event_handler = FileChangeHandler(converter)
        observer = Observer()
        observer.schedule(event_handler, path='.', recursive=False)

        event_handlers.append(event_handler)
        observers.append(observer)

        thread = threading.Thread(target=run_observer, args=(observer,))
        thread.daemon = True
        threads.append(thread)

    logging.info("Watching for changes in .bib and .qmd files.")
    for thread in threads:
        thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        for thread in threads:
            thread.join()

    logging.info("Exiting.")
