
import os
import subprocess
import shutil
import re
import tkinter as tk
from tkinter import filedialog, messagebox

def get_main_class(java_code):
    match = re.search(r'public\s+class\s+(\w+)', java_code)
    return match.group(1) if match else "Main"

def compile_java_to_jar(java_code, output_jar, main_class, author, jar_dependencies):
    java_file = f"{main_class}.java"
    build_dir = "build_classes"
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    with open(java_file, "w", encoding="utf-8") as f:
        f.write(java_code)
    
    classpath_files = []
    for jar in jar_dependencies:
        jar_name = os.path.basename(jar)
        if os.path.dirname(jar) != os.getcwd():
            if not os.path.exists(jar_name):
                shutil.copy(jar, jar_name)
        classpath_files.append(jar_name)
    
    classpath = ":".join(classpath_files) if classpath_files else ""
    compile_cmd = ["javac", "-d", build_dir, java_file]
    if classpath:
        compile_cmd.insert(1, "-cp")
        compile_cmd.insert(2, classpath)
    
    result = subprocess.run(compile_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        messagebox.showerror("Ошибка компиляции", result.stderr)
        return
    
    manifest_file = os.path.join(build_dir, "MANIFEST.MF")
    with open(manifest_file, "w") as mf:
        mf.write(f"Manifest-Version: 1.0\n")
        mf.write(f"Main-Class: {main_class}\n")
        mf.write(f"Author: {author}\n")
        if classpath_files:
            mf.write(f"Class-Path: {' '.join(classpath_files)}\n")
    
    jar_cmd = ["jar", "cfm", output_jar, manifest_file, "-C", build_dir, "."]
    result = subprocess.run(jar_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        messagebox.showerror("Ошибка создания JAR", result.stderr)
    else:
        messagebox.showinfo("Успех", f"JAR-файл успешно создан: {output_jar}")
    
    shutil.rmtree(build_dir)
    os.remove(java_file)

def save_jar():
    java_code = text_box.get("1.0", "end-1c").strip()
    if not java_code:
        messagebox.showwarning("Предупреждение", "Java-код не введён.")
        return
    main_class = main_class_entry.get().strip()
    if not main_class:
        messagebox.showwarning("Предупреждение", "Имя главного класса не указано.")
        return
    author = author_entry.get().strip()
    output_jar = filedialog.asksaveasfilename(title="Сохранить JAR как", defaultextension=".jar", filetypes=[["JAR Files", "*.jar"]])
    if output_jar:
        compile_java_to_jar(java_code, output_jar, main_class, author, jar_dependencies)

def add_jar_dependency():
    files = filedialog.askopenfilenames(title="Выбрать .jar библиотеки", filetypes=[["JAR Files", "*.jar"]])
    if files:
        jar_dependencies.extend(files)
        print("Добавленные библиотеки:", jar_dependencies)

def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)

def copy_text():
    text_box.event_generate("<<Copy>>")

def paste_text():
    text_box.event_generate("<<Paste>>")

def delete_text():
    text_box.delete("sel.first", "sel.last")

root = tk.Tk()
root.title("Java Compiler")

text_box = tk.Text(root, height=20, width=60)
text_box.pack()
text_box.bind("<Button-3>", show_context_menu)

context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Копировать", command=copy_text)
context_menu.add_command(label="Вставить", command=paste_text)
context_menu.add_command(label="Удалить", command=delete_text)

label1 = tk.Label(root, text="Главный класс:")
label1.pack()
main_class_entry = tk.Entry(root)
main_class_entry.pack()

label2 = tk.Label(root, text="Автор:")
label2.pack()
author_entry = tk.Entry(root)
author_entry.pack()

jar_dependencies = []
add_jar_button = tk.Button(root, text="Добавить .jar библиотеку", command=add_jar_dependency)
add_jar_button.pack()

save_button = tk.Button(root, text="Сохранить в JAR", command=save_jar)
save_button.pack()

root.mainloop()