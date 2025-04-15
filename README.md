# AI Book Generator (Auto Language/Structure)

This application provides a web interface using Gradio to automatically generate book content using OpenAI's GPT models.

The workflow is designed to generate the full book content first, and then allow the user to save the generated content in multiple formats (PDF, TXT, DOCX) without re-running the generation process.

Based on a user-provided title, description, and writing style, the application:

1.  **Generates Content:**
    * Detects the **language** from the input description.
    * Determines an appropriate **chapter and subsection structure** using AI.
    * Generates **chapter titles**, **subsection titles**, and the **full content** for each subsection.
    * Provides detailed progress updates during generation.
2.  **Saves Content:**
    * After generation, presents options to save the completed book.
    * Allows saving in **PDF**, **TXT**, and **DOCX** formats.
    * PDF output includes an automatically generated Table of Contents and page numbering.

## Features

* **Simple Web Interface:** Easy-to-use UI built with Gradio.
* **AI-Powered Generation:** Leverages OpenAI for content creation.
* **Automatic Language Detection:** Determines the book's language from the input description.
* **AI-Driven Structure:** The AI decides the optimal chapter and subsection structure.
* **Two-Step Workflow:** Generate content first, then save in desired formats.
* **Multiple Output Formats:** Save the *same* generated content as PDF, TXT, or DOCX.
* **Detailed Progress:** Real-time status updates and progress bar during the generation phase.
* **PDF Enhancements:** Automatic Table of Contents and page numbering in PDF output.
* **Local Storage:** All saved books are stored locally in the `generated_books/` directory.
* **Error Handling:** Displays errors encountered during generation or saving in the status log.

## Prerequisites

* **Python 3.9+** (due to dependencies like Gradio and OpenAI library features)
* **OpenAI API Key:** You need an active API key from OpenAI with sufficient credits/quota.

## Installation

1.  **Clone the repository or download the files:**
    Make sure you have `app_gradio.py`, `book_openai.py`, and `LICENSE` in the same directory.

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows: venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```

3.  **Install Dependencies:**
    With your virtual environment activated, install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If you encounter issues, you might need specific versions of these libraries. Check the libraries' documentation if needed.)*

4.  **Configure Environment Variables:**
    Create a file named `.env` in the root project directory (same level as `app_gradio.py`). Add your OpenAI API key to this file:
    ```env
    # .env
    OPENAI_API_KEY='YOUR_OPENAI_API_KEY_HERE'
    ```
    The `book_openai.py` script is configured to load the key from this file.

## Usage

1.  **Run the Gradio Application:**
    Open your terminal, navigate to the project directory (`LLM_book_writer-main`), activate your virtual environment, and run:
    ```bash
    python app_gradio.py
    ```

2.  **Access the Web Interface:**
    The script will output a local URL (usually `http://127.0.0.1:7860` or similar). Open this URL in your web browser.

3.  **Enter Book Details:**
    * **Book Title:** Enter the desired title.
    * **Book Description:** Provide a detailed description. The language used here will be automatically detected.
    * **Writing Style:** Specify the desired style (e.g., "Academic", "Narrative", "Technical", "Humorous").

4.  **Generate Content:**
    * Click the **"1. Generate Book Content"** button.
    * Monitor the generation progress via the progress bar and the "Status / Log" text area. This step can take a significant amount of time depending on the book's complexity and API response times.

5.  **Save Generated Content:**
    * Once the status log shows "Generation Ready!" and "Select a format below...", the save buttons will appear.
    * Click the **"PDF"**, **"TXT"**, or **"DOCX"** button to save the generated content in that specific format.
    * Each save action will update the status log and provide a download link for the *last saved file* in the "Download Last Saved Book" section. You can click multiple save buttons.

6.  **Find Saved Files:**
    All generated files (regardless of format) are saved locally in the `generated_books/` directory within the project folder. Filenames include the title, language code, and a timestamp corresponding to the *save time*.

