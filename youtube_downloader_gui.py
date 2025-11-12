#!/usr/bin/env python3
"""
YouTube Video Downloader with GUI
Requires: yt-dlp, tkinter (usually pre-installed)
Install yt-dlp with: pip install yt-dlp
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import json
import threading
import os
from pathlib import Path

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Get Downloads folder
        self.download_path = str(Path.home() / "Downloads")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # URL input
        ttk.Label(main_frame, text="YouTube URL:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, width=70)
        self.url_entry.grid(row=1, column=0, columnspan=2, pady=5, padx=5)
        
        # Fetch button
        self.fetch_btn = ttk.Button(main_frame, text="Fetch Formats", command=self.fetch_formats)
        self.fetch_btn.grid(row=2, column=0, pady=10)
        
        # Video title
        self.title_label = ttk.Label(main_frame, text="", wraplength=650, font=('Arial', 9))
        self.title_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Format selection
        ttk.Label(main_frame, text="Available Qualities:", font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=5)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=5, column=0, columnspan=2, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.format_listbox = tk.Listbox(list_frame, width=80, height=10, yscrollcommand=scrollbar.set)
        self.format_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.config(command=self.format_listbox.yview)
        
        # Download button
        self.download_btn = ttk.Button(main_frame, text="Download Selected", command=self.start_download, state='disabled')
        self.download_btn.grid(row=6, column=0, pady=10)
        
        # Progress bar
        ttk.Label(main_frame, text="Progress:", font=('Arial', 10, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=5)
        self.progress = ttk.Progressbar(main_frame, length=650, mode='indeterminate')
        self.progress.grid(row=8, column=0, columnspan=2, pady=5)
        
        # Status text
        self.status_text = scrolledtext.ScrolledText(main_frame, width=80, height=8, wrap=tk.WORD, state='disabled')
        self.status_text.grid(row=9, column=0, columnspan=2, pady=5)
        
        # Download location
        location_label = ttk.Label(main_frame, text=f"Save location: {self.download_path}", font=('Arial', 8), foreground='gray')
        location_label.grid(row=10, column=0, columnspan=2, pady=5)
        
        self.formats = []
        
    def log_status(self, message):
        """Add message to status text"""
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')
        
    def fetch_formats(self):
        """Fetch available formats for the video"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        self.fetch_btn.config(state='disabled')
        self.download_btn.config(state='disabled')
        self.format_listbox.delete(0, tk.END)
        self.formats = []
        self.progress.start()
        self.log_status("Fetching video information...")
        
        # Run in thread to avoid freezing GUI
        thread = threading.Thread(target=self._fetch_formats_thread, args=(url,))
        thread.daemon = True
        thread.start()
        
    def _fetch_formats_thread(self, url):
        """Thread function to fetch formats"""
        try:
            cmd = ['yt-dlp', '-J', url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_info = json.loads(result.stdout)
            
            title = video_info.get('title', 'Unknown')
            formats = video_info.get('formats', [])
            
            # Process formats
            video_formats = []
            for f in formats:
                if f.get('vcodec') != 'none':
                    format_id = f.get('format_id')
                    ext = f.get('ext')
                    resolution = f.get('resolution', 'audio only')
                    fps = f.get('fps', 0)
                    acodec = f.get('acodec', 'none')
                    filesize = f.get('filesize') or f.get('filesize_approx', 0)
                    
                    if filesize:
                        size_mb = filesize / (1024 * 1024)
                        size_str = f"{size_mb:.1f}MB"
                    else:
                        size_str = "Unknown"
                    
                    audio_info = "with audio" if acodec != 'none' else "no audio"
                    fps_info = f" {fps}fps" if fps else ""
                    
                    video_formats.append({
                        'id': format_id,
                        'description': f"{resolution}{fps_info} ({ext}) - {audio_info} - {size_str}",
                        'resolution': resolution,
                        'has_audio': acodec != 'none'
                    })
            
            # Remove duplicates
            seen = set()
            unique_formats = []
            for f in video_formats:
                key = (f['resolution'], f['has_audio'])
                if key not in seen:
                    seen.add(key)
                    unique_formats.append(f)
            
            # Update GUI in main thread
            self.root.after(0, self._update_formats_ui, title, unique_formats)
            
        except subprocess.CalledProcessError as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch video info:\n{e}"))
            self.root.after(0, self._reset_ui)
        except FileNotFoundError:
            self.root.after(0, lambda: messagebox.showerror("Error", "yt-dlp not found. Install it with: pip install yt-dlp"))
            self.root.after(0, self._reset_ui)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{str(e)}"))
            self.root.after(0, self._reset_ui)
            
    def _update_formats_ui(self, title, formats):
        """Update UI with fetched formats"""
        self.progress.stop()
        self.title_label.config(text=f"Video: {title}")
        self.formats = formats
        
        for f in formats:
            self.format_listbox.insert(tk.END, f['description'])
        
        self.fetch_btn.config(state='normal')
        self.download_btn.config(state='normal')
        self.log_status(f"Found {len(formats)} quality options")
        
    def _reset_ui(self):
        """Reset UI state"""
        self.progress.stop()
        self.fetch_btn.config(state='normal')
        
    def start_download(self):
        """Start downloading selected format"""
        selection = self.format_listbox.curselection()
        
        if not selection:
            messagebox.showwarning("Warning", "Please select a quality option")
            return
            
        selected_idx = selection[0]
        selected_format = self.formats[selected_idx]
        url = self.url_entry.get().strip()
        
        self.fetch_btn.config(state='disabled')
        self.download_btn.config(state='disabled')
        self.progress.start()
        self.log_status(f"Starting download: {selected_format['description']}")
        
        # Run download in thread
        thread = threading.Thread(target=self._download_thread, args=(url, selected_format['id']))
        thread.daemon = True
        thread.start()
        
    def _download_thread(self, url, format_id):
        """Thread function to download video"""
        try:
            cmd = [
                'yt-dlp',
                '-f', f'{format_id}+bestaudio/best',
                '-P', self.download_path,
                '--newline',
                url
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Read output line by line
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.root.after(0, self.log_status, line)
            
            process.wait()
            
            if process.returncode == 0:
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Download completed!\n\nSaved to: {self.download_path}"))
                self.root.after(0, self.log_status, "✓ Download completed successfully!")
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Download failed. Check the status log for details."))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Download error:\n{str(e)}"))
        finally:
            self.root.after(0, self._download_complete)
            
    def _download_complete(self):
        """Reset UI after download"""
        self.progress.stop()
        self.fetch_btn.config(state='normal')
        self.download_btn.config(state='normal')

def main():
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()