import logging
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).setLevel(logging.DEBUG)


class Bib2QuartoSyncer:
    """
    Watches and syncs a bibtex file with a markdown file. If the bibtex file is modified, the markdown file is updated and vice versa.
    """

    def __init__(self, converter):
        """
        Initializes the Bib2QuartoSyncer with a Converter object.

        Args:
            converter (Converter): The Converter object to sync.
        """

        self.converter = converter

        # If output file doesn't exist, create it
        if not os.path.exists(self.converter.md_path):
            logging.info(f"Output file {self.converter.md_path} does not exist. Creating it.")
            self.converter.bibtex_to_markdown()

        self.create_bib_observer()
        self.create_md_observer()


    def create_bib_observer(self):
        """
        Creates and starts an observer to monitor changes in the bibliography file.

        Attributes:
            observer_bib (Observer): The observer instance monitoring the bibliography file.
        """

        if hasattr(self, 'observer_bib'):
            self.observer_bib.stop()
            self.observer_bib.join()
        self.observer_bib = Observer()
        event_handler = BibChangeHandler(self.converter,
                                         callback_pre=self.remove_md_observer,
                                         callback_post=self.create_md_observer)
        self.observer_bib.schedule(event_handler, path=self.converter.bib_path, recursive=False)

    def remove_bib_observer(self):
        """
        Stops and removes the observer monitoring the bibliography file.
        """
        self.observer_bib.stop()
        self.observer_bib.join()
        del self.observer_bib

    def create_md_observer(self):
        """
        Creates and starts an observer to monitor changes in the markdown file.

        Attributes:
            observer_md (Observer): The observer instance monitoring the markdown file.
        """
        if hasattr(self, 'observer_md'):
            self.observer_md.stop()
            self.observer_md.join()
        self.observer_md = Observer()
        event_handler = MdChangeHandler(self.converter,
                                        callback_pre=self.remove_bib_observer,
                                        callback_post=self.create_bib_observer)
        self.observer_md.schedule(event_handler, path=self.converter.md_path, recursive=False)

    def remove_md_observer(self):
        """
        Stops and removes the observer monitoring the markdown file.
        """
        self.observer_md.stop()
        self.observer_md.join()
        del self.observer_md

    def run(self):
        """
        Starts the observers and keeps the script running to monitor file changes.
        Stops the observers on a keyboard interrupt.
        """
        logging.info(f"Starting observers for {self.converter.bib_path} and {self.converter.md_path}.")
        self.observer_bib.start()
        self.observer_md.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer_bib.stop()
            self.observer_md.stop()
        self.observer_bib.join()
        self.observer_md.join()


class BibChangeHandler(FileSystemEventHandler):
    """
    Handles events for changes in the bibliography file.
    """
    def __init__(self, converter, callback_pre=None, callback_post=None):
        """
        Initializes the BibChangeHandler.

        Args:
            converter (Converter): The Converter object to sync.
            callback_pre (function, optional): A callback function to call before handling the event.
            callback_post (function, optional): A callback function to call after handling the event.
        """
        self.converter = converter
        self.callback_pre = callback_pre
        self.callback_post = callback_post

    def on_modified(self, event):
        """
        Handles the event when the bibliography file is modified.

        Args:
            event (FileSystemEvent): The event object representing the file modification.
        """
        logging.info(f"{event.src_path} has been modified. Updating markdown {self.converter.md_path}.")
        if self.callback_pre is not None:
            self.callback_pre()
        self.converter.bibtex_to_markdown()
        if self.callback_post is not None:
            self.callback_post()

class MdChangeHandler(FileSystemEventHandler):
    """
    Handles events for changes in the markdown file.
    """
    def __init__(self, converter, callback_pre=None, callback_post=None):
        """
        Initializes the MdChangeHandler.

        Args:
            converter (Converter): The Converter object to sync.
            callback_pre (function, optional): A callback function to call before handling the event.
            callback_post (function, optional): A callback function to call after handling the event.
        """
        self.converter = converter
        self.callback_pre = callback_pre
        self.callback_post = callback_post

    def on_modified(self, event):
        """
        Handles the event when the markdown file is modified.

        Args:
            event (FileSystemEvent): The event object representing the file modification.
        """
        logging.info(f"{event.src_path} has been modified. Updating bibtex {self.converter.bib_path}.")

        if self.callback_pre is not None:
            self.callback_pre()
        self.converter.markdown_to_bibtex()
        if self.callback_post is not None:
            self.callback_post()
