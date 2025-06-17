import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import threading
import logging
from gogo_downloader_app import GogoDownloaderApp
from config import Config
from dl_list_manager import DlListManager

class GogoDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gogo Downloader v4.0")
        self.root.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.config = Config()
        self.app = GogoDownloaderApp(self.config)
        self.dl_list_manager = DlListManager(self.config.dl_list_path)
        self.is_downloading = False
        self.stop_event = threading.Event()

        self.setup_logging()
        self.create_widgets()
        self.update_dl_list_view()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('gogo_downloader.log'),
                logging.StreamHandler(),
                self.GUILogHandler(self)
            ]
        )

    class GUILogHandler(logging.Handler):
        def __init__(self, gui):
            super().__init__()
            self.gui = gui

        def emit(self, record):
            msg = self.format(record)
            self.gui.root.after(0, self.gui.append_log, msg)

    def create_widgets(self):
        # Input Frame
        input_frame = ctk.CTkFrame(self.root, fg_color="#1c2526")
        input_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(input_frame, text="Anime Download").grid(row=0, column=0, columnspan=2, pady=5)
        
        ctk.CTkLabel(input_frame, text="Nickname:").grid(row=1, column=0, padx=5, sticky="e")
        self.nickname_entry = ctk.CTkEntry(input_frame, placeholder_text="e.g., Naruto")
        self.nickname_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text="Anime Name:").grid(row=2, column=0, padx=5, sticky="e")
        self.anime_entry = ctk.CTkEntry(input_frame, placeholder_text="e.g., Naruto-dub")
        self.anime_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text="Episodes:").grid(row=3, column=0, padx=5, sticky="e")
        self.episode_entry = ctk.CTkEntry(input_frame, placeholder_text="e.g., 1-5, 1&9")
        self.episode_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text="Quality:").grid(row=4, column=0, padx=5, sticky="e")
        self.quality_var = tk.StringVar(value="3")
        quality_menu = ctk.CTkOptionMenu(
            input_frame,
            values=["1 (LD)", "2 (SD)", "3 (HD)", "4 (HD+)"],
            variable=self.quality_var
        )
        quality_menu.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Buttons
        button_frame = ctk.CTkFrame(input_frame, fg_color="#1c2526")
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        self.start_button = ctk.CTkButton(button_frame, text="Start Download", command=self.start_download)
        self.start_button.pack(side="left", padx=5)
        self.add_button = ctk.CTkButton(button_frame, text="Add to List", command=self.add_to_list)
        self.add_button.pack(side="left", padx=5)
        self.clear_button = ctk.CTkButton(button_frame, text="Clear List", command=self.clear_list)
        self.clear_button.pack(side="left", padx=5)

        # Download List View
        list_frame = ctk.CTkFrame(self.root, fg_color="#1c2526")
        list_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.tree = ttk.Treeview(
            list_frame,
            columns=("Nickname", "Anime", "Episodes"),
            show="headings",
            height=5
        )
        self.tree.heading("Nickname", text="Nickname")
        self.tree.heading("Anime", text="Anime Name")
        self.tree.heading("Episodes", text="Episodes")
        self.tree.column("Nickname", width=150)
        self.tree.column("Anime", width=250)
        self.tree.column("Episodes", width=100)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Progress and Log
        progress_frame = ctk.CTkFrame(self.root, fg_color="#1c2526")
        progress_frame.pack(pady=10, padx=10, fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        self.progress_bar.set(0)

        self.log_text = ctk.CTkTextbox(progress_frame, height=150, state="disabled")
        self.log_text.pack(fill="x", padx=5, pady=5)

    def append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def start_download(self):
        if self.is_downloading:
            self.stop_event.set()
            self.start_button.configure(text="Start Download")
            self.is_downloading = False
            return

        self.is_downloading = True
        self.start_button.configure(text="Stop Download")
        self.progress_bar.start()
        self.stop_event.clear()

        threading.Thread(target=self.run_download, daemon=True).start()

    def run_download(self):
        try:
            use_list = len(self.tree.get_children()) > 0
            if use_list:
                self.app.start_batch_download()
            else:
                nickname = self.nickname_entry.get() or "Naruto"
                keyword = self.anime_entry.get() or "Naruto-dub"
                epi = self.episode_entry.get() or "1-5"
                quality = int(self.quality_var.get().split()[0])
                self.app.start_single_download(nickname, keyword, epi, quality)
        except Exception as e:
            logging.error(f"Download error: {e}")
        finally:
            self.root.after(0, self.download_finished)

    def download_finished(self):
        self.is_downloading = False
        self.start_button.configure(text="Start Download")
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.update_dl_list_view()

    def add_to_list(self):
        nickname = self.nickname_entry.get() or "Naruto"
        keyword = self.anime_entry.get() or "Naruto-dub"
        epi = self.episode_entry.get() or "1-5"
        with open(self.config.dl_list_path, 'a') as f:
            f.write(f"{nickname} {keyword} {epi}\n")
        self.update_dl_list_view()

    def clear_list(self):
        self.dl_list_manager.ensure_exists()
        self.update_dl_list_view()

    def update_dl_list_view(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        entries = self.dl_list_manager.load_list()
        for entry in entries:
            self.tree.insert("", "end", values=(
                entry['nickname'],
                entry['keyword'],
                entry['epi']
            ))

def main():
    root = ctk.CTk()
    app = GogoDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()