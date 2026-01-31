import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import shutil

items = []
folder = ""

def select_folder():
    global folder, items
    new_folder = filedialog.askdirectory(title="Open folder")
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
            im.thumbnail((150, 150), Image.LANCZOS)
            photo = ImageTk.PhotoImage(im)
            faded_pil = im.copy().convert("RGBA")
            faded_pil.putalpha(128)
            faded_photo = ImageTk.PhotoImage(faded_pil)
            target_var = tk.IntVar(value=0)
            row = idx // columns
            col = idx % columns
            frame = tk.Frame(inner_frame, bd=2, relief=tk.GROOVE, highlightbackground="dodgerblue", highlightthickness=0)
            frame.grid(row=row, column=col, padx=15, pady=15)
            lbl = tk.Label(frame, image=photo)
            lbl.image = photo
            lbl.pack()
            name = tk.Label(frame, text=os.path.basename(p), font=("", 9), wraplength=150)
            name.pack()
            size_lbl = tk.Label(frame, text="Choose size", font=("", 9), fg="gray")
            size_lbl.pack()
            def cycle_handler(event, var=target_var, fr=frame, lab=lbl, sz=size_lbl, orig=photo, fad=faded_photo):
                current = var.get()
                if current == 0:
                    new_target = 1024
                elif current == 1024:
                    new_target = 1536
                elif current == 1536:
                    new_target = 2048
                elif current == 2048:
                    new_target = 3072
                elif current == 3072:
                    new_target = 0
                else:
                    new_target = 1024
                var.set(new_target)
                if new_target > 0:
                    fr.config(highlightthickness=4)
                    sz.config(text=f"{new_target}px", fg="black")
                    lab.config(image=orig)
                    lab.image = orig
                else:
                    fr.config(highlightthickness=0)
                    sz.config(text="Choose size", fg="gray")
            lbl.bind("<Button-1>", cycle_handler)
            name.bind("<Button-1>", cycle_handler)
            size_lbl.bind("<Button-1>", cycle_handler)
            items.append((p, target_var, photo, faded_photo, frame, size_lbl))
        except:
            pass
    for c in range(columns):
        inner_frame.grid_columnconfigure(c, weight=1)

def unselect_all():
    for item in items:
        _, var, orig, _, frame, sz = item
        var.set(0)
        frame.config(highlightthickness=0)
        sz.config(text="Choose size", fg="gray")
        lab = frame.winfo_children()[0]
        lab.config(image=orig)
        lab.image = orig

def process_selected():
    selected_any = any(var.get() > 0 for _, var, _, _, _, _ in items)
    if not selected_any:
        messagebox.showinfo("No selection", "No images have a target size selected.")
        return
    count = 0
    for item in items:
        p, var, orig, fad, frame, sz = item
        target = var.get()
        if target <= 0:
            continue
        try:
            im = Image.open(p)
            w, h = im.size
            resized_dir = os.path.join(folder, f"resized_{target}")
            os.makedirs(resized_dir, exist_ok=True)
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
                    if exif is not None:
                        save_kwargs["exif"] = exif
                    rim.save(save_p, **save_kwargs)
                else:
                    rim.save(save_p)
            lab = frame.winfo_children()[0]
            lab.config(image=fad)
            lab.image = fad
            sz.config(text="Processed", fg="green")
            var.set(0)
            frame.config(highlightthickness=0)
            count += 1
        except Exception as e:
            print(f"Error processing {p}: {e}")
    if count > 0:
        messagebox.showinfo("Completed", f"Saved {count} images to their selected sizes.")
    else:
        messagebox.showinfo("Completed", "Processing failed. Check console for errors.")

root = tk.Tk()
root.title("Image Resize")
root.geometry("1200x900")
top = tk.Frame(root)
top.pack(fill=tk.X, pady=10)
tk.Button(top, text="Open Image Folder", command=select_folder).pack(side=tk.LEFT, padx=20)
lbl_folder = tk.Label(top, text="No folder selected")
lbl_folder.pack(side=tk.LEFT, padx=20)
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
def on_mouse_wheel(event):
    if event.num == 4 or event.delta > 0:
        canvas.yview_scroll(-1, "units")
    elif event.num == 5 or event.delta < 0:
        canvas.yview_scroll(1, "units")
canvas.bind_all("<MouseWheel>", on_mouse_wheel)
canvas.bind_all("<Button-4>", on_mouse_wheel)
canvas.bind_all("<Button-5>", on_mouse_wheel)
bottom = tk.Frame(root)
bottom.pack(fill=tk.X, pady=10)
tk.Button(bottom, text="Unselect all", command=unselect_all).pack(side=tk.LEFT, padx=20)
tk.Button(bottom, text="Process Selected Images", command=process_selected).pack(side=tk.LEFT, padx=20)
root.mainloop()

