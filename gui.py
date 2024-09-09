from book import BookOpenAI
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from dotenv import load_dotenv
from pathlib import Path
import threading
import os

load_dotenv(Path("./api_key.env"))
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class BookApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Generator")
        self.root.geometry("400x400")  # Adjusted height for additional input
        self.book_generator = BookOpenAI()
        self.create_widgets()

    def create_widgets(self):
        # Title input
        self.title_label = tk.Label(self.root, text="Book Title:")
        self.title_label.pack(pady=(20, 5))
        self.title_entry = tk.Entry(self.root, width=50)
        self.title_entry.pack()

        # Description input
        self.description_label = tk.Label(self.root, text="Book Description:")
        self.description_label.pack(pady=(15, 5))
        self.description_entry = tk.Text(self.root, width=50, height=5)
        self.description_entry.pack()

        # Writing style input
        self.style_label = tk.Label(self.root, text="Writing Style:")
        self.style_label.pack(pady=(15, 5))
        self.style_entry = tk.Entry(self.root, width=50)
        self.style_entry.pack()
        
        # Generate button
        self.generate_button = tk.Button(self.root, text="Generate Book", command=self.generate_book)
        self.generate_button.pack(pady=(20, 10))

        # File type selection
        self.file_type_label = tk.Label(self.root, text="Save as:")
        self.file_type_label.pack()
        self.file_type_var = tk.StringVar(value="PDF")
        file_types = ["PDF", "TXT", "DOCX"]
        self.file_type_menu = ttk.Combobox(self.root, textvariable=self.file_type_var, values=file_types, state="readonly")
        self.file_type_menu.pack()

        # Save button
        self.save_button = tk.Button(self.root, text="Save", command=self.save, state=tk.DISABLED)
        self.save_button.pack(pady=(10, 20))

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=300, mode='indeterminate')
        self.progress.pack()

    def generate_book(self):
        title = self.title_entry.get().strip()
        description = self.description_entry.get("1.0", tk.END).strip()
        writing_style = self.style_entry.get().strip()

        if not title or not description or not writing_style:
            messagebox.showwarning("Input Error", "Please provide the book title, description, and writing style.")
            return

        self.generate_button.config(state=tk.DISABLED)
        self.progress.start()
        print("Generating book...")

        # Run book generation in a separate thread to keep GUI responsive
        threading.Thread(target=self._generate_book_thread, args=(title, description, writing_style)).start()

    def _generate_book_thread(self, title, description, writing_style):
        try:
            print("Starting generation process...")
            self.book_generator.generate_chapters(title, description, writing_style)
            print("Chapters generated.")
            chapters = list(self.book_generator.chapters.keys())
            self.book_generator.generate_subsections(chapters)
            print("Subsections generated.")
            self.book_generator.generate_content()
            print("Content generated.")

            # Update GUI after generation
            self.root.after(0, self._generation_complete)
        except Exception as e:
            # Capture and handle the exception
            error_message = str(e)
            self.root.after(0, lambda: self._generation_error(error_message))

    def _generation_complete(self):
        self.progress.stop()
        self.generate_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)  # Enable save button after successful generation
        messagebox.showinfo("Success", "Book generated successfully!")
        print("Book generation complete.")

    def _generation_error(self, error_message):
        self.progress.stop()
        self.generate_button.config(state=tk.NORMAL)
        messagebox.showerror("Error", f"An error occurred during book generation: {error_message}")
        print(f"Error occurred: {error_message}")

    def save(self):
        filetype = self.file_type_var.get()
        file_extensions = {
            "PDF": ".pdf",
            "TXT": ".txt",
            "DOCX": ".docx"
        }
        extension = file_extensions.get(filetype, ".pdf")

        file_path = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[("All files", "*.*"), ("PDF files", "*.pdf"), ("Text files", "*.txt"), ("Word files", "*.docx")]
        )

        if not file_path:
            return

        try:
            if filetype == "PDF":
                self.book_generator.save_as_pdf(file_path)
            elif filetype == "TXT":
                self.book_generator.save_as_txt(file_path)
            elif filetype == "DOCX":
                self.book_generator.save_as_docx(file_path)

            messagebox.showinfo("Success", f"Book saved as {filetype} successfully!")
            print(f"Book saved as {filetype} successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving the file: {str(e)}")
            print(f"Error occurred while saving the file: {str(e)}")

# Start the application
if __name__ == "__main__":
    root = tk.Tk()
    app = BookApp(root)
    root.mainloop()

