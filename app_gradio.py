# app_gradio.py (Fix for ValueError: not enough output values)

import gradio as gr
from book_openai import BookOpenAI # Assuming book_openai.py is correct
from dotenv import load_dotenv
from pathlib import Path
import os
import time
import traceback
import logging

# --- Setup ---
load_dotenv()
OUTPUT_DIR = "generated_books"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define overall progress ranges for generation
INIT_END = 0.05
CHAPTERS_END = 0.15
SUBSECTIONS_END = 0.40
CONTENT_END = 0.95
GENERATION_COMPLETE = 1.0


# --- Generation Function (Corrected Yields) ---
def generate_book_content(
    book_title,
    book_description,
    writing_style,
    progress=gr.Progress(track_tqdm=True) # Gradio progress tracking
):
    """
    Generates the book content and yields updates for the 4 output components.
    """
    status_message = "Starting generation process...\n"
    book_generator = None
    # Default UI updates (hide buttons, hide download link)
    save_row_update = gr.update(visible=False)
    dl_link_update = gr.update(value=None, visible=False)

    # --- Input Validation ---
    if not all([book_title, book_description, writing_style]):
        status_message = "Error: Please fill in Title, Description, and Writing Style."
        # Return 4 values for the 4 outputs
        return status_message, save_row_update, dl_link_update, None

    try:
        # --- Step 1: Initialize Generator ---
        progress(0, desc="Initializing Generator...")
        status_message += "Initializing generator...\n"
        # Yield 4 values
        yield status_message, save_row_update, dl_link_update, None
        book_generator = BookOpenAI()
        if not book_generator.client:
             raise ConnectionError("Failed to initialize OpenAI client (Check API Key?).")
        progress(INIT_END, desc="Generator Initialized.")
        status_message += "Generator initialized.\n"
        # Yield 4 values
        yield status_message, save_row_update, dl_link_update, None

        # --- Step 2: Generate Chapters ---
        progress(INIT_END, desc="Generating Chapters Outline...")
        status_message += "Generating chapters (detecting language internally)...\n"
        # Yield 4 values
        yield status_message, save_row_update, dl_link_update, None
        chapters_data = book_generator.generate_chapters(
            book_title, book_description, writing_style
        )
        if chapters_data is None:
            status_message += "Error: Failed to generate chapters (check logs).\n"
            # Yield 4 values on error
            yield status_message, save_row_update, dl_link_update, None
            return # Stop generation
        total_chapters = len(chapters_data)
        progress(CHAPTERS_END, desc=f"Outline Generated ({total_chapters} Chapters)")
        status_message += f"Language '{book_generator.target_language}' used. Outline: {total_chapters} chapters.\n"
        # Yield 4 values
        yield status_message, save_row_update, dl_link_update, None

        # --- Step 3: Generate Subsections (with Progress Callback) ---
        status_message += "Generating subsections for each chapter...\n"
        # Yield 4 values
        yield status_message, save_row_update, dl_link_update, None
        def update_subsection_progress(current_chapter_idx, total_chapters_cb):
            overall_fraction = CHAPTERS_END + ((current_chapter_idx + 1) / total_chapters_cb) * (SUBSECTIONS_END - CHAPTERS_END)
            desc = f"Generating Subsections: Ch {current_chapter_idx + 1}/{total_chapters_cb}"
            progress(overall_fraction, desc=desc)

        book_generator.generate_subsections(chapters_data, progress_callback=update_subsection_progress)
        progress(SUBSECTIONS_END, desc="Subsections Generated.")
        status_message += "Subsections generated.\n"
        # Yield 4 values
        yield status_message, save_row_update, dl_link_update, None

        # --- Step 4: Generate Content (with Progress Callback) ---
        status_message += "Generating content (this may take a while)...\n"
        # Yield 4 values
        yield status_message, save_row_update, dl_link_update, None
        try: total_subsections = sum(len(data.get("subsections", {})) for data in book_generator.chapters.values())
        except Exception: total_subsections = 0
        def update_content_progress(proc_count, total_count, ch_idx, tot_ch, sub_idx, tot_sub_in_ch):
            if total_count > 0: overall_fraction = SUBSECTIONS_END + (proc_count / total_count) * (CONTENT_END - SUBSECTIONS_END)
            else: overall_fraction = CONTENT_END
            desc = f"Content: Ch {ch_idx+1}/{tot_ch}, Sub {sub_idx+1}/{tot_sub_in_ch} ({proc_count}/{total_count})"
            progress(overall_fraction, desc=desc)

        if total_subsections > 0: book_generator.generate_content(progress_callback=update_content_progress)
        else: status_message += "Skipping content generation: No subsections found.\n"

        progress(CONTENT_END, desc="Content Generation Complete.")
        status_message += "Content generation complete.\n"
        status_message += "\n>>> Select a format below to save the book. <<<"
        # Yield 4 values - Keep buttons hidden until the *final* yield/return
        yield status_message, save_row_update, dl_link_update, None

        # --- Generation Finished ---
        progress(GENERATION_COMPLETE, desc="Generation Ready!")
        # Final yield: Update status, SHOW save buttons, keep download link hidden, return generator state
        yield status_message, gr.update(visible=True), dl_link_update, book_generator

    except Exception as e:
        error_message = f"Generation Error: {str(e)}\n{traceback.format_exc()}"
        logging.error(f"Error during generation: {error_message}", exc_info=True)
        progress(1.0, desc="Generation Failed")
        # Yield 4 values on general error
        yield f"{status_message}\n\nERROR:\n{error_message}", gr.update(visible=False), gr.update(value=None, visible=False), None


