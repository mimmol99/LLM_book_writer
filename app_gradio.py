# app_gradio.py (Adapted for automatic language/structure in book_openai.py)

import gradio as gr
# Ensure book_openai.py is using the modified code provided by the user
from book_openai import BookOpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
import time
import traceback
import logging # Import logging

# Load environment variables from .env file
load_dotenv()

OUTPUT_DIR = "generated_books" # Directory to save generated files
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True) # Create output directory
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Modified Gradio function ---
def generate_book_interface(
    book_title,
    book_description,
    writing_style,
    # Removed language, n_chapters, n_subsections
    file_type,
    progress=gr.Progress(track_tqdm=True) # Gradio progress tracking
):
    """
    Main function called by the Gradio interface to generate the book.
    Relies on BookOpenAI class to internally handle language detection
    and determine chapter/subsection counts.
    """
    status_message = "Starting process...\n"
    output_file_path = None
    book_generator = None # Initialize to None

    # --- Input Validation ---
    if not all([book_title, book_description, writing_style]):
        # Use yield to update the status message correctly in Gradio
        yield "Error: Please fill in Title, Description, and Writing Style.", None
        return # Stop execution

    try:
        # --- Step 1: Initialize Generator ---
        progress(0.1, desc="Initializing Generator")
        status_message += "Initializing generator...\n"
        yield status_message, None
        # The __init__ might still take target_language, but generate_chapters overwrites it
        book_generator = BookOpenAI(model_name="gpt-4o-mini")

        # --- Step 2: Generate Chapters (Handles Language Detection Internally) ---
        progress(0.3, desc="Generating Chapters (Language Detected Internally)")
        status_message += "Generating chapters (detecting language internally)...\n"
        yield status_message, None
        # This method now returns the chapter list *and* sets self.target_language
        chapters_data = book_generator.generate_chapters(
            book_title, book_description, writing_style
        )
        # Check if chapter generation failed (e.g., language detection failed)
        if chapters_data is None:
            status_message += "Error: Failed to generate chapters (possibly language detection failure).\n"
            yield status_message, None
            return # Stop execution
        status_message += f"Language '{book_generator.target_language}' used. Chapters generated ({len(chapters_data)} chapters determined by AI).\n"
        yield status_message, None

        # --- Step 3: Generate Subsections (Determined by AI) ---
        progress(0.6, desc="Generating Subsections (Determined by AI)")
        status_message += "Generating subsections for each chapter (determined by AI)...\n"
        yield status_message, None
        # Pass the returned chapter objects to generate_subsections
        book_generator.generate_subsections(chapters_data)
        status_message += "Subsections generated.\n"
        yield status_message, None

        # --- Step 4: Generate Content ---
        progress(0.8, desc="Generating Content")
        status_message += "Generating content (this may take a while)...\n"
        yield status_message, None
        book_generator.generate_content() # Modifies internal state
        status_message += "Content generation complete.\n"
        yield status_message, None

        # --- Step 5: Save File ---
        progress(0.9, desc=f"Saving as {file_type}")
        status_message += f"Saving book as {file_type}...\n"
        yield status_message, None

        # Create filename (ensure book_generator has title/language set)
        safe_title = "".join(c for c in book_generator.title if c.isalnum() or c in (' ', '_')).rstrip()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        # Use target_language from the generator instance
        lang = book_generator.target_language # Should be set by generate_chapters
        if not lang: # Fallback just in case
             lang = "unknown_lang"
             status_message += "Warning: Target language was not set properly, using default filename.\n"

        base_filename = f"{safe_title}_{lang}_{timestamp}"

        file_extensions = { "PDF": ".pdf", "TXT": ".txt", "DOCX": ".docx" }
        extension = file_extensions.get(file_type, ".pdf")
        output_file_path = os.path.join(OUTPUT_DIR, f"{base_filename}{extension}")

        if file_type == "PDF":
            book_generator.save_as_pdf(output_file_path)
        elif file_type == "TXT":
            book_generator.save_as_txt(output_file_path)
        elif file_type == "DOCX":
            book_generator.save_as_docx(output_file_path)

        status_message += f"Book saved successfully: {output_file_path}\n"
        progress(1.0, desc="Completed")
        yield status_message, output_file_path # Final update

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logging.error(f"Error in Gradio interface: {error_message}", exc_info=True) # Log full traceback
        # Return error message to status and None for file path
        yield f"{status_message}\n\n-------------------\nERROR:\n{error_message}\n-------------------", None


# --- Define Gradio Components (Inputs Modified) ---
input_title = gr.Textbox(label="Book Title", placeholder="Enter the title of the book")
input_description = gr.Textbox(label="Book Description", lines=5, placeholder="Describe the book's content and purpose (language will be detected from this)")
input_style = gr.Textbox(label="Writing Style", placeholder="e.g., Academic, Narrative, Technical, Humorous")
# REMOVED: input_language
# REMOVED: input_chapters
# REMOVED: input_subsections
input_filetype = gr.Dropdown(["PDF", "TXT", "DOCX"], label="Save as", value="PDF")

# --- Define Gradio Outputs (Unchanged) ---
output_status = gr.Textbox(label="Status / Log", lines=10, interactive=False)
output_file = gr.File(label="Download Generated Book")

# --- Create the Gradio Interface (Inputs List Modified) ---
iface = gr.Interface(
    fn=generate_book_interface,
    inputs=[
        input_title,
        input_description,
        input_style,
        # Removed language, chapters, subsections
        input_filetype
    ],
    outputs=[
        output_status,
        output_file
    ],
    title="AI Book Generator (Auto Language/Structure)",
    description="Enter details to generate a book using OpenAI. Language and chapter/subsection structure are determined automatically by the AI.",
    flagging_mode="never", # Use updated parameter
)

# --- Launch the Interface ---
if __name__ == "__main__":
    print(f"Generated books will be saved in: {os.path.abspath(OUTPUT_DIR)}")
    print("--- About to call iface.launch() ---")
    try:
        iface.launch()
    except Exception as e:
        print(f"--- Error during iface.launch(): {e} ---")
        traceback.print_exc() # Print full traceback if launch fails
    print("--- iface.launch() has finished (server stopped) ---")
