from webdriver_manager import WebDriverManager
from anime_link_scraper import AnimeLinkScraper
from anime_downloader import AnimeDownloader
from dl_list_manager import DlListManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import logging

class GogoDownloaderApp:
    def __init__(self, config):
        self.config = config
        self.dl_list_manager = DlListManager(config.dl_list_path)

    def progress_callback(self, message):
        logging.info(message)

    def start_single_download(self, nickname, keyword, epi, quality):
        try:
            with WebDriverManager(self.config.firefox_binary_path, self.config.geckodriver_path) as driver:
                scraper = AnimeLinkScraper(driver, self.config)
                scraper.login()
                links = scraper.scrape_links(keyword, quality, epi)
                if not links:
                    logging.warning(f"No valid links found for {keyword} episodes {epi}")
                    return
                downloader = AnimeDownloader(self.config, self.progress_callback)
                failed = downloader.download(links, nickname, keyword)
                if not failed:
                    self.dl_list_manager.remove_completed(keyword, epi)
                else:
                    logging.warning(f"Some downloads failed for {keyword} episodes {epi}")
        except Exception as e:
            logging.error(f"Single download failed: {e}")
            raise

    def start_batch_download(self):
        entries = self.dl_list_manager.load_list()
        for entry in entries:
            try:
                self.start_single_download(
                    entry['nickname'],
                    entry['keyword'],
                    entry['epi'],
                    quality=3  # Default quality
                )
            except Exception as e:
                logging.error(f"Batch download failed for {entry['keyword']}: {e}")

    def run(self):
        use_dl_list = input("Use dl_list.txt? (yes/no): ").strip().lower() or 'yes'
        if use_dl_list == 'yes':
            self.start_batch_download()
        else:
            nickname = input("Save name: ").strip() or "Naruto"
            keyword = input("Anime name: ").strip() or "Naruto-dub"
            epi = input("Episode range: ").strip() or "1-5"
            quality = int(input("Quality (1-4): ").strip() or 3)
            self.start_single_download(nickname, keyword, epi, quality)