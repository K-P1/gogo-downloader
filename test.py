import os
import requests
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DownloadLinkExtractor:
    def __init__(self, keyword, nickname, quality):
        self.keyword = keyword
        self.nickname = nickname
        self.quality = quality
        self.episode_list = []
        self.failed_downloads = []
        self.failed_file_path = os.path.join(r".\temp", f"{self.nickname}_failed_downloads.txt")
        self.driver = self.setup_driver()

    def setup_driver(self):
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
        service = FirefoxService(executable_path=r'.\geckodriver.exe')
        return webdriver.Firefox(service=service, options=options)

    def fetch_content(self, url):
        self.driver.get(url)
        return self.driver.page_source

    def login(self, email, password):
        self.fetch_content('https://anitaku.pe/login.html')
        self.driver.find_element(By.NAME, 'email').send_keys(email)
        self.driver.find_element(By.NAME, 'password').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    def get_link(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True) if 'download' in a['href']]
        quality_map = {1: "LD", 2: "SD", 3: "HD", 4: "HD+"}
        try:
            link = links[self.quality]
            self.episode_list.append(f"Episode {self.episode} : {quality_map.get(self.quality)} {link}\n")
        except IndexError:
            print(f"Error: Download link not found for episode {self.episode}.")

    def save_links(self):
        os.makedirs(r'.\temp', exist_ok=True)
        file_path = os.path.join(r'.\temp', f"{self.nickname}_links.txt")
        with open(file_path, 'w') as file:
            file.writelines(self.episode_list)

    def scrape_links(self, epi):
        episodes = self.parse_episodes(epi)
        for episode in tqdm(episodes, desc=f"Scraping {self.nickname} links", unit="episode"):
            self.episode = episode
            url = f'https://anitaku.pe/{self.keyword}-episode-{episode}'
            content = self.fetch_content(url)
            self.get_link(content)

    def parse_episodes(self, epi):
        epi = epi.replace('.', ',').replace('&', ',')
        episodes = []
        for part in epi.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                episodes.extend(range(start, end + 1))
            else:
                episodes.append(int(part))
        return episodes

    def close_driver(self):
        self.driver.quit()

    def file_check(self, dest_folder):
        null_dl = [file.split('.')[0] for file in os.listdir(dest_folder) if os.path.getsize(os.path.join(dest_folder, file)) < 20000]
        if null_dl:
            self.retry_failed_downloads(null_dl)

    def retry_failed_downloads(self, null_dl):
        epi = ','.join(null_dl)
        with open(r'.\dl_list.txt', 'a') as file:
            file.write(f"{self.nickname} {self.keyword} {epi}\n")
        self.run(os.getenv('EMAIL'), os.getenv('PASSWORD'), epi)
        self.download_links()

    def download_links(self, dest_folder):
        # Ensure the destination directory exists
        os.makedirs(dest_folder, exist_ok=True)
        
        # Ensure the temp directory and failed file exist
        os.makedirs(os.path.dirname(self.failed_file_path), exist_ok=True)
        if not os.path.exists(self.failed_file_path):
            with open(self.failed_file_path, 'w') as file:
                pass  # Create the file if it doesn't exist

        # Proceed with reading the failed download links and downloading them
        with open(self.failed_file_path, 'r') as file:
            for line in file:
                url, filename = line.split()[-1], f"{line.split()[1]}.mp4"
                self.download_file(url, os.path.join(dest_folder, filename))

    def download_file(self, url, path):
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(path, 'wb') as file, tqdm(total=int(response.headers.get('content-length', 0)), unit='B', unit_scale=True, unit_divisor=1024) as bar:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
                    bar.update(len(chunk))

    def run(self, email, password, episode):
        self.login(email, password)
        self.scrape_links(episode)
        self.save_links()
        self.close_driver()

# Main execution
if __name__ == "__main__":
    use_dl_list = input("Do you want to use dl_list.txt for download list? (yes/no): ").strip().lower() or 'yes'
    email, password = os.getenv('EMAIL'), os.getenv('PASSWORD')

    if not email or not password:
        print("Error: Email and password must be provided.")
    else:
        if use_dl_list == 'yes':
            with open('dl_list.txt', 'r') as dl_file:
                for line in dl_file:
                    parts = line.split()
                    if len(parts) in [2, 3]:
                        nickname, keyword, epi = (parts + [parts[0]])[:3]
                        extractor = DownloadLinkExtractor(keyword, nickname, 3)
                        extractor.run(email, password, epi)
                        extractor.download_links(rf'.\downloads\{nickname}\{keyword}')
                        extractor.file_check(rf'.\downloads\{nickname}\{keyword}')
                    else:
                        print("Error: Incorrect format in dl_list.txt.")
        else:
            keyword = input("Enter anime name:\t").strip()
            nickname = input("Enter the name you want to save this anime as:\t") or keyword
            epi = input("Enter episode range, eg. 1-23 for multiple or 23 for single:\t").strip() or '1-5'
            quality = int(input("Enter quality 1(low)-4(high):\t").strip() or 2)
            extractor = DownloadLinkExtractor(keyword, nickname, quality)
            extractor.run(email, password, epi)
            extractor.download_links(rf'.\downloads\{nickname}\{keyword}')
            extractor.file_check(rf'.\downloads\{nickname}\{keyword}')
