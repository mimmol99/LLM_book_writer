import gradio as gr
from book_openai import BookOpenAI # Your existing backend logic
from dotenv import load_dotenv
from pathlib import Path
import os
import time # For creating unique filenames

# Load environment variables from .env file
load_dotenv()
# Note: OpenAI library usually picks up the key automatically if dotenv loads it
# or if it's set as an environment variable.

OUTPUT_DIR = "generated_books" # Directory to save generated files
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True) # Create output directory

def generate_book_interface(
    book_title,
    book_description,
    writing_style,
    target_language,
    n_chapters,
    n_subsections,
    file_type,
    progress=gr.Progress(track_tqdm=True) # Gradio progress tracking
):
    """
    Main function called by the Gradio interface to generate the book.
    Uses the BookOpenAI class and handles progress updates and file output.
    """
    status_message = "Starting generation...\n"
    output_file_path = None

    # --- Input Validation --- (Optional but good practice)
    if not all([book_title, book_description, writing_style, target_language]):
        return "Error: Please fill in all text fields.", None
    if not n_chapters or not n_subsections or n_chapters <= 0 or n_subsections <= 0:
         return "Error: Chapters and subsections must be positive numbers.", None
    # Ensure numbers are integers
    n_chapters = int(n_chapters)
    n_subsections = int(n_subsections)

    try:
        # --- Step 1: Initialize Generator ---
        progress(0.1, desc="Initializing Generator")
        status_message += "Initializing generator...\n"
        # Pass language during initialization
        book_generator = BookOpenAI(model_name="gpt-4o-mini", target_language=target_language)
        yield status_message, None # Update status, no file yet

        # --- Step 2: Generate Chapters ---
        progress(0.3, desc=f"Generating {n_chapters} Chapters")
        status_message += f"Generating {n_chapters} chapters...\n"
        yield status_message, None # Update status
        chapters_data = book_generator.generate_chapters(
            book_title, book_description, writing_style, n_chapters
        )
        status_message += "Chapters generated.\n"
        yield status_message, None # Update status

        # --- Step 3: Generate Subsections ---
        progress(0.6, desc=f"Generating {n_subsections} Subsections per Chapter")
        status_message += f"Generating {n_subsections} subsections per chapter...\n"
        yield status_message, None # Update status
        book_generator.generate_subsections(chapters_data, n_subsections)
        status_message += "Subsections generated.\n"
        yield status_message, None # Update status

        # --- Step 4: Generate Content ---
        progress(0.8, desc="Generating Content")
        status_message += "Generating content...\n"
        yield status_message, None # Update status
        book_generator.generate_content()
        status_message += "Content generation complete.\n"
        yield status_message, None # Update status

        # --- Step 5: Save File ---
        progress(0.9, desc=f"Saving as {file_type}")
        status_message += f"Saving book as {file_type}...\n"
        yield status_message, None # Update status

        # Create a unique filename to avoid conflicts
        safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '_')).rstrip()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_filename = f"{safe_title}_{target_language}_{timestamp}"

        file_extensions = { "PDF": ".pdf", "TXT": ".txt", "DOCX": ".docx" }
        extension = file_extensions.get(file_type, ".pdf")
        output_file_path = os.path.join(OUTPUT_DIR, f"{base_filename}{extension}")

        if file_type == "PDF":
            book_generator.save_as_pdf(output_file_path)
        elif file_type == "TXT":
            book_generator.save_as_txt(output_file_path)
        elif file_type == "DOCX":
            book_generator.save_as_docx(output_file_path)

        status_message += f"Book saved successfully to {output_file_path}\n"
        progress(1.0, desc="Completed")
        yield status_message, output_file_path # Final update with file path

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(f"Error during generation: {error_message}") # Log to console too
        # Return error message to status and None for file path
        yield f"{status_message}\nError: {error_message}", None

# --- Define Gradio Components ---
input_title = gr.Textbox(label="Book Title", placeholder="Enter the title of the book")
input_description = gr.Textbox(label="Book Description", lines=5, placeholder="Describe the book's content and purpose")
input_style = gr.Textbox(label="Writing Style", placeholder="e.g., Academic, Narrative, Technical, Humorous")
input_language = gr.Textbox(label="Target Language", value="English")
input_chapters = gr.Number(label="Number of Chapters", value=5, precision=0)
input_subsections = gr.Number(label="Number of Subsections per Chapter", value=3, precision=0)
input_filetype = gr.Dropdown(["PDF", "TXT", "DOCX"], label="Save as", value="PDF")

output_status = gr.Textbox(label="Status / Log", lines=10, interactive=False)
output_file = gr.File(label="Download Generated Book") # Component to display download link

# --- Create the Gradio Interface ---
iface = gr.Interface(
    fn=generate_book_interface,
    inputs=[
        input_title,
        input_description,
        input_style,
        input_language,
        input_chapters,
        input_subsections,
        input_filetype
    ],
    outputs=[
        output_status,
        output_file
    ],
    title="AI Book Generator",
    description="Enter details to generate a book using OpenAI. Generation might take some time.",
    flagging_mode="never", # <-- Use this instead
    # examples=[ # Optional: Add examples for users to click
    #     ["The Quantum Butterfly Effect", "A sci-fi novel exploring how small changes in quantum states affect macroscopic reality.", "Narrative with scientific explanations", "English", 10, 4, "PDF"]
    # ]
)

# --- Launch the Interface ---
if __name__ == "__main__":
    print(f"Generated books will be saved in: {os.path.abspath(OUTPUT_DIR)}")

    print("--- About to call iface.launch() ---") # <-- ADD THIS
    try:
        iface.launch() 
    except Exception as e:
        print(f"--- Error during iface.launch(): {e} ---") # <-- ADD THIS
        import traceback
        traceback.print_exc() # Print full traceback if launch fails

    print("--- iface.launch() has finished (server stopped) ---") # <-- ADD THIS (Likely only seen after Ctrl+C) 
