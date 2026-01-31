import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import shutil

items = []
folder = ""
target_size_var = None

def get_target_size():
    try:
        val = int(target_size_var.get().strip())
        if val > 0:
            return val
    except:
        pass
    return 1024

def select_folder():
    global folder, items
    new_folder = filedialog.askdirectory(title="Select folder containing images")
    if not new_folder:
        return
    folder = new_folder
    lbl_folder.config(text=f"Folder: {folder}")
    for child in inner_frame.winfo_children():
        child.destroy()
    items = []
    paths = [os.path.join(folder, fn) for fn in os.listdir(folder)]
    paths = [p for p in paths if os.path.isfile(p) and p.lower().split('.')[-1] in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']]
    paths.sort(key=os.path.basename)
    columns = 6
    for idx, p in enumerate(paths):
        try:
            im = Image.open(p)
            w, h = im.size
            var = tk.IntVar(value=0)
            im.thumbnail((150, 150), Image.LANCZOS)
            photo = ImageTk.PhotoImage(im)
            row = idx // columns
            col = idx % columns
            frame = tk.Frame(inner_frame, bd=2, relief=tk.GROOVE, highlightbackground="dodgerblue", highlightthickness=0)
            frame.grid(row=row, column=col, padx=15, pady=15)
            lbl = tk.Label(frame, image=photo)
            lbl.image = photo
            lbl.pack()
            name = tk.Label(frame, text=os.path.basename(p), font=("", 9), wraplength=150)
            name.pack()
            def toggle_handler(event, v=var, f=frame):
                new_val = 1 - v.get()
                v.set(new_val)
                if new_val:
                    f.config(highlightthickness=4)
                else:
                    f.config(highlightthickness=0)
            lbl.bind("<Button-1>", toggle_handler)
            name.bind("<Button-1>", toggle_handler)
            items.append((p, var, photo, frame))
        except:
            pass
    for c in range(columns):
        inner_frame.grid_columnconfigure(c, weight=1)

def process_selected():
    target = get_target_size()
    selected = [p for p, v, _, _ in items if v.get()]
    if not selected:
        messagebox.showinfo("No selection", "No images selected for processing.")
        return
    resized_dir = os.path.join(folder, "resized")
    os.makedirs(resized_dir, exist_ok=True)
    count = 0
    for p in selected:
        try:
            im = Image.open(p)
            w, h = im.size
            save_p = os.path.join(resized_dir, os.path.basename(p))
            if max(w, h) <= target:
                shutil.copy2(p, save_p)
            else:
                ratio = target / max(w, h)
                nw = round(w * ratio)
                nh = round(h * ratio)
                rim = im.resize((nw, nh), Image.LANCZOS)
                if im.format == "JPEG":
                    save_kwargs = {"quality": 95, "optimize": True}
                    exif = im.info.get("exif")
                    if exif:
                        save_kwargs["exif"] = exif
                    rim.save(save_p, **save_kwargs)
                else:
                    rim.save(save_p)
            count += 1
        except Exception as e:
            print(f"Error processing {p}: {e}")
    messagebox.showinfo("Completed", f"Processed {count} images to max {target} px.\nSaved to {resized_dir}")

root = tk.Tk()
root.title("Image Preview and Resize")
root.geometry("1400x900")

top = tk.Frame(root)
top.pack(fill=tk.X, pady=10)
tk.Button(top, text="Select Image Folder", command=select_folder).pack(side=tk.LEFT, padx=20)
lbl_folder = tk.Label(top, text="No folder selected yet")
lbl_folder.pack(side=tk.LEFT, padx=20)

tk.Label(top, text="Max long side (px):").pack(side=tk.LEFT)
target_size_var = tk.StringVar(value="1024")
tk.Entry(top, textvariable=target_size_var, width=8).pack(side=tk.LEFT, padx=5)

canvas_frame = tk.Frame(root)
canvas_frame.pack(fill=tk.BOTH, expand=True)
canvas = tk.Canvas(canvas_frame, bg="white")
scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
canvas.configure(yscrollcommand=scroll.set)
scroll.pack(side=tk.RIGHT, fill=tk.Y)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

inner_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=inner_frame, anchor=tk.NW)
inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))
canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

bottom = tk.Frame(root)
bottom.pack(fill=tk.X, pady=10)
tk.Button(bottom, text="Process Selected Images", command=process_selected).pack(pady=10)

root.mainloop()
