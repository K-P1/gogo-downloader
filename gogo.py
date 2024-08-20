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
        self.episode = None
        self.quality = quality
        self.driver = self.setup_driver()
        self.episode_list = []
        self.failed_downloads = []
        self.failed_file_path= os.path.join(r".\temp",f"{self.nickname}_failed_downloads.txt")

    def setup_driver(self):
        try:
            # Set up headless Firefox driver
            options = FirefoxOptions()
            options.add_argument("--headless")
            options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
            driver_path = r'.\geckodriver.exe'
            service = FirefoxService(executable_path=driver_path)
            driver = webdriver.Firefox(service=service, options=options)
            return driver
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")

    def fetch_content(self, url):
        try:
            # Fetch page content using Selenium
            self.driver.get(url)
            return self.driver.page_source
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")

    def login(self, email, password):
        try:
            # Log in to the website
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
            # Parse the page content to extract download links
            soup = BeautifulSoup(content, 'html.parser')
            link = [a['href'] for a in soup.find_all('a', href=True) if 'download' in a['href']]

            # Select the link based on the desired quality
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

    def save_links(self):
        try:
            directory= r'.\temp'
            os.makedirs(directory, exist_ok=True)
            file_path= os.path.join(directory,f"{self.nickname}_links.txt")
            # Save the extracted links to a file
            with open(file_path, 'w') as file:
                for link in self.episode_list:
                    file.write(f"{link}")#add \n if you encounter errors relating to link file format
        except Exception as e:
            print(f"Error saving links to {file_path}: {e}")
    
    def scrape_links(self, epi):
        try:
            # Determine the episode range or list
            episodes = []

            # Replace dots and & with commas to handle dot-separated numbers
            epi = epi.replace('.', ',').replace('&', ',')

            # Split the input by commas and iterate through each part
            if ',' in epi:
                parts = epi.split(',')
                for part in parts:
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        episodes.extend(range(start, end + 1))
                    else:
                        episodes.append(int(part))
            elif '-' in epi:
                start, end = map(int, epi.split('-'))
                episodes = list(range(start, end + 1))
            elif epi.isdigit():
                episodes = [int(epi)]
            else:
                raise ValueError("Invalid episode format")
            
            # Scrape links for each episode
            for episode in tqdm(episodes, desc=f"Scraping {self.nickname} links", unit="episode"):
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
            # Close the WebDriver
            self.driver.quit()
        except Exception as e:
            print(f"Error closing WebDriver: {e}")

    def file_check(self,dest_folder):
        try:
            null_dl=[]
            n=0
            p=0
            dl_links_path= fr'.\dl_list.txt'
            for file in os.listdir(dest_folder):
                file_path= os.path.join(dest_folder,file)
                if os.path.getsize(file_path) < 20000:
                    null_dl.append((file.split('.')[0]))
                    n+=1
                else:
                    p+=1
            print(f"Second file(s) check completed:\t {p} file(s) passed and {n} failed")
            if n != 0:
                print("retrying failed downloads...")
                epi= ','.join(null_dl)
                if os.path.exists(dl_links_path):
                    with open(dl_links_path, 'r') as file:
                        old_contents = file.readlines()
                else:
                    old_contents = []
                # Prepare the new line to write
                new_line = f"{self.nickname} {self.keyword} {epi}\n"
                # Write the new line followed by the old contents
                with open(dl_links_path, 'w') as file:
                    file.write(new_line)
                    file.writelines(old_contents)
                links= os.path.join(r".\temp",f"{self.nickname}_links.txt")
                extractor = DownloadLinkExtractor(self.keyword, self.nickname, self.quality)
                extractor.run(os.getenv('EMAIL'), os.getenv('PASSWORD'), epi)
                extractor.download(links, rf'.\downloads\{self.nickname}\{self.keyword}')
                extractor.update_dl_list(self.keyword, epi)
        
            else:
                print("No failed download dectected on second check, moving on to next download...")
        except Exception as e:
            print(f"Error during file check: {e}")
            
    def download(self, links_path, dest_folder):
        # Create destination folder if it doesn't exist
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder, exist_ok=True)
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
                path = rf"{dest_folder}\{filename}"  # Define the full path for the file
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

    def retry(self, dest_folder):
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
                        path = rf"{dest_folder}\{filename}"  # Define the full path for the file
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
     
    def run(self, email, password, episode):
        try:
            # Execute the main process: login, scrape links, save links, close driver
            self.login(email, password)
            self.scrape_links(episode)
            self.save_links()
            self.close_driver()
        except Exception as e:
            print(f"Error in run method: {e}")

# Main execution
if __name__ == "__main__":
    try:
        # Ask the user if they want to use the dl_list.txt file
        use_dl_list = input("Do you want to use dl_list.txt for download list? (yes/no): ").strip().lower() or 'yes'
        if use_dl_list == 'yes':
            with open('dl_list.txt', 'r') as dl_file:
                for line in dl_file:
                    parts = line.split()
                    if len(parts) == 3:
                        nickname, keyword, epi = parts
                        extractor = DownloadLinkExtractor(keyword, nickname, 3)
                        extractor.run(os.getenv('EMAIL'), os.getenv('PASSWORD'), epi)
                        extractor.download(rf'.\temp\{nickname}_links.txt', rf'.\downloads\{nickname}\{keyword}')
                        extractor.retry(fr'.\downloads\{nickname}\{keyword}')
                        extractor.file_check(rf'.\downloads\{nickname}\{keyword}')
                        extractor.update_dl_list(keyword, epi)
                    elif len(parts) == 2:
                        keyword, epi = parts
                        extractor = DownloadLinkExtractor(keyword, keyword, 3)
                        extractor.run(os.getenv('EMAIL'), os.getenv('PASSWORD'), epi)
                        extractor.download(rf'.\temp\{keyword}_links.txt', fr'.\downloads\{keyword}')
                        extractor.retry(fr'.\downloads\{keyword}')
                        extractor.file_check(fr'.\downloads\{keyword}')
                        extractor.update_dl_list(keyword, epi)
                    else:
                        print("Error: Incorrect format in dl_list.txt.")
                print("All donwloads complete")
        elif use_dl_list == 'no':
            # Prompt the user for input details
            keyword = input("Enter anime name:\t").strip()
            nickname = input("Enter the name you want to save this anime as:\t") or keyword
            epi = input("Enter episode range, eg. 1-23 for multiple or 23 for single:\t").strip() or '1-5'
            quality = int(input("Enter quality 1(low)-4(high):\t").strip() or 2)
            email = os.getenv('EMAIL')
            password = os.getenv('PASSWORD')

            # Check if email and password are provided
            if not email or not password:
                print("Error: Email and password must be provided.")
            else:
                extractor = DownloadLinkExtractor(keyword, nickname, quality)
                extractor.run(email, password, epi)
                extractor.download(rf'.\temp\{nickname}_links.txt', rf'.\downloads\{nickname}\{keyword}')
                extractor.retry(fr'.\downloads\{nickname}\{keyword}')
                extractor.file_check(fr'.\downloads\{nickname}\{keyword}')
                extractor.update_dl_list(keyword, epi) 
        else:
            print("Error: Invalid input for using dl_list.txt. Please enter 'yes' or 'no'.")
    except Exception as e:
        print(f"Error in main execution: {e}")