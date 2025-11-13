#!/usr/bin/env python3
"""
YouTube Video Downloader with Modern GUI
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

class ModernButton(tk.Canvas):
    """Custom modern button with hover effects"""
    def __init__(self, parent, text, command, bg_color="#3b82f6", hover_color="#2563eb", **kwargs):
        super().__init__(parent, height=40, bg=parent['bg'], highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text = text
        self.enabled = True
        
        self.rect = self.create_rectangle(0, 0, 0, 0, fill=bg_color, outline="", tags="button")
        self.text_id = self.create_text(0, 0, text=text, fill="white", font=("Segoe UI", 10, "bold"), tags="button")
        
        self.bind("<Configure>", self._resize)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        
    def _resize(self, event):
        self.coords(self.rect, 0, 0, event.width, event.height)
        self.coords(self.text_id, event.width/2, event.height/2)
        
    def _on_enter(self, event):
        if self.enabled:
            self.itemconfig(self.rect, fill=self.hover_color)
            
    def _on_leave(self, event):
        if self.enabled:
            self.itemconfig(self.rect, fill=self.bg_color)
            
    def _on_click(self, event):
        if self.enabled and self.command:
            self.command()
            
    def configure_state(self, state):
        self.enabled = state == 'normal'
        if not self.enabled:
            self.itemconfig(self.rect, fill="#6b7280")
        else:
            self.itemconfig(self.rect, fill=self.bg_color)

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("800x700")
        self.root.resizable(False, False)
        
        # Modern color scheme
        self.colors = {
            'bg': '#0f172a',           # Dark blue background
            'card': '#1e293b',         # Card background
            'card_hover': '#334155',   # Card hover
            'primary': '#3b82f6',      # Blue
            'primary_hover': '#2563eb',
            'success': '#10b981',      # Green
            'text': '#f1f5f9',         # Light text
            'text_secondary': '#94a3b8', # Secondary text
            'border': '#334155',       # Border color
            'accent': '#8b5cf6',       # Purple accent
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Get Downloads folder
        self.download_path = str(Path.home() / "Downloads")
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header = tk.Frame(main_frame, bg=self.colors['bg'])
        header.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(header, text="📥 YouTube Downloader", 
                        font=("Segoe UI", 24, "bold"),
                        bg=self.colors['bg'], fg=self.colors['text'])
        title.pack(side=tk.LEFT)
        
        subtitle = tk.Label(header, text="Download videos in your preferred quality", 
                           font=("Segoe UI", 10),
                           bg=self.colors['bg'], fg=self.colors['text_secondary'])
        subtitle.pack(side=tk.LEFT, padx=(10, 0), pady=(8, 0))
        
        # URL Card
        url_card = tk.Frame(main_frame, bg=self.colors['card'], highlightbackground=self.colors['border'], 
                           highlightthickness=1)
        url_card.pack(fill=tk.X, pady=(0, 15))
        
        url_inner = tk.Frame(url_card, bg=self.colors['card'])
        url_inner.pack(fill=tk.X, padx=20, pady=15)
        
        url_label = tk.Label(url_inner, text="Video URL", 
                            font=("Segoe UI", 11, "bold"),
                            bg=self.colors['card'], fg=self.colors['text'])
        url_label.pack(anchor=tk.W, pady=(0, 8))
        
        # Custom styled entry
        self.url_entry = tk.Entry(url_inner, font=("Segoe UI", 11),
                                 bg=self.colors['bg'], fg=self.colors['text'],
                                 insertbackground=self.colors['text'],
                                 relief=tk.FLAT, highlightthickness=2,
                                 highlightbackground=self.colors['border'],
                                 highlightcolor=self.colors['primary'])
        self.url_entry.pack(fill=tk.X, ipady=8, ipadx=10)
        
        # Fetch button
        btn_frame = tk.Frame(url_inner, bg=self.colors['card'])
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.fetch_btn = ModernButton(btn_frame, "🔍 Fetch Video Info", 
                                      command=self.fetch_formats,
                                      bg_color=self.colors['primary'],
                                      hover_color=self.colors['primary_hover'],
                                      width=200)
        self.fetch_btn.pack(side=tk.LEFT)
        
        # Video info card
        self.info_card = tk.Frame(main_frame, bg=self.colors['card'], 
                                 highlightbackground=self.colors['border'], 
                                 highlightthickness=1)
        
        info_inner = tk.Frame(self.info_card, bg=self.colors['card'])
        info_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        self.title_label = tk.Label(info_inner, text="", 
                                    font=("Segoe UI", 12, "bold"),
                                    bg=self.colors['card'], fg=self.colors['text'],
                                    wraplength=720, justify=tk.LEFT)
        self.title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Quality selection card
        quality_label = tk.Label(info_inner, text="Select Quality", 
                                font=("Segoe UI", 11, "bold"),
                                bg=self.colors['card'], fg=self.colors['text'])
        quality_label.pack(anchor=tk.W, pady=(10, 8))
        
        # Custom listbox
        list_frame = tk.Frame(info_inner, bg=self.colors['bg'], 
                             highlightbackground=self.colors['border'],
                             highlightthickness=1)
        list_frame.pack(fill=tk.X, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(list_frame, bg=self.colors['card'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.format_listbox = tk.Listbox(list_frame, 
                                        yscrollcommand=scrollbar.set,
                                        font=("Consolas", 10),
                                        bg=self.colors['bg'],
                                        fg=self.colors['text'],
                                        selectbackground=self.colors['primary'],
                                        selectforeground="white",
                                        relief=tk.FLAT,
                                        highlightthickness=0,
                                        height=6,
                                        activestyle='none')
        self.format_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        scrollbar.config(command=self.format_listbox.yview)
        
        # Download button
        self.download_btn = ModernButton(info_inner, "⬇️ Download Video", 
                                        command=self.start_download,
                                        bg_color=self.colors['success'],
                                        hover_color="#059669",
                                        width=200)
        self.download_btn.configure_state('disabled')
        self.download_btn.pack(anchor=tk.W, pady=(0, 5))
        
        # Progress card
        self.progress_card = tk.Frame(main_frame, bg=self.colors['card'], 
                                     highlightbackground=self.colors['border'], 
                                     highlightthickness=1)
        
        progress_inner = tk.Frame(self.progress_card, bg=self.colors['card'])
        progress_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        progress_label = tk.Label(progress_inner, text="Download Progress", 
                                 font=("Segoe UI", 11, "bold"),
                                 bg=self.colors['card'], fg=self.colors['text'])
        progress_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Custom progress bar
        progress_bg = tk.Frame(progress_inner, bg=self.colors['bg'], height=8,
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        progress_bg.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_fill = tk.Frame(progress_bg, bg=self.colors['primary'], height=6)
        self.progress_fill.place(x=1, y=1, width=0, height=6)
        
        # Status text
        self.status_text = tk.Text(progress_inner, 
                                  font=("Consolas", 9),
                                  bg=self.colors['bg'],
                                  fg=self.colors['text'],
                                  relief=tk.FLAT,
                                  height=6,
                                  wrap=tk.WORD,
                                  state='disabled',
                                  highlightbackground=self.colors['border'],
                                  highlightthickness=1)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Footer
        footer = tk.Frame(main_frame, bg=self.colors['bg'])
        footer.pack(fill=tk.X, pady=(15, 0))
        
        location_label = tk.Label(footer, 
                                 text=f"💾 Downloads saved to: {self.download_path}", 
                                 font=("Segoe UI", 9),
                                 bg=self.colors['bg'], 
                                 fg=self.colors['text_secondary'])
        location_label.pack(side=tk.LEFT)
        
        self.formats = []
        self.is_downloading = False
        
    def update_progress(self, percentage):
        """Update progress bar with actual percentage"""
        max_width = 756  # Approximate width of progress bar
        width = int((percentage / 100) * max_width)
        self.progress_fill.config(width=width)
        
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
            
        self.fetch_btn.configure_state('disabled')
        self.download_btn.configure_state('disabled')
        self.format_listbox.delete(0, tk.END)
        self.formats = []
        
        # Hide cards initially
        self.info_card.pack_forget()
        self.progress_card.pack_forget()
        
        # Show progress
        self.progress_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.log_status("🔍 Fetching video information...")
        self.update_progress(0)
        
        # Run in thread
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
                    
                    audio_info = "🔊 Audio" if acodec != 'none' else "🔇 No Audio"
                    fps_info = f" • {fps}fps" if fps else ""
                    
                    video_formats.append({
                        'id': format_id,
                        'description': f"📹 {resolution}{fps_info} • {ext} • {audio_info} • {size_str}",
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
            
            # Update GUI
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
        self.title_label.config(text=f"🎬 {title}")
        self.formats = formats
        
        for f in formats:
            self.format_listbox.insert(tk.END, f['description'])
        
        self.fetch_btn.configure_state('normal')
        self.download_btn.configure_state('normal')
        self.log_status(f"✅ Found {len(formats)} quality options")
        
        # Show info card
        self.info_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
    def _reset_ui(self):
        """Reset UI state"""
        self.progress_fill.config(width=0)
        self.fetch_btn.configure_state('normal')
        
    def start_download(self):
        """Start downloading selected format"""
        selection = self.format_listbox.curselection()
        
        if not selection:
            messagebox.showwarning("Warning", "Please select a quality option")
            return
            
        selected_idx = selection[0]
        selected_format = self.formats[selected_idx]
        url = self.url_entry.get().strip()
        
        self.fetch_btn.configure_state('disabled')
        self.download_btn.configure_state('disabled')
        self.is_downloading = True
        
        self.log_status(f"\n⬇️ Starting download: {selected_format['description']}")
        self.update_progress(0)
        
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
            
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.root.after(0, self.log_status, line)
            
            process.wait()
            
            if process.returncode == 0:
                self.root.after(0, lambda: messagebox.showinfo("Success", f"✅ Download completed!\n\nSaved to: {self.download_path}"))
                self.root.after(0, self.log_status, "\n✅ Download completed successfully!")
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "❌ Download failed. Check the status log."))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Download error:\n{str(e)}"))
        finally:
            self.root.after(0, self._download_complete)
            
    def _download_complete(self):
        """Reset UI after download"""
        self.progress_fill.config(width=0)
        self.fetch_btn.configure_state('normal')
        self.download_btn.configure_state('normal')
        self.is_downloading = False

def main():
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()