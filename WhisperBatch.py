import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import whisper
import ffmpeg

class WhisperBatchApp:
    def __init__(self, master):
        self.master = master
        master.title("Whisper Batch Audio Converter")
        master.geometry('600x400')

        self.model_name = tk.StringVar(value='large-v3')

        self.audio_files = []
        self.output_dir = ''

        # File select
        self.select_files_btn = tk.Button(master, text="Select Audio Files", command=self.select_files)
        self.select_files_btn.pack(pady=10)

        self.files_label = tk.Label(master, text="No audio files selected.")
        self.files_label.pack()

        # Output dir select
        self.output_dir_btn = tk.Button(master, text="Select Output Directory", command=self.select_output_dir)
        self.output_dir_btn.pack(pady=10)

        self.output_dir_label = tk.Label(master, text="No output directory selected.")
        self.output_dir_label.pack()

        # Model selector
        self.model_frame = tk.Frame(master)
        self.model_frame.pack(pady=10)
        tk.Label(self.model_frame, text="Whisper model:").pack(side=tk.LEFT)
        tk.OptionMenu(
            self.model_frame,
            self.model_name,
            "tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"
        ).pack(side=tk.LEFT)

        # Start button
        self.start_btn = tk.Button(master, text="Start Batch Processing", command=self.start_batch)
        self.start_btn.pack(pady=20)

        # Status label
        self.status_text = tk.StringVar()
        self.status_label = tk.Label(master, textvariable=self.status_text, fg="blue", wraplength=580, justify="center")
        self.status_label.pack()

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=[("Audio files", "*.mp3 *.wav *.m4a *.flac *.aac *.ogg")]
        )
        if files:
            self.audio_files = list(files)
            self.files_label.config(text=f"{len(files)} audio files selected.")
        else:
            self.audio_files = []
            self.files_label.config(text="No audio files selected.")

    def select_output_dir(self):
        dir_selected = filedialog.askdirectory()
        if dir_selected:
            self.output_dir = dir_selected
            self.output_dir_label.config(text=self.output_dir)
        else:
            self.output_dir = ''
            self.output_dir_label.config(text="No output directory selected.")

    def start_batch(self):
        if not self.audio_files:
            messagebox.showerror("Error", "Please select audio files first.")
            return
        if not self.output_dir:
            messagebox.showerror("Error", "Please select an output directory.")
            return

        self.start_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.process_files, daemon=True).start()

    def process_files(self):
        try:
            # Load model once
            self.status_text.set(f"Loading Whisper model '{self.model_name.get()}'. This may take a while initially...")
            model = whisper.load_model(self.model_name.get())

            for idx, audio_path in enumerate(self.audio_files, 1):
                basename = os.path.splitext(os.path.basename(audio_path))[0]
                srt_out = os.path.join(self.output_dir, basename + ".srt")
                vid_out = os.path.join(self.output_dir, basename + ".mp4")

                self.status_text.set(f"[{idx}/{len(self.audio_files)}]\nTranscribing: {basename}")
                result = model.transcribe(audio_path)
                self.save_srt(result['segments'], srt_out)

                self.status_text.set(f"[{idx}/{len(self.audio_files)}]\nMaking video: {basename}")
                self.make_video(audio_path, srt_out, vid_out)

            self.status_text.set("✅ Batch processing finished.")
            messagebox.showinfo("Done", "All files processed successfully.")
        except Exception as e:
            self.status_text.set(f"Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.start_btn.config(state=tk.NORMAL)

    def save_srt(self, segments, srt_path):
        def ts(t):
            ms = int((t % 1) * 1000)
            s = int(t) % 60
            m = (int(t) // 60) % 60
            h = int(t) // 3600
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{ts(seg['start'])} --> {ts(seg['end'])}\n")
                f.write(f"{seg['text'].strip()}\n\n")

    def make_video(self, audio_path, srt_path, video_path):
        # get audio duration
        probe = ffmpeg.probe(audio_path)
        duration = float(probe['format']['duration'])

        # black video input
        black = ffmpeg.input(f"color=black:s=1280x720:d={duration}:r=25", f='lavfi')

        audio = ffmpeg.input(audio_path)

        # overlay subtitles and combine with lossless audio copy
        (
            ffmpeg
            .output(
                black.video.filter('subtitles', srt_path),
                audio.audio,
                video_path,
                vcodec='libx264', pix_fmt='yuv420p',
                acodec='copy',
                shortest=None,
                y=None
            )
            .global_args('-loglevel', 'error')
            .overwrite_output()
            .run()
        )

def main():
    root = tk.Tk()
    app = WhisperBatchApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
