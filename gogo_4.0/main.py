import logging
from gogo_downloader_app import GogoDownloaderApp
from config import Config

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('gogo_downloader.log'),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logging.info("Starting Gogo Downloader v4.0")
    app = GogoDownloaderApp(Config())
    app.run()

if __name__ == "__main__":
    main()