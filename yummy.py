import os
import subprocess
import shutil
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import List, Optional, Tuple
import threading
import platform
import webbrowser
from pathlib import Path
import json


class JavaCompilerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Advanced Java Compiler")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)
        
        # Configuration
        self.config_file = Path.home() / ".java_compiler_config.json"
        self.jar_dependencies: List[str] = []
        self.theme = "light"
        self.font_size = 12
        self.load_config()
        
        # UI Setup
        self.setup_ui()
        self.setup_menu()
        self.apply_theme()
        
        # Auto-detect Java
        self.java_version = self.detect_java_version()
        if not self.java_version:
            messagebox.showwarning("Java Not Found", "Java JDK not found in PATH. Please install Java JDK to use this compiler.")

    def setup_ui(self):
        """Initialize all UI components"""
        self.setup_paned_window()
        self.setup_code_editor()
        self.setup_output_panel()
        self.setup_controls()
        self.setup_status_bar()

    def setup_paned_window(self):
        """Create paned window for resizable panels"""
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

    def setup_code_editor(self):
        """Set up the code editor with line numbers and syntax highlighting"""
        # Editor frame
        editor_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(editor_frame, weight=3)
        
        # Line numbers
        self.line_numbers = tk.Text(editor_frame, width=4, padx=5, pady=5, 
                                   takefocus=0, border=0, background="#f0f0f0",
                                   state="disabled")
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Code editor
        self.text_box = ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            font=("Consolas", self.font_size),
            undo=True,
            autoseparators=True,
            maxundo=-1
        )
        self.text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add right-click context menu
        self.setup_context_menu()
        
        # Bind events
        self.text_box.bind("<KeyRelease>", self.update_line_numbers)
        self.text_box.bind("<MouseWheel>", self.sync_scroll)
        self.text_box.bind("<Button-4>", self.sync_scroll)
        self.text_box.bind("<Button-5>", self.sync_scroll)
        
        # Initial line numbers
        self.update_line_numbers()

    def setup_output_panel(self):
        """Set up the output panel for compilation messages"""
        output_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(output_frame, weight=1)
        
        self.output_text = ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", self.font_size - 2),
            state="disabled",
            background="#f5f5f5"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def setup_controls(self):
        """Set up control buttons and input fields"""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Main class
        ttk.Label(control_frame, text="Main Class:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.main_class_entry = ttk.Entry(control_frame, width=30)
        self.main_class_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Author
        ttk.Label(control_frame, text="Author:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.author_entry = ttk.Entry(control_frame, width=30)
        self.author_entry.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=4, columnspan=2, sticky=tk.E, padx=5)
        
        self.add_jar_button = ttk.Button(button_frame, text="Add JARs", command=self.add_jar_dependency)
        self.add_jar_button.pack(side=tk.LEFT, padx=2)
        
        self.compile_button = ttk.Button(button_frame, text="Compile to JAR", command=self.compile_java)
        self.compile_button.pack(side=tk.LEFT, padx=2)
        
        # Dependencies list
        self.dependencies_list = tk.Listbox(
            control_frame,
            height=3,
            selectmode=tk.EXTENDED,
            background="white"
        )
        self.dependencies_list.grid(row=1, column=0, columnspan=5, sticky=tk.EW, pady=5, padx=5)
        self.dependencies_list.bind("<Delete>", self.remove_selected_dependencies)
        
        remove_button = ttk.Button(control_frame, text="Remove Selected", command=self.remove_selected_dependencies)
        remove_button.grid(row=1, column=5, sticky=tk.E, padx=5)

    def setup_status_bar(self):
        """Set up the status bar at the bottom"""
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X)

    def setup_menu(self):
        """Set up the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.text_box.edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.text_box.edit_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut_text, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy_text, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste_text, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Light Theme", command=lambda: self.set_theme("light"))
        view_menu.add_command(label="Dark Theme", command=lambda: self.set_theme("dark"))
        view_menu.add_separator()
        view_menu.add_command(label="Increase Font", command=self.increase_font)
        view_menu.add_command(label="Decrease Font", command=self.decrease_font)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        
        # Bind keyboard shortcuts
        self.root.bind_all("<Control-n>", lambda e: self.new_file())
        self.root.bind_all("<Control-o>", lambda e: self.open_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_file())
        self.root.bind_all("<Control-z>", lambda e: self.text_box.edit_undo())
        self.root.bind_all("<Control-y>", lambda e: self.text_box.edit_redo())
        self.root.bind_all("<Control-a>", lambda e: self.select_all())

    def setup_context_menu(self):
        """Set up the right-click context menu"""
        self.context_menu = tk.Menu(self.text_box, tearoff=0)
        self.context_menu.add_command(label="Undo", command=self.text_box.edit_undo)
        self.context_menu.add_command(label="Redo", command=self.text_box.edit_redo)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cut", command=self.cut_text)
        self.context_menu.add_command(label="Copy", command=self.copy_text)
        self.context_menu.add_command(label="Paste", command=self.paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self.select_all)
        
        self.text_box.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Show the context menu at the cursor position"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def update_line_numbers(self, event=None):
        """Update the line numbers in the editor"""
        lines = self.text_box.get("1.0", "end-1c").split("\n")
        line_count = len(lines)
        
        # Update line numbers
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        
        for i in range(1, line_count + 1):
            self.line_numbers.insert("end", f"{i}\n")
        
        self.line_numbers.config(state="disabled")
        
        # Highlight current line
        self.highlight_current_line()

    def sync_scroll(self, *args):
        """Synchronize scrolling between text widget and line numbers"""
        self.line_numbers.yview_moveto(self.text_box.yview()[0])
        self.highlight_current_line()

    def highlight_current_line(self):
        """Highlight the current line in the editor"""
        self.text_box.tag_remove("current_line", "1.0", "end")
        
        current_line = self.text_box.index(tk.INSERT).split(".")[0]
        self.text_box.tag_add("current_line", f"{current_line}.0", f"{current_line}.end")
        self.text_box.tag_config("current_line", background="#e6f3ff")

    def apply_theme(self):
        """Apply the current theme settings"""
        if self.theme == "dark":
            bg = "#2d2d2d"
            fg = "#ffffff"
            editor_bg = "#1e1e1e"
            line_bg = "#252526"
            current_line = "#3a3a3a"
        else:
            bg = "#f0f0f0"
            fg = "#000000"
            editor_bg = "#ffffff"
            line_bg = "#f0f0f0"
            current_line = "#e6f3ff"
        
        # Apply to all widgets
        self.root.config(bg=bg)
        
        # Editor
        self.text_box.config(
            background=editor_bg,
            foreground=fg,
            insertbackground=fg,
            selectbackground="#4d97ff",
            selectforeground=fg
        )
        self.line_numbers.config(
            background=line_bg,
            foreground=fg
        )
        self.text_box.tag_config("current_line", background=current_line)
        
        # Output
        self.output_text.config(
            background=editor_bg,
            foreground=fg,
            insertbackground=fg
        )
        
        # Dependencies list
        self.dependencies_list.config(
            background="white" if self.theme == "light" else "#3c3c3c",
            foreground=fg
        )

    def set_theme(self, theme: str):
        """Set the application theme"""
        self.theme = theme
        self.apply_theme()
        self.save_config()

    def increase_font(self):
        """Increase the editor font size"""
        self.font_size = min(self.font_size + 1, 24)
        self.text_box.config(font=("Consolas", self.font_size))
        self.output_text.config(font=("Consolas", self.font_size - 2))
        self.save_config()

    def decrease_font(self):
        """Decrease the editor font size"""
        self.font_size = max(self.font_size - 1, 8)
        self.text_box.config(font=("Consolas", self.font_size))
        self.output_text.config(font=("Consolas", self.font_size - 2))
        self.save_config()

    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.theme = config.get("theme", "light")
                    self.font_size = config.get("font_size", 12)
                    self.jar_dependencies = config.get("dependencies", [])
                    self.update_dependencies_list()
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                "theme": self.theme,
                "font_size": self.font_size,
                "dependencies": self.jar_dependencies
            }
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def update_status(self, message: str):
        """Update the status bar message"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()

    def update_dependencies_list(self):
        """Update the dependencies listbox"""
        self.dependencies_list.delete(0, tk.END)
        for dep in self.jar_dependencies:
            self.dependencies_list.insert(tk.END, os.path.basename(dep))

    def new_file(self):
        """Create a new file"""
        self.text_box.delete("1.0", tk.END)
        self.main_class_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.clear_output()
        self.update_status("New file created")

    def open_file(self):
        """Open a Java file"""
        file_path = filedialog.askopenfilename(
            filetypes=[["Java Files", "*.java"], ["All Files", "*.*"]]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.text_box.delete("1.0", tk.END)
                    self.text_box.insert("1.0", content)
                    
                    # Try to detect main class
                    main_class = self.detect_main_class(content)
                    if main_class:
                        self.main_class_entry.delete(0, tk.END)
                        self.main_class_entry.insert(0, main_class)
                    
                    self.update_status(f"Opened: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def save_file(self):
        """Save the current content to a Java file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".java",
            filetypes=[["Java Files", "*.java"], ["All Files", "*.*"]]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    content = self.text_box.get("1.0", "end-1c")
                    f.write(content)
                    self.update_status(f"Saved: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def clear_output(self):
        """Clear the output panel"""
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state="disabled")

    def append_output(self, text: str):
        """Append text to the output panel"""
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state="disabled")

    def detect_main_class(self, java_code: str) -> Optional[str]:
        """Detect the main class from Java code"""
        match = re.search(r'public\s+class\s+(\w+)', java_code)
        return match.group(1) if match else None

    def detect_java_version(self) -> Optional[str]:
        """Detect installed Java version"""
        try:
            result = subprocess.run(
                ["javac", "-version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            if result.returncode == 0:
                return result.stderr.strip() or result.stdout.strip()
        except FileNotFoundError:
            return None
        return None

    def add_jar_dependency(self):
        """Add JAR files as dependencies"""
        files = filedialog.askopenfilenames(
            title="Select JAR Dependencies",
            filetypes=[["JAR Files", "*.jar"], ["All Files", "*.*"]]
        )
        if files:
            # Add only new dependencies
            new_deps = [f for f in files if f not in self.jar_dependencies]
            self.jar_dependencies.extend(new_deps)
            self.update_dependencies_list()
            self.save_config()
            self.update_status(f"Added {len(new_deps)} JAR dependencies")

    def remove_selected_dependencies(self, event=None):
        """Remove selected dependencies from the list"""
        selected = self.dependencies_list.curselection()
        if selected:
            # Remove in reverse order to maintain correct indices
            for i in reversed(selected):
                del self.jar_dependencies[i]
            self.update_dependencies_list()
            self.save_config()
            self.update_status(f"Removed {len(selected)} dependencies")

    def compile_java(self):
        """Compile the Java code to a JAR file"""
        java_code = self.text_box.get("1.0", "end-1c").strip()
        if not java_code:
            messagebox.showwarning("Warning", "Please enter Java code to compile.")
            return
        
        main_class = self.main_class_entry.get().strip()
        if not main_class:
            detected_class = self.detect_main_class(java_code)
            if detected_class:
                main_class = detected_class
            else:
                messagebox.showwarning("Warning", "Please specify the main class.")
                return
        
        author = self.author_entry.get().strip() or "Unknown"
        
        output_jar = filedialog.asksaveasfilename(
            title="Save JAR As",
            defaultextension=".jar",
            filetypes=[["JAR Files", "*.jar"]]
        )
        if not output_jar:
            return
        
        # Show compilation in progress
        self.clear_output()
        self.append_output(f"Compiling {main_class}.java to {os.path.basename(output_jar)}...\n")
        self.update_status("Compiling...")
        self.compile_button.config(state="disabled")
        
        # Run compilation in a separate thread
        threading.Thread(
            target=self.compile_java_thread,
            args=(java_code, output_jar, main_class, author),
            daemon=True
        ).start()

    def compile_java_thread(self, java_code: str, output_jar: str, main_class: str, author: str):
        """Thread function for Java compilation"""
        try:
            # Create temporary directory
            temp_dir = Path("temp_build")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir()
            
            # Write Java file
            java_file = temp_dir / f"{main_class}.java"
            with open(java_file, "w", encoding="utf-8") as f:
                f.write(java_code)
            
            # Prepare classpath
            classpath = [str(Path(dep).absolute()) for dep in self.jar_dependencies]
            classpath_str = os.pathsep.join(classpath)
            
            # Compile Java code
            compile_cmd = ["javac", "-d", str(temp_dir)]
            if classpath_str:
                compile_cmd.extend(["-cp", classpath_str])
            compile_cmd.append(str(java_file))
            
            self.append_output(f"Compile command: {' '.join(compile_cmd)}\n")
            
            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            if result.returncode != 0:
                self.append_output("Compilation failed:\n")
                self.append_output(result.stderr)
                self.root.after(0, lambda: messagebox.showerror(
                    "Compilation Error",
                    "Failed to compile Java code. See output for details."
                ))
                return
            
            self.append_output("Compilation successful!\n")
            
            # Create manifest
            manifest_file = temp_dir / "MANIFEST.MF"
            with open(manifest_file, "w") as mf:
                mf.write(f"Manifest-Version: 1.0\n")
                mf.write(f"Main-Class: {main_class}\n")
                mf.write(f"Author: {author}\n")
                if classpath:
                    mf.write(f"Class-Path: {' '.join(os.path.basename(dep) for dep in classpath)}\n")
            
            # Create JAR file
            jar_cmd = [
                "jar", "cfm",
                str(Path(output_jar).absolute()),
                str(manifest_file),
                "-C", str(temp_dir), "."
            ]
            
            self.append_output(f"JAR command: {' '.join(jar_cmd)}\n")
            
            result = subprocess.run(
                jar_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            if result.returncode != 0:
                self.append_output("JAR creation failed:\n")
                self.append_output(result.stderr)
                self.root.after(0, lambda: messagebox.showerror(
                    "JAR Creation Error",
                    "Failed to create JAR file. See output for details."
                ))
                return
            
            self.append_output(f"Successfully created JAR file: {output_jar}\n")
            self.root.after(0, lambda: messagebox.showinfo(
                "Success",
                f"JAR file successfully created:\n{output_jar}"
            ))
            
        except Exception as e:
            self.append_output(f"Error: {str(e)}\n")
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"An unexpected error occurred: {e}"
            ))
        finally:
            # Clean up and update UI
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            self.root.after(0, lambda: self.update_status("Ready"))
            self.root.after(0, lambda: self.compile_button.config(state="normal"))

    def cut_text(self):
        """Cut selected text"""
        self.text_box.event_generate("<<Cut>>")

    def copy_text(self):
        """Copy selected text"""
        self.text_box.event_generate("<<Copy>>")

    def paste_text(self):
        """Paste text from clipboard"""
        self.text_box.event_generate("<<Paste>>")

    def select_all(self):
        """Select all text in the editor"""
        self.text_box.tag_add(tk.SEL, "1.0", tk.END)
        self.text_box.mark_set(tk.INSERT, "1.0")
        self.text_box.see(tk.INSERT)

    def show_about(self):
        """Show about dialog"""
        about_text = (
            "Advanced Java Compiler\n"
            "Version 2.0\n\n"
            "A feature-rich Java compiler with GUI interface\n\n"
            "Features:\n"
            "- Syntax highlighting\n"
            "- Line numbers\n"
            "- Dependency management\n"
            "- Theme support\n"
            "- Cross-platform\n\n"
            "© 2025 Java Compiler Project"
        )
        messagebox.showinfo("About", about_text)

    def show_docs(self):
        """Open documentation in browser"""
        webbrowser.open("https://docs.oracle.com/javase/tutorial/")

    def exit_app(self):
        """Exit the application"""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.save_config()
            self.root.destroy()


def main():
    root = tk.Tk()
    app = JavaCompilerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()