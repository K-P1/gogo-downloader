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
    def __init__(self, keyword, nickname, quality, dest):
        self.keyword = keyword
        self.nickname = nickname
        self.episode = None
        self.quality = quality
        self.driver = self.setup_driver()
        self.episode_list = []
        self.failed_downloads = []
        self.failed_file_path= os.path.join(r".\temp",f"{self.nickname}_failed_downloads.txt")
        self.dest= dest

    def setup_driver(self):
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
        driver_path = r'.\geckodriver.exe'
        service = FirefoxService(executable_path=driver_path)
        driver = webdriver.Firefox(service=service, options=options)
        return driver

    def fetch_content(self, url):
        self.driver.get(url)
        return self.driver.page_source
        
    def login(self, email, password):
        self.fetch_content('https://anitaku.pe/login.html')
        email_field = self.driver.find_element(By.NAME, 'email')
        email_field.clear()
        email_field.send_keys(email)
        password_field = self.driver.find_element(By.NAME, 'password')
        password_field.clear()
        password_field.send_keys(password)
        button = self.driver.find_element(By.CSS_SELECTOR, f"button[type='submit']")
        button.click()

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
    
    def scrape_links(self, epi):
        episodes = self.parse_episodes(epi)
        for episode in tqdm(episodes, desc=f"Scraping {self.nickname} links", unit="episode"):
            self.episode = episode
            url = f'https://anitaku.pe/{self.keyword}-episode-{episode}'
            content = self.fetch_content(url)
            self.get_link(content)

    def close_driver(self):
        self.driver.quit()

    def file_check(self):
        null_dl = [file.split('.')[0] for file in os.listdir(self.dest) if os.path.getsize(os.path.join(self.dest, file)) < 20000]
        if null_dl:
            self.retry_failed_downloads(null_dl)

    def retry_failed_downloads(self, null_dl):
        epi = ','.join(null_dl)
        with open(r'.\dl_list.txt', 'a') as file:
            file.write(f"{self.nickname} {self.keyword} {epi}\n")
        self.download_links(os.getenv('EMAIL'), os.getenv('PASSWORD'), epi)
        self.download_files(rf".\temp\{self.nickname}_links.txt", rf'.\downloads\{self.nickname}\{self.keyword}')
        self.update_dl_list(self.keyword, epi)

    def download_files(self, links_path):
        # Create destination folder if it doesn't exist
        if not os.path.exists(self.dest):
            os.makedirs(self.dest, exist_ok=True)
        if os.path.exists(links_path):
            # Read links from the provided file
            with open(links_path, 'r') as file:
                lines = file.readlines()
            os.remove(links_path)
        else:
            print("links path in downloads does not exist")
            return  # Exit if the links path does not exist

        # Iterate through each link
        for line in lines if lines else (print("links path is empty")):
            # Add to failed downloads list to be removed if the download is successful
            self.failed_dl_tracker(True, line)
            line_parts = line.strip().split()
            if line_parts:
                url = line_parts[-1]  # Get the URL from the last part of the line
                name = line_parts[1]  # Get the name from the second part of the line
                filename = name + '.mp4'  # Create a filename with the .mp4 extension
                path = rf"{self.dest}\{filename}"  # Define the full path for the file
                showname = f"{self.nickname} {filename}"

                try:
                    # Try using a HEAD request first
                    response = requests.head(url, allow_redirects=True)
                    expected_size = int(response.headers.get('content-length', 0))
                    
                    if expected_size == 0:
                        # Fallback to GET request if HEAD didn't return content-length
                        print("expected file size gotten at second attempt")
                        response = requests.get(url, stream=True, allow_redirects=True)
                        expected_size = int(response.headers.get('content-length', 0))
                        if expected_size == 0:
                            print(f"Failed to download {showname}")
                            self.failed_dl_tracker(True, line)
                            continue

                    print(f"This is the expected size:\t{expected_size}")
                    print(f"This is the file size:\t{os.path.getsize(path)}")
                    
                    #checks if expected size is valid
                    
                    # Check if file already exists and matches the expected size
                    if os.path.exists(path) and os.path.getsize(path) == expected_size and os.path.getsize(path) > 1024:
                        print(f"{showname} already exists and matches the expected size. Skipping download.")
                        self.failed_dl_tracker(False, line)
                        continue
                    
                    # Proceed with the download if needed
                    with requests.get(url, stream=True) as response:
                        response.raise_for_status()
                        total_size = int(response.headers.get('content-length', 0))
                        print(f"This is the total size:\t{total_size}")
                        block_size = 1024
                        with open(path, 'wb') as file, tqdm(
                            desc=showname,
                            total=total_size,
                            unit='B',
                            unit_scale=True,
                            unit_divisor=1024,
                        ) as bar:
                            for chunk in response.iter_content(chunk_size=block_size):
                                file.write(chunk)
                                bar.update(len(chunk))
                    self.failed_dl_tracker(False, line)
                    print(f"Downloaded {showname}")

                except Exception as e:
                    print(f"Failed to download {showname}: {e}")
                    if line not in self.failed_downloads:
                        print("Failed file was not in failed downloads but has been added.")
                        self.failed_dl_tracker(True, line)

    def download(self, links_path):
        os.makedirs(self.dest, exist_ok=True)
        with open(links_path, 'r') as file:
            lines = file.readlines()
        os.remove(links_path)
        for line in lines if lines else():
            self.failed_dl_tracker(True, line)
            try:
                response = requests.get(line()[0], stream=True, allow_redirects=True)
                expected_size = int(response.headers.get('content-length', 0))
                file_size = os.path.getsize(line()[-1])
                if not expected_size or (file_size == expected_size and file_size > 1024):
                    self.failed_dl_tracker(False, line)
                    continue


            except:
                pass

    def line(self, line):
        line= line.strip().split()[1][-1]
        url, name= line[-1], line[1]
        filename = name + '.mp4'
        showname = f"{self.nickname} {filename}"
        path = rf"{self.dest}\{filename}"
        line=[url, name, filename, showname, path]
        return line

        

    def update_dl_list(self, keyword, episode):
        try:
            if os.path.exists(self.failed_file_path):
                os.remove(self.failed_file_path)
            # Read the current contents of the dl_list.txt
            with open('dl_list.txt', 'r') as file:
                lines = file.readlines()
            # Write back all lines except the one to be removed
            with open('dl_list.txt', 'w') as file:
                for line in lines:
                    if not (keyword in line and episode in line):
                        file.write(line)
                    else:
                        print("Dl_list updated")
        except Exception as e:
            print(f"Error updating dl_list.txt: {e}")

    def failed_dl_tracker(self, condition, value):
        if condition:
            self.failed_downloads.append(value)
            # Write the value to the file
            with open(self.failed_file_path, 'a' if os.path.exists(self.failed_file_path) else 'w') as file:
                file.write(f'{value}')
        else:
            self.failed_downloads.remove(value)
            # Read the file lines and remove the value if present
            if os.path.exists(self.failed_file_path):
                with open(self.failed_file_path, 'r') as file:
                    lines = file.readlines()
                
                # Write back all lines except the one with the specified value
                with open(self.failed_file_path, 'w') as file:
                    for line in lines:
                        if line.strip() != value.strip():
                            file.write(line)
            else:
                os.makedirs(self.failed_file_path)
                print("DEBUG MESSAGE: failed file path was created in failed dl tracker")

    def retry(self):
        try:
            if self.failed_downloads and os.path.exists(self.failed_file_path):
                # Read links from the provided file
                with open(self.failed_file_path, 'r') as file:
                    lines = file.readlines()
                os.remove(self.failed_file_path)
                # Iterate through each link
                for line in lines:
                    line_parts = line.strip().split()
                    if line_parts:
                        url = line_parts[-1]  # Get the URL from the last part of the line
                        name = line_parts[1]  # Get the name from the second part of the line
                        filename = name + '.mp4'  # Create a filename with the .mp4 extension
                        path = rf"{self.dest}\{filename}"  # Define the full path for the file
                        showname = f"{self.nickname} {filename}"
                        try:
                            # Try using a HEAD request first
                            response = requests.head(url, allow_redirects=True)
                            expected_size = int(response.headers.get('content-length', 0))
                            
                            if expected_size == 0:
                                # Fallback to GET request if HEAD didn't return content-length
                                print("expected file size gotten at second attempt")
                                response = requests.get(url, stream=True, allow_redirects=True)
                                expected_size = int(response.headers.get('content-length', 0))
                                if expected_size == 0:
                                    print(f"Failed to download {showname} again, skipping this file")
                                    self.failed_dl_tracker(True, line)
                                    continue

                            print(f"This is the expected size:\t{expected_size}")
                            print(f"This is the file size:\t{os.path.getsize(path)}")
                            
                            #checks if expected size is valid
                            
                            # Check if file already exists and matches the expected size
                            if os.path.exists(path) and os.path.getsize(path) == expected_size and os.path.getsize(path) > 1024:
                                print(f"{showname} already exists and matches the expected size. Skipping download.")
                                self.failed_dl_tracker(False, line)
                                continue
                            
                            # Proceed with the download if needed
                            with requests.get(url, stream=True) as response:
                                response.raise_for_status()
                                total_size = int(response.headers.get('content-length', 0))
                                print(f"This is the total size:\t{total_size}")
                                block_size = 1024
                                with open(path, 'wb') as file, tqdm(
                                    desc=showname,
                                    total=total_size,
                                    unit='B',
                                    unit_scale=True,
                                    unit_divisor=1024,
                                ) as bar:
                                    for chunk in response.iter_content(chunk_size=block_size):
                                        file.write(chunk)
                                        bar.update(len(chunk))
                            print(f"Downloaded {filename} on second attempt")
                        except Exception as e:
                            print(f"Failed to download {filename}: {e} again, skipping this file")
            else:
                print("No failed download dectected on first check, running second check now...")
        except Exception as e:
            print(f"Error during retry: {e}")
    
    def download_links(self, email, password, episode):
        self.login(email, password)
        self.scrape_links(episode)
        self.save_links()
        self.close_driver()

    @staticmethod
    def run():
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
                            extractor = DownloadLinkExtractor(keyword, nickname, 3, rf'.\downloads\{nickname}\{keyword}')
                            extractor.download_links(email, password, epi)
                            extractor.download_files(rf'.\temp\{nickname}_links.txt')
                            extractor.retry()
                            extractor.file_check()
                            extractor.update_dl_list(keyword, epi)
                        else:
                            print("Error: Incorrect format in dl_list.txt.")
                    print("All donwloads complete")
            else:
                keyword = input("Enter anime name:\t").strip()
                nickname = input("Enter the name you want to save this anime as:\t") or keyword
                epi = input("Enter episode range, eg. 1-23 for multiple or 23 for single:\t").strip() or '1-5'
                quality = int(input("Enter quality 1(low)-4(high):\t").strip() or 2)
                extractor = DownloadLinkExtractor(keyword, nickname, quality, rf'.\downloads\{nickname}\{keyword}')
                extractor.download_links(email, password, epi)
                extractor.download_files(rf'.\temp\{nickname}_links.txt')
                extractor.retry()
                extractor.file_check()
                extractor.update_dl_list(keyword, epi)
    
# Main execution
if __name__ == "__main__":
    DownloadLinkExtractor.run()