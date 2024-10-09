import logging
from book_openai import BookOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Initialize the BookOpenAI instance
    book_generator = BookOpenAI(model_name="gpt-4o-mini", target_language="english")

    # Define book details
    title = "The Future of AI"
    description = "Exploring the potential of artificial intelligence in various fields."
    writing_style = "Conversational"
    n_chapters = 2

    # Generate chapters
    chapters = book_generator.generate_chapters(title, description, writing_style, n_chapters)
    logging.info(f"Generated Chapters: {chapters}")

    # Generate subsections for each chapter
    book_generator.generate_subsections(chapters)

    # Generate content for each subsection
    book_generator.generate_content()

    # Save the generated book as a PDF
    pdf_filename = "The_Future_of_AI.pdf"
    book_generator.save_as_pdf(pdf_filename)

if __name__ == "__main__":
    main()

