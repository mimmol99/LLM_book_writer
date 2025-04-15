# AI Book Generator (Auto Language/Structure)

This application provides a web interface using Gradio to generate books automatically using OpenAI API.

Based on a user-provided title, description, and writing style, the AI:
1.  **Detects the language** of the intended book from the description.
2.  **Determines an appropriate number of chapters and subsections** for the topic.
3.  Generates the **chapter titles**, **subsection titles**, and the **full content** for each subsection.
4.  Saves the complete book in the user's chosen format.

## Features

* **Simple Web Interface:** Easy-to-use UI built with Gradio.
* **AI-Powered Generation:** Leverages OpenAI for content creation.
* **Automatic Language Detection:** Determines the book's language based on the input description.
* **AI-Driven Structure:** The AI decides the optimal number of chapters and subsections.
* **User Inputs:** Requires only Book Title, Description, and desired Writing Style.
* **Multiple Output Formats:** Save the generated book as PDF, TXT, or DOCX.
* **Local Storage:** Generated books are saved in the `generated_books/` directory.
* **Progress Tracking:** Real-time status updates and progress bar during generation.
* **Error Handling:** Displays errors encountered during the generation process.

## Prerequisites

* **Python 3.8+**
* **OpenAI API Key:** You need an API key from OpenAI to use the underlying OpenAI model.
* **Required Python Libraries:** (See Installation)

## Installation

1.  **Clone the repository or download the files:**
    Make sure you have `app_gradio.py` and the corresponding `book_openai.py` (which contains the `BookOpenAI` class logic) in the same directory.

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    Create a `requirements.txt` file with the following content (you might need to adjust based on the *exact* needs of `book_openai.py`, especially for PDF/DOCX saving):
    ```txt
    gradio
    openai # Assuming book_openai.py uses this
    python-dotenv
    # Add libraries potentially used by book_openai.py for saving:
    reportlab # Likely needed for PDF generation
    python-docx # Likely needed for DOCX generation
    # Add any other dependencies required by book_openai.py
    ```
    Then install them:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a file named `.env` in the same directory as `app_gradio.py`. Add your OpenAI API key to this file:
    ```env
    # .env
    OPENAI_API_KEY='your_openai_api_key_here'
    ```

## Usage

1.  **Run the Gradio Application:**
    Open your terminal, navigate to the directory containing the files, and run:
    ```bash
    python app_gradio.py
    ```

2.  **Access the Web Interface:**
    The script will output a URL (usually `http://127.0.0.1:7860` or similar). Open this URL in your web browser.

3.  **Fill in the Details:**
    * **Book Title:** Enter the desired title for your book.
    * **Book Description:** Provide a detailed description of the book's content and purpose. The language used here will be detected and used for generation.
    * **Writing Style:** Specify the style (e.g., "Academic", "Narrative", "Technical", "Humorous", "Informative and concise").
    * **Save as:** Select the desired output file format (PDF, TXT, or DOCX) from the dropdown.

4.  **Generate the Book:**
    Click the "Submit" button.

5.  **Monitor Progress:**
    The "Status / Log" box will show updates on the generation process (Initializing, Generating Chapters, Generating Subsections, Generating Content, Saving). A progress bar will also indicate the overall progress.

6.  **Download the Book:**
    Once generation is complete, a success message will appear in the status box, and a download link for the generated file will appear in the "Download Generated Book" section.

7.  **Find Saved Files:**
    A copy of the generated book will also be saved locally in the `generated_books/` directory within the application's folder. The filename includes the title, detected language, and a timestamp (e.g., `My_Awesome_Book_en_20240515_103000.pdf`).

