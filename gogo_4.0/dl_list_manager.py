from pathlib import Path
import logging

class DlListManager:
    def __init__(self, dl_list_path):
        self.dl_list_path = dl_list_path
        self.ensure_exists()

    def ensure_exists(self):
        if not self.dl_list_path.exists():
            logging.info("Creating dl_list.txt")
            with open(self.dl_list_path, 'w') as f:
                f.write("Save-name Anime-name Episode\n")

    def load_list(self):
        with open(self.dl_list_path, 'r') as f:
            lines = f.readlines()
        entries = []
        for line in lines[1:]:  # Skip header
            if line.strip():
                parts = line.strip().split()
                if len(parts) in [2, 3]:
                    nickname = parts[0] if len(parts) == 3 else parts[1]
                    entries.append({
                        'nickname': nickname,
                        'keyword': parts[-2],
                        'epi': parts[-1]
                    })
        return entries

    def remove_completed(self, keyword, epi):
        with open(self.dl_list_path, 'r') as f:
            lines = f.readlines()
        with open(self.dl_list_path, 'w') as f:
            f.write(lines[0])  # Write header
            for line in lines[1:]:
                if not (keyword in line and epi in line):
                    f.write(line)