from dataclasses import dataclass
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup, Tag
import logging

@dataclass
class DownloadLink:
    episode: int
    quality: str
    url: str

class AnimeLinkScraper:
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.base_url = 'https://anitaku.pe'

    def login(self):
        logging.info("Attempting to login")
        try:
            self.driver.get(f'{self.base_url}/login.html')
            self.driver.find_element(By.NAME, 'email').send_keys(self.config.email)
            self.driver.find_element(By.NAME, 'password').send_keys(self.config.password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            logging.info("Logged in successfully")
        except Exception as e:
            logging.error(f"Login failed: {e}")
            raise

    def parse_episodes(self, epi_str):
        episodes = []
        for part in epi_str.replace('.', ',').replace('&', ',').split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                episodes.extend(range(start, end + 1))
            else:
                episodes.append(int(part))
        return episodes

    def scrape_links(self, keyword, quality, epi_str):
        logging.info(f"Scraping links for {keyword}")
        links = []
        for episode in self.parse_episodes(epi_str):
            url = f'{self.base_url}/{keyword}-episode-{episode}'
            content = self.fetch_content(url)
            link = self.get_link(content, episode, quality)
            if link:
                links.append(link)
        return links

    def fetch_content(self, url):
        try:
            self.driver.get(url)
            return self.driver.page_source
        except Exception as e:
            logging.error(f"Failed to fetch content from {url}: {e}")
            return None

    def get_link(self, content, episode, quality):
        if not content:
            return None
        soup = BeautifulSoup(content, 'html.parser')
        # Explicitly type as list of Tag to satisfy Pylance
        download_links = [
            a.get('href')
            for a in soup.find_all('a', href=True)
            if isinstance(a, Tag) and a.get('href') is not None and 'download' in str(a.get('href'))
        ]
        try:
            return DownloadLink(
                episode=episode,
                quality=self.config.quality_map[quality],
                url=download_links[quality - 1]
            )
        except (IndexError, KeyError):
            logging.error(f"No valid download link found for episode {episode} with quality {quality}")
            return None