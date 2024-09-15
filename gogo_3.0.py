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
    def __init__(self, keyword, nickname, quality, epi):
        self.keyword = keyword
        self.nickname = nickname
        self.quality = quality
        self.episode = None
        self.episode_list = []
        self.failed_downloads = []
        self.failed_file_path = rf'.\temp\{nickname}_failed_downloads.txt'
        self.dest = rf'C:\Users\hamed\Downloads\{nickname}\{keyword}'
        self.links = rf'.\temp\{nickname}_links.txt'
        self.epi = epi
        self.driver = self.setup_driver()
        print("Driver setup successful.\n")

    def setup_driver(self):
        print("Driver setup initiated...")
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
        driver_path = r'.\geckodriver.exe'
        service = FirefoxService(executable_path=driver_path)
        return webdriver.Firefox(service=service, options=options)

    def fetch_content(self, url):
        self.driver.get(url)
        return self.driver.page_source
        
    def login(self, email, password):
        print("Attempting to login...")
        self.fetch_content('https://anitaku.pe/login.html')
        self.driver.find_element(By.NAME, 'email').send_keys(email)
        self.driver.find_element(By.NAME, 'password').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        print("Logged in successfully.\n")

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
        print("\nSaving links...")
        os.makedirs(r'.\temp', exist_ok=True)
        with open(self.links, 'w') as file:
            file.writelines(self.episode_list)
        print("links saved.\n")
    
    def parse_episodes(self):
        episodes = []
        for part in self.epi.replace('.', ',').replace('&', ',').split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                episodes.extend(range(start, end + 1))
            else:
                episodes.append(int(part))
        return episodes
    
    def scrape_links(self):
        print("Scraping initiated ETA: 5sec/episode (First episode takes longer)")
        for episode in tqdm(self.parse_episodes(), desc=f"Scraping {self.nickname} link(s)", unit="episode"):
            self.episode = episode
            url = f'https://anitaku.pe/{self.keyword}-episode-{episode}'
            self.get_link(self.fetch_content(url))

    def close_driver(self):
        self.driver.quit()
        print("DRIVER CLOSED.\n")

    def file_check(self):
        null_dl = [file.split('.')[0] for file in os.listdir(self.dest) 
                   if os.path.getsize(os.path.join(self.dest, file)) < 20]
        if null_dl:
            self.retry_failed_downloads(null_dl)

    def retry_failed_downloads(self, null_dl):
        self.epi = ','.join(null_dl)
        self.driver = self.setup_driver()
        self.download_links(os.getenv('EMAIL'), os.getenv('PASSWORD'))
        self.download()
        self.update_dl_list()

    def download(self):
        print("Downloading...")
        os.makedirs(self.dest, exist_ok=True)
        with open(self.links, 'r') as file:
            lines = file.readlines()
        os.remove(self.links)
        for line in lines:
            url, showname, path = self.line(line)
            self.failed_dl_tracker(True, line)
            try:
                response = requests.get(url, stream=True, allow_redirects=True)
                expected_size = int(response.headers.get('content-length', 0))
                file_size = os.path.getsize(path) if os.path.exists(path) else None
                if file_size == expected_size and file_size > 1024:
                    self.failed_dl_tracker(False, line)
                    print(f"{showname} already exists and matches the expected size. Skipping download.\n")
                    continue
                elif expected_size == 0:
                    continue
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    dl_size = int(response.headers.get('content-length', 0))
                    block_size = 1024
                    with open(path, 'wb') as file, tqdm(
                        desc=showname,
                        total=dl_size,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as bar:
                        for chunk in response.iter_content(chunk_size=block_size):
                            file.write(chunk)
                            bar.update(len(chunk))
                print(f"Downloaded {showname}\n")
            except Exception as e:
                print(f"Failed to download {showname}: {e}\n")

    def line(self, line):
        line = line.strip().split()
        url, name = line[-1], line[1]
        filename = f"{name}.mp4"
        showname = f"{self.nickname} {filename}"
        path = rf"{self.dest}\{filename}"
        return [url, showname, path]

    def update_dl_list(self):
        with open('dl_list.txt', 'r+') as file:
            lines = file.readlines()
            file.seek(0)
            file.writelines(line for line in lines if not (self.keyword in line and self.epi in line))
            file.truncate()

    def failed_dl_tracker(self, condition, value):
        if condition:
            self.failed_downloads.append(value)
            with open(self.failed_file_path, 'a') as file:
                file.write(f'{value}')
        else:
            self.failed_downloads.remove(value)
            with open(self.failed_file_path, 'r+') as file:
                lines = file.readlines()
                file.seek(0)
                file.writelines(line for line in lines if line.strip() != value.strip())
                file.truncate()

    def retry(self):
        if self.failed_downloads and os.path.exists(self.failed_file_path):
            with open(self.failed_file_path, 'r') as file:
                lines = file.readlines()
            os.remove(self.failed_file_path)
            for line in lines:
                try:
                    url, showname, path = self.line(line)
                    response = requests.get(url, stream=True, allow_redirects=True)
                    expected_size = int(response.headers.get('content-length', 0))
                    file_size = os.path.getsize(path) if os.path.exists(path) else None
                    if file_size == expected_size and file_size > 1024:
                        continue
                    if expected_size == 0:
                        continue
                    with requests.get(url, stream=True) as response:
                        response.raise_for_status()
                        dl_size = int(response.headers.get('content-length', 0))
                        block_size = 1024
                        with open(path, 'wb') as file, tqdm(
                            desc=showname,
                            total=dl_size,
                            unit='B',
                            unit_scale=True,
                            unit_divisor=1024,
                        ) as bar:
                            for chunk in response.iter_content(chunk_size=block_size):
                                file.write(chunk)
                                bar.update(len(chunk))
                    print(f"Downloaded {showname}")
                except Exception as e:
                    print(f"Failed to download {showname} again: {e}\n")
        else:
            print("No failed downloads detected, running second check now...\n")

    def download_links(self, email, password):
        self.login(email, password)
        self.scrape_links()
        self.save_links()
        self.close_driver()

    @staticmethod
    def dl_list():
        key= "Save-name Anime-name Episode"
        try:
            with open("dl_list.txt", "r+") as f:
                lines = f.readlines()
                if not lines or lines[0].strip() != key or key in lines:
                    lines = [line for line in lines if line.strip() != key.strip()]
                    f.seek(0)
                    f.write(f'{key}\n')
                    f.writelines(lines)
                    f.truncate()
        except FileNotFoundError:
            with open("dl_list.txt", "w") as f:
                f.write(key)

    @staticmethod
    def run():
        DownloadLinkExtractor.dl_list()
        use_dl_list = input("Do you want to use dl_list.txt for download list? (yes/no): ").strip().lower() or 'yes'
        email, password = os.getenv('EMAIL'), os.getenv('PASSWORD')
        if not email or not password:
            print("Error: Email and password must be provided.")
            return
        print("\nLoading... estimated time(25sec) before scraping starts.\n")
        if use_dl_list == 'yes':
            with open('dl_list.txt', 'r') as dl_file:
                for line in dl_file:
                    if line.strip() != "Save-name Anime-name Episode":
                        parts = line.split()
                        if len(parts) in [2, 3]:
                            nickname, keyword, epi = (parts + [parts[0]])[:3]
                            extractor = DownloadLinkExtractor(keyword, nickname, 3, epi)
                            extractor.download_links(email, password)
                            extractor.download()
                            extractor.retry()
                            extractor.file_check()
                            extractor.update_dl_list()
                        else:
                            print("Error: Incorrect format in dl_list.txt.\n")
                            print("Correct format:")
                            print("|Save-name\tAnime-name\tEpisode|")
                            print("Demon-slayer Kimetsu-no-Yaiba-dub 1-24")
                            print("Naruto naruto-shippuden 1-220\n")
                            print("Separate each with a space, leave no space between anime name, use - to separate anime name... eg: Demon-slayer not: demon slayer. Leave no empty lines.\n")
                print("All downloads completed")
        else:
            keyword = input("Enter anime name:\t").strip() or "Naruto-dub"
            nickname = input("Enter the name you want to save this anime as:\t") or keyword
            epi = input("Enter episode range, e.g., 1-23 for multiple or 23 for single:\t").strip() or '1-5'
            quality = int(input("Enter quality 1(low)-4(high):\t").strip() or 2)
            print("Loading... please wait.")
            extractor = DownloadLinkExtractor(keyword, nickname, quality, epi)
            extractor.download_links(email, password)
            extractor.download()
            extractor.retry()
            extractor.file_check()
            print("Download completed")
            
# Main execution
if __name__ == "__main__":
    DownloadLinkExtractor.run()