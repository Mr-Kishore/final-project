import contextlib
import io
import json
import shutil
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .. import llm
from .. import core


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


class QueueWriter(io.TextIOBase):
    def __init__(self, callback):
        self.callback = callback

    def write(self, text):
        if text:
            self.callback(text)
        return len(text)

    def flush(self):
        return None


class WhatsAppCrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Crawler Dashboard")
        self.root.geometry("1300x760")
        self.root.minsize(1080, 640)

        self.selected_text_file = None
        self.selected_json_file = None
        self.is_busy = False
        self.log_buffer = []

        self._build_ui()
        self._refresh_file_lists()

    def _build_ui(self):
        main_vertical = ttk.Panedwindow(self.root, orient=tk.VERTICAL)
        main_vertical.pack(fill=tk.BOTH, expand=True)

        top_pane = ttk.Frame(main_vertical, padding=8)
        bottom_pane = ttk.Frame(main_vertical, padding=(8, 2, 8, 8))
        main_vertical.add(top_pane, weight=4)
        main_vertical.add(bottom_pane, weight=2)

        horizontal = ttk.Panedwindow(top_pane, orient=tk.HORIZONTAL)
        horizontal.pack(fill=tk.BOTH, expand=True)

        self.left_panel = ttk.Frame(horizontal, padding=6)
        self.center_panel = ttk.Frame(horizontal, padding=6)
        self.right_panel = ttk.Frame(horizontal, padding=6)
        horizontal.add(self.left_panel, weight=2)
        horizontal.add(self.center_panel, weight=3)
        horizontal.add(self.right_panel, weight=2)

        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()
        self._build_terminal(bottom_pane)

    def _build_left_panel(self):
        ttk.Label(self.left_panel, text="Project Files", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")

        split_frame = ttk.Panedwindow(self.left_panel, orient=tk.VERTICAL)
        split_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        txt_frame = ttk.LabelFrame(split_frame, text="Text Files (.txt)")
        json_frame = ttk.LabelFrame(split_frame, text="JSON Files (.json)")
        split_frame.add(txt_frame, weight=1)
        split_frame.add(json_frame, weight=1)

        self.txt_listbox = self._create_listbox(txt_frame)
        self.json_listbox = self._create_listbox(json_frame)

        self.txt_listbox.bind("<<ListboxSelect>>", self._on_select_text_file)
        self.json_listbox.bind("<<ListboxSelect>>", self._on_select_json_file)

    def _build_center_panel(self):
        ttk.Label(self.center_panel, text="Workspace Controls", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")

        file_box = ttk.LabelFrame(self.center_panel, text="Loaded Files")
        file_box.pack(fill=tk.X, pady=(8, 10))

        self.text_file_var = tk.StringVar(value="Input text: Not selected")
        self.json_file_var = tk.StringVar(value="Input JSON: Not selected")
        ttk.Label(file_box, textvariable=self.text_file_var).pack(anchor="w", padx=8, pady=(6, 2))
        ttk.Label(file_box, textvariable=self.json_file_var).pack(anchor="w", padx=8, pady=(0, 8))

        upload_box = ttk.LabelFrame(self.center_panel, text="Upload From Elsewhere")
        upload_box.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(
            upload_box,
            text="Import .txt or .json into the project folder, then load it from the left panel."
        ).pack(anchor="w", padx=8, pady=(6, 6))
        ttk.Button(upload_box, text="Upload File", command=self._upload_external_file).pack(anchor="w", padx=8, pady=(0, 8))

        run_box = ttk.LabelFrame(self.center_panel, text="Pipeline Actions")
        run_box.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(run_box, text="Run Parse + DB Insert", command=self._run_parse_pipeline).pack(fill=tk.X, padx=8, pady=(6, 4))
        ttk.Button(run_box, text="Run LLM Extraction", command=self._run_llm_extraction).pack(fill=tk.X, padx=8, pady=(0, 8))

        utility_box = ttk.LabelFrame(self.center_panel, text="Utilities")
        utility_box.pack(fill=tk.X)
        ttk.Button(utility_box, text="Refresh File Lists", command=self._refresh_file_lists).pack(fill=tk.X, padx=8, pady=(6, 4))
        ttk.Button(utility_box, text="Clear Terminal", command=self._clear_terminal).pack(fill=tk.X, padx=8, pady=(0, 8))

    def _build_right_panel(self):
        ttk.Label(self.right_panel, text="Finished Files / Logs", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")

        frame = ttk.Frame(self.right_panel)
        frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        self.output_listbox = self._create_listbox(frame)

        btn_row = ttk.Frame(self.right_panel)
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(btn_row, text="Open Selected", command=self._open_selected_output).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _build_terminal(self, parent):
        ttk.Label(parent, text="Terminal Output", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        terminal_box = ttk.Frame(parent)
        terminal_box.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        scrollbar = ttk.Scrollbar(terminal_box, orient=tk.VERTICAL)
        self.terminal_text = tk.Text(
            terminal_box,
            wrap=tk.WORD,
            bg="#111111",
            fg="#E0E0E0",
            insertbackground="#E0E0E0",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.terminal_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.terminal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._log("Ready. Select a .txt file from data/ and run the parser pipeline.")

    def _create_listbox(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, activestyle="none", exportselection=False)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return listbox

    def _refresh_file_lists(self):
        txt_files = sorted([p.name for p in DATA_DIR.glob("*.txt") if p.is_file()])
        json_files = sorted([p.name for p in DATA_DIR.glob("*.json") if p.is_file()])
        output_files = sorted([
            p.name for p in DATA_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in {".txt", ".json"}
        ])
        runtime_log = PROJECT_ROOT / "runtime.log"
        if runtime_log.exists():
            output_files.append(runtime_log.name)

        self._fill_listbox(self.txt_listbox, txt_files)
        self._fill_listbox(self.json_listbox, json_files)
        self._fill_listbox(self.output_listbox, output_files)

        if self.selected_text_file and not (DATA_DIR / self.selected_text_file).exists():
            self.selected_text_file = None
            self.text_file_var.set("Input text: Not selected")

        if self.selected_json_file and not (DATA_DIR / self.selected_json_file).exists():
            self.selected_json_file = None
            self.json_file_var.set("Input JSON: Not selected")

    def _fill_listbox(self, listbox, items):
        listbox.delete(0, tk.END)
        for item in items:
            listbox.insert(tk.END, item)

    def _on_select_text_file(self, _event):
        selection = self.txt_listbox.curselection()
        if not selection:
            return
        file_name = self.txt_listbox.get(selection[0])
        use_file = messagebox.askyesno(
            "Use This Text File?",
            f"Final warning: load '{file_name}' as input text file for this project run?"
        )
        if use_file:
            self.selected_text_file = file_name
            self.text_file_var.set(f"Input text: {file_name}")
            self._log(f"Loaded text file: {file_name}")
        else:
            self.txt_listbox.selection_clear(0, tk.END)

    def _on_select_json_file(self, _event):
        selection = self.json_listbox.curselection()
        if not selection:
            return
        file_name = self.json_listbox.get(selection[0])
        use_file = messagebox.askyesno(
            "Use This JSON File?",
            f"Final warning: load '{file_name}' as input JSON file for extraction?"
        )
        if use_file:
            self.selected_json_file = file_name
            self.json_file_var.set(f"Input JSON: {file_name}")
            self._log(f"Loaded JSON file: {file_name}")
        else:
            self.json_listbox.selection_clear(0, tk.END)

    def _upload_external_file(self):
        file_path = filedialog.askopenfilename(
            title="Select file to import",
            filetypes=[("Text or JSON files", "*.txt *.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        src = Path(file_path)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        dest = DATA_DIR / src.name
        if dest.exists():
            overwrite = messagebox.askyesno("File Exists", f"'{src.name}' already exists. Overwrite it?")
            if not overwrite:
                self._log(f"Upload cancelled for: {src.name}")
                return

        try:
            shutil.copy2(src, dest)
            self._log(f"Uploaded file: {src.name}")
            self._refresh_file_lists()
        except Exception as exc:
            messagebox.showerror("Upload Failed", str(exc))
            self._log(f"Upload failed for {src.name}: {exc}")

    def _run_parse_pipeline(self):
        if self.is_busy:
            self._log("A task is already running. Please wait.")
            return

        input_file = self.selected_text_file or "chat.txt"
        input_path = DATA_DIR / input_file
        if not input_path.exists():
            messagebox.showerror("Missing File", f"Text file '{input_file}' was not found in data/ folder.")
            return

        self._log(f"Starting parse pipeline using: {input_file}")
        self._run_in_background(self._parse_pipeline_worker, input_file)

    def _run_llm_extraction(self):
        if self.is_busy:
            self._log("A task is already running. Please wait.")
            return

        input_json = self.selected_json_file or "chat.json"
        input_path = DATA_DIR / input_json
        if not input_path.exists():
            messagebox.showerror("Missing File", f"JSON file '{input_json}' was not found in data/ folder.")
            return

        self._log(f"Starting LLM extraction using: {input_json}")
        self._run_in_background(self._llm_worker, input_json)

    def _parse_pipeline_worker(self, input_file):
        messages = core.parse_chat(input_file=str(DATA_DIR / input_file))
        if messages is None:
            self._log("Parsing failed.")
            return
        if not messages:
            self._log("No messages found after parsing.")
            return

        filtered_messages = [msg for msg in messages if not core.is_system_message(msg.get("text", ""))]
        core.save_messages_to_json(filtered_messages, output_file=str(DATA_DIR / "chat.json"))
        core.display_sample_messages(filtered_messages)
        core.filter_and_insert_messages(filtered_messages)
        self._log(f"Parse pipeline complete. Filtered messages: {len(filtered_messages)}")

    def _llm_worker(self, input_json):
        training_info = llm.extract_opportunities(str(DATA_DIR / input_json))
        if not training_info:
            self._log("No training/job opportunities extracted.")
            return

        output_file = DATA_DIR / "job_details.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(training_info, f, indent=2, ensure_ascii=False)

        self._log(f"LLM extraction complete. Records: {len(training_info)}")
        for idx, info in enumerate(training_info[:3], start=1):
            domain = info.get("domain/topic", "Unknown")
            location = info.get("location", "Unknown")
            contact = info.get("contact", "Unknown")
            self._log(f"{idx}. {domain} | {location} | {contact}")

    def _run_in_background(self, target, *args):
        self.is_busy = True
        thread = threading.Thread(target=self._thread_wrapper, args=(target, *args), daemon=True)
        thread.start()

    def _thread_wrapper(self, target, *args):
        writer = QueueWriter(self._queue_log)
        try:
            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                target(*args)
        except Exception as exc:
            self._queue_log(f"\nTask failed: {exc}\n")
        finally:
            self._queue_log("\nTask finished.\n")
            self.root.after(0, self._task_finished_ui)

    def _task_finished_ui(self):
        self.is_busy = False
        self._refresh_file_lists()

    def _queue_log(self, text):
        self.root.after(0, self._append_terminal_text, text)

    def _append_terminal_text(self, text):
        self.terminal_text.insert(tk.END, text)
        self.terminal_text.see(tk.END)
        self.log_buffer.append(text)
        self._write_runtime_log(text)

    def _write_runtime_log(self, text):
        try:
            with open(PROJECT_ROOT / "runtime.log", "a", encoding="utf-8") as log_file:
                log_file.write(text)
        except Exception:
            pass

    def _log(self, message):
        self._append_terminal_text(message.rstrip() + "\n")

    def _clear_terminal(self):
        self.terminal_text.delete("1.0", tk.END)
        self._log("Terminal cleared.")

    def _open_selected_output(self):
        selection = self.output_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Select a file from Finished Files / Logs.")
            return

        file_name = self.output_listbox.get(selection[0])
        file_path = PROJECT_ROOT / file_name if file_name == "runtime.log" else DATA_DIR / file_name
        if not file_path.exists():
            messagebox.showerror("Missing File", f"'{file_name}' no longer exists.")
            self._refresh_file_lists()
            return

        preview = tk.Toplevel(self.root)
        preview.title(f"Preview: {file_name}")
        preview.geometry("900x540")

        text_widget = tk.Text(preview, wrap=tk.WORD)
        scroll = ttk.Scrollbar(preview, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = f.read()
            text_widget.insert(tk.END, data)
            text_widget.see("1.0")
        except Exception as exc:
            text_widget.insert(tk.END, f"Failed to open file: {exc}")


def main():
    root = tk.Tk()
    app = WhatsAppCrawlerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
