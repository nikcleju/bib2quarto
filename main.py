import logging
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from converter import Converter

logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).setLevel(logging.DEBUG)


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, converter):
        self.converter = converter

    def on_modified(self, event):
        if event.src_path.endswith(".bib"):
            logging.info(f"{event.src_path} has been modified. Updating markdown.")
            self.converter.to_markdown()
        elif event.src_path.endswith(".qmd"):
            logging.info(f"{event.src_path} has been modified. Updating bibtex.")
            self.converter.to_bibtex()

if __name__ == "__main__":
    converter = Converter(
        "CeCitesc.bib",
        "output.qmd",
        "template.qmd"
    )

    # Uncomment the desired operation
    # converter.to_markdown()
    # converter.to_bibtex()

    event_handler = FileChangeHandler(converter)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)

    logging.info("Watching for changes in .bib and .qmd files.")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
