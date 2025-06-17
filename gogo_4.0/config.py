from pathlib import Path
import os
from dotenv import load_dotenv
import shutil

class Config:
    def __init__(self):
        load_dotenv()
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.validate_credentials()
        
        # Attempt to find Firefox binary dynamically
        self.firefox_binary_path = self.find_firefox_binary() or r'C:\Program Files\Mozilla Firefox\firefox.exe'
        self.geckodriver_path = r'.\geckodriver.exe'
        self.default_download_dir = Path.home() / 'Downloads'
        self.temp_dir = Path('temp')
        self.dl_list_path = Path('dl_list.txt')
        self.quality_map = {1: 'LD', 2: 'SD', 3: 'HD', 4: 'HD+'}
        
        self.validate_paths()

    def find_firefox_binary(self):
        # Check common Firefox installation paths
        possible_paths = [
            r'C:\Program Files\Mozilla Firefox\firefox.exe',
            r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe',
            shutil.which('firefox')
        ]
        for path in possible_paths:
            if path and Path(path).exists():
                return path
        return None

    def validate_credentials(self):
        if not (self.email and self.password):
            raise ValueError("Email and password must be provided in .env file")

    def validate_paths(self):
        if not Path(self.geckodriver_path).exists():
            raise FileNotFoundError(f"Geckodriver not found at {self.geckodriver_path}")
        if not Path(self.firefox_binary_path).exists():
            raise FileNotFoundError(f"Firefox binary not found at {self.firefox_binary_path}")