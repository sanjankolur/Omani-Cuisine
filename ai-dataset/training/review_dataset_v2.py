
from pathlib import Path
import csv
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageOps

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "ai-dataset" / "split_data"
OUTPUT_ROOT = ROOT / "ai-dataset" / "curated_v2"
IMAGES_OUT = OUTPUT_ROOT / "images_by_class"
LOG_PATH = OUTPUT_ROOT / "review_log.csv"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def read_log():
    records = {}
    if LOG_PATH.exists():
        with LOG_PATH.open("r", newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                records[row["source_path"]] = row
    return records


def write_log(records):
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_path", "original_split", "original_label",
        "decision", "final_label", "notes"
    ]
    with LOG_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records.values())


class ReviewApp:

    def __init__(self, root):
        self.root = root
        self.root.title("OMAN FOOD AI - Dataset V2 Review")
        self.root.geometry("1050x780")
        self.root.minsize(800, 600)

        if not SOURCE_ROOT.is_dir():
            messagebox.showerror(
                "Missing dataset", f"Cannot find:\n{SOURCE_ROOT}"
            )
            root.destroy()
            return

        train_dir = SOURCE_ROOT / "train"
        self.classes = sorted(
            p.name for p in train_dir.iterdir() if p.is_dir()
        )

        self.records = read_log()
        self.items = []

        for split in ("train", "val", "test"):
            split_dir = SOURCE_ROOT / split

            if not split_dir.exists():
                continue

            for class_dir in sorted(
                p for p in split_dir.iterdir() if p.is_dir()
            ):
                for file in sorted(class_dir.rglob("*")):
                    if file.is_file() and file.suffix.lower() in IMAGE_EXTS:
                        self.items.append({
                            "path": file.resolve(),
                            "split": split,
                            "label": class_dir.name
                        })

        self.index = 0
        self.photo = None
        self.choice = tk.StringVar(
            value=self.classes[0] if self.classes else ""
        )
        self.status = tk.StringVar()
        self.info = tk.StringVar()
        self.note = tk.StringVar()

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        ttk.Label(
            top,
            text="OMAN FOOD AI - Dataset V2 Review",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w")

        ttk.Label(
            top,
            text="Review each image. Original images are never deleted."
        ).pack(anchor="w")

        self.image_label = ttk.Label(root, anchor="center")
        self.image_label.pack(fill="both", expand=True, padx=10, pady=8)

        ttk.Label(
            root, textvariable=self.info,
            font=("Segoe UI", 11, "bold")
        ).pack()

        ttk.Label(root, textvariable=self.status).pack(pady=8)

        controls = ttk.Frame(root, padding=8)
        controls.pack(fill="x")

        ttk.Button(
            controls, text="Previous", command=self.previous
        ).pack(side="left", padx=4)

        ttk.Button(
            controls, text="Next", command=self.next
        ).pack(side="left", padx=4)

        ttk.Button(
            controls, text="Approve", command=self.approve
        ).pack(side="left", padx=4)

        ttk.Button(
            controls, text="Reject", command=self.reject
        ).pack(side="left", padx=4)

        ttk.Button(
            controls, text="Unsure", command=self.unsure
        ).pack(side="left", padx=4)

        relabel = ttk.Frame(root, padding=10)
        relabel.pack(fill="x")

        ttk.Label(relabel, text="Correct category:").pack(side="left")

        self.combo = ttk.Combobox(
            relabel,
            textvariable=self.choice,
            values=self.classes,
            state="readonly",
            width=25
        )
        self.combo.pack(side="left", padx=6)

        ttk.Button(
            relabel,
            text="Relabel + include",
            command=self.relabel
        ).pack(side="left", padx=5)

        ttk.Label(relabel, text="Notes:").pack(side="left", padx=5)

        ttk.Entry(
            relabel, textvariable=self.note, width=30
        ).pack(side="left", fill="x", expand=True)

        if not self.items:
            messagebox.showinfo(
                "No images", "No images found in the dataset."
            )
            return

        self.show_current()

    def current_key(self):
        return str(self.items[self.index]["path"])

    def show_current(self):
        item = self.items[self.index]
        path = item["path"]

        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((900, 500))
                self.photo = ImageTk.PhotoImage(image.copy())

            self.image_label.configure(image=self.photo, text="")

        except Exception as error:
            self.photo = None
            self.image_label.configure(
                image="",
                text=f"Cannot open image: {error}"
            )

        self.info.set(
            f"{self.index + 1}/{len(self.items)} | "
            f"Category: {item['label']} | Split: {item['split']}"
        )

        previous = self.records.get(self.current_key())

        if previous:
            self.status.set(
                f"Previously reviewed: {previous['decision']}"
            )
            self.note.set(previous.get("notes", ""))
        else:
            self.status.set(f"Not reviewed: {path.name}")
            self.note.set("")

        self.choice.set(item["label"])

    def save_decision(self, decision, final_label=""):
        item = self.items[self.index]
        key = self.current_key()

        self.records[key] = {
            "source_path": key,
            "original_split": item["split"],
            "original_label": item["label"],
            "decision": decision,
            "final_label": final_label,
            "notes": self.note.get().strip()
        }

        write_log(self.records)

        # Remove an earlier V2 copy if this image is reviewed again.
        filename = (
            f"{item['split']}__{item['path'].stem}"
            f"{item['path'].suffix.lower()}"
        )

        if IMAGES_OUT.exists():
            for old_file in IMAGES_OUT.glob(f"*/{filename}"):
                if old_file.is_file():
                    old_file.unlink()

        if decision in ("approve", "relabel"):
            destination = IMAGES_OUT / final_label
            destination.mkdir(parents=True, exist_ok=True)

            shutil.copy2(
                item["path"],
                destination / filename
            )

        self.status.set(f"Saved: {decision}")
        self.next()

    def approve(self):
        self.save_decision(
            "approve",
            self.items[self.index]["label"]
        )

    def reject(self):
        self.save_decision("reject")

    def unsure(self):
        self.save_decision("unsure")

    def relabel(self):
        new_label = self.choice.get()

        if new_label not in self.classes:
            messagebox.showwarning(
                "Choose category",
                "Please select a valid category."
            )
            return

        self.save_decision("relabel", new_label)

    def next(self):
        if self.index < len(self.items) - 1:
            self.index += 1
            self.show_current()
        else:
            messagebox.showinfo(
                "Review complete",
                "You reached the end. Your decisions have been saved."
            )

    def previous(self):
        if self.index > 0:
            self.index -= 1
            self.show_current()


if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewApp(root)
    root.mainloop()
