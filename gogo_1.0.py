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

def download(file_path, dest_folder, keyword):
    # Create destination folder if it doesn't exist
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    with open(file_path, 'r') as file:
        lines = file.readlines()

    failed_downloads = []

    for line in lines:
        line_parts = line.strip().split()
        if line_parts:
            url = line_parts[-1]
            name = line_parts[1]
            filename = name + '.mp4'
            path = f"{dest_folder}/{filename}"

            try:
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    block_size = 1024
                    with open(path, 'wb') as file, tqdm(
                        desc=filename,
                        total=total_size,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as bar:
                        for chunk in response.iter_content(chunk_size=block_size):
                            file.write(chunk)
                            bar.update(len(chunk))
                print(f"Downloaded {filename}")
            except Exception as e:
                print(f"Failed to download {filename}: {e}")
                failed_downloads.append(line)
        else:
            print("Error: Line parts are empty. Check the format of the input file.")

    if failed_downloads:
        with open(f'{keyword}_failed_downloads.txt', 'w') as file:
            for link in failed_downloads:
                file.write(f"{link}\n")
    else:
        os.remove(file_path)

class DownloadLinkExtractor:
    def __init__(self, keyword, epi, quality):
        self.keyword = keyword
        self.episode = epi
        self.quality = quality
        self.driver = self.setup_driver()
        self.episode_list = []

    def setup_driver(self):
        try:
            # Set up headless Firefox driver
            options = FirefoxOptions()
            options.add_argument("--headless")
            options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
            driver_path = './geckodriver.exe'
            service = FirefoxService(executable_path=driver_path)
            driver = webdriver.Firefox(service=service, options=options)
            return driver
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")

    def fetch_content(self, url):
        try:
            self.driver.get(url)
            return self.driver.page_source
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")

    def login(self, email, password):
        try:
            self.fetch_content('https://anitaku.pe/login.html')
            email_field = self.driver.find_element(By.NAME, 'email')
            email_field.clear()
            email_field.send_keys(email)
            password_field = self.driver.find_element(By.NAME, 'password')
            password_field.clear()
            password_field.send_keys(password)
            button = self.driver.find_element(By.CSS_SELECTOR, f"button[type='submit']")
            button.click()
        except Exception as e:
            print(f"Error during login: {e}")

    def get_link(self, content):
        try:
            soup = BeautifulSoup(content, 'html.parser')
            link = [a['href'] for a in soup.find_all('a', href=True) if 'download' in a['href']]

            if self.quality == 1:
                self.episode_list.append(f"Episode {self.episode} : LD {link[1]}\n")
            elif self.quality == 2:
                self.episode_list.append(f"Episode {self.episode} : SD {link[2]}\n")
            elif self.quality == 3:
                self.episode_list.append(f"Episode {self.episode} : HD {link[3]}\n")
            elif self.quality == 4:
                self.episode_list.append(f"Episode {self.episode} : HD+ {link[-1]}\n")
            else:
                print("Error: Invalid quality specified.")
        except IndexError:
            print(f"Error: Download link not found for episode {self.episode}.")
        except Exception as e:
            print(f"Error extracting links: {e}")

    def save_links(self, file_path):
        try:
            with open(file_path, 'w') as file:
                for link in self.episode_list:
                    file.write(f"{link}\n")
        except Exception as e:
            print(f"Error saving links to {file_path}: {e}")

    def scrape_links(self):
        try:
            if ',' in self.episode:
                episodes = self.episode.split(',')
            elif '&' in self.episode:
                episodes = self.episode.split('&')
            elif '-' in self.episode:
                epi_range = self.episode.split('-')
                min_epi = int(epi_range[0])
                max_epi = int(epi_range[-1])
                episodes = list(range(min_epi, max_epi + 1))
            elif self.episode.isdigit():
                episodes = [int(self.episode)]
            else:
                raise ValueError("Invalid episode format")

            for episode in tqdm(episodes, desc="Scraping links", unit="episode"):
                self.episode = episode
                url = f'https://anitaku.pe/{self.keyword}-episode-{episode}'
                content = self.fetch_content(url)
                self.get_link(content)
        except ValueError as ve:
            print(f"Error in episode format: {ve}")
        except Exception as e:
            print(f"Error during scraping links: {e}")

    def close_driver(self):
        try:
            self.driver.quit()
        except Exception as e:
            print(f"Error closing WebDriver: {e}")

    def run(self, email, password, file_path):
        try:
            self.login(email, password)
            self.scrape_links()
            self.save_links(file_path)
            self.close_driver()
        except Exception as e:
            print(f"Error in run method: {e}")

# Main execution
if __name__ == "__main__":
    try:
        use_dl_list = input("Do you want to use dl_list.txt for download list? (yes/no): ").strip().lower()
        if use_dl_list == 'yes':
            with open('dl_list.txt', 'r') as dl_file:
                for line in dl_file:
                    parts = line.split()
                    if len(parts) == 2:
                        keyword, epi = parts
                        extractor = DownloadLinkExtractor(keyword, epi, 4)
                        extractor.run(os.getenv('EMAIL'), os.getenv('PASSWORD'), f'{keyword}_links.txt')
                        download(f'{keyword}_links.txt', f'./{keyword}_{epi}', keyword)
                    else:
                        print("Error: Incorrect format in dl_list.txt.")
        elif use_dl_list == 'no':
            keyword = input("Enter anime name:\t").strip()
            epi = input("Enter episode range, eg. 1-23 for multiple range, 1,2,3 for specific or 23 for single:\t").strip() or '1-5'
            quality = int(input("Enter quality 1(low)-4(high):\t").strip() or 2)
            email = os.getenv('EMAIL')
            password = os.getenv('PASSWORD')

            if not email or not password:
                print("Error: Email and password must be provided.")
            else:
                extractor = DownloadLinkExtractor(keyword, epi, quality)
                extractor.run(email, password, f'{keyword}_links.txt')
                download(f'{keyword}_links.txt', f'./{keyword}_{epi}', keyword)
        else:
            print("Error: Invalid input for using dl_list.txt. Please enter 'yes' or 'no'.")
    except Exception as e:
        print(f"Error in main execution: {e}")