# --- Save Action Function (Same as before) ---
def save_book_file(generator_state, format_type):
    """Saves the book from the state object in the specified format."""
    if generator_state is None:
        return "Error: No generated book content found. Please generate first.", gr.update(value=None, visible=False) # Return 2 values for outputs

    book_generator = generator_state
    status_message = f"Saving as {format_type}...\n"
    output_file_path = None

    try:
        # Create filename
        if not book_generator.title: safe_title = "Untitled_Book"
        else: safe_title = "".join(c for c in book_generator.title if c.isalnum() or c in (' ', '_')).rstrip().replace(" ", "_")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        lang = book_generator.target_language if book_generator.target_language else "unk"
        base_filename = f"{safe_title}_{lang}_{timestamp}"
        file_extensions = { "PDF": ".pdf", "TXT": ".txt", "DOCX": ".docx" }
        extension = file_extensions.get(format_type, ".txt")
        output_file_path = os.path.join(OUTPUT_DIR, f"{base_filename}{extension}")
        logging.info(f"Attempting to save to: {output_file_path}")

        # Call save method
        if format_type == "PDF": book_generator.save_as_pdf(output_file_path)
        elif format_type == "TXT": book_generator.save_as_txt(output_file_path)
        elif format_type == "DOCX": book_generator.save_as_docx(output_file_path)
        else: raise ValueError(f"Unsupported format type: {format_type}")

        status_message += f"Book saved successfully: {output_file_path}"
        logging.info(f"Save successful: {output_file_path}")
        # Return status update and visible download link
        return status_message, gr.update(value=output_file_path, visible=True) # Return 2 values for outputs

    except Exception as e:
        error_message = f"Save Error ({format_type}): {str(e)}\n{traceback.format_exc()}"
        logging.error(f"Error saving file as {format_type}: {error_message}", exc_info=True)
        # Return error status and hide download link
        return f"{status_message}\n\nERROR:\n{error_message}", gr.update(value=None, visible=False) # Return 2 values for outputs


# --- Build Gradio Interface (Same as before) ---
with gr.Blocks() as iface:
    gr.Markdown("# AI Book Generator (Auto Language/Structure)")
    gr.Markdown("Enter details, generate the book content, then choose format(s) to save.")

    generator_state = gr.State(value=None) # Holds BookOpenAI object

    with gr.Row():
        with gr.Column(scale=1):
            input_title = gr.Textbox(label="Book Title", placeholder="Enter the title")
            input_description = gr.Textbox(label="Book Description", lines=5, placeholder="Describe the book (language detected from this)")
            input_style = gr.Textbox(label="Writing Style", placeholder="e.g., Academic, Narrative, Technical")
            btn_generate = gr.Button("1. Generate Book Content", variant="primary")
        with gr.Column(scale=1):
            output_status = gr.Textbox(label="Status / Log", lines=10, interactive=False)
            with gr.Row(visible=False) as save_options_row:
                 gr.Markdown("2. Save Generated Content As:")
                 btn_save_pdf = gr.Button("PDF")
                 btn_save_txt = gr.Button("TXT")
                 btn_save_docx = gr.Button("DOCX")
            output_dl_link = gr.File(label="Download Last Saved Book", visible=False)

    # --- Connect Generate Button ---
    btn_generate.click(
        fn=generate_book_content,
        inputs=[input_title, input_description, input_style],
        # Outputs MUST match the number of yielded/returned values in ALL paths
        outputs=[output_status, save_options_row, output_dl_link, generator_state]
    )

    # --- Connect Save Buttons ---
    # These expect 2 return values from save_book_file for the 2 outputs
    btn_save_pdf.click(
        fn=save_book_file,
        inputs=[generator_state, gr.Textbox("PDF", visible=False)],
        outputs=[output_status, output_dl_link]
    )
    btn_save_txt.click(
        fn=save_book_file,
        inputs=[generator_state, gr.Textbox("TXT", visible=False)],
        outputs=[output_status, output_dl_link]
    )
    btn_save_docx.click(
        fn=save_book_file,
        inputs=[generator_state, gr.Textbox("DOCX", visible=False)],
        outputs=[output_status, output_dl_link]
    )

# --- Launch the Interface (Same as before) ---
if __name__ == "__main__":
    print(f"Generated books will be saved in: {os.path.abspath(OUTPUT_DIR)}")
    print("--- Launching Gradio Interface ---")
    try:
        iface.launch()
    except Exception as e:
        print(f"--- Error during iface.launch(): {e} ---")
        traceback.print_exc()
    print("--- Gradio interface stopped ---")
