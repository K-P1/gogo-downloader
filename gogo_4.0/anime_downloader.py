from pathlib import Path
import requests
from tqdm import tqdm
import logging

class AnimeDownloader:
    def __init__(self, config, progress_callback=None):
        self.config = config
        self.progress_callback = progress_callback

    def download(self, links, nickname, keyword):
        dest_dir = self.config.default_download_dir / nickname / keyword
        dest_dir.mkdir(parents=True, exist_ok=True)
        failed_downloads = []

        for link in links:
            try:
                filename = f"{link.episode}.mp4"
                showname = f"{nickname} Episode {link.episode}"
                file_path = dest_dir / filename
                self.download_file(link.url, file_path, showname)
                if self.progress_callback:
                    self.progress_callback(f"Downloaded {showname}")
            except Exception as e:
                logging.error(f"Failed to download {showname}: {e}")
                failed_downloads.append(link)
                if self.progress_callback:
                    self.progress_callback(f"Failed: {showname}")

        return failed_downloads

    def download_file(self, url, file_path, showname):
        response = requests.get(url, stream=True, allow_redirects=True)
        expected_size = int(response.headers.get('content-length', 0))
        if file_path.exists() and file_path.stat().st_size == expected_size and expected_size > 1024:
            logging.info(f"{showname} already exists. Skipping.")
            return

        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            with open(file_path, 'wb') as f, tqdm(
                desc=showname,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024
            ) as bar:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
                    bar.update(len(chunk))