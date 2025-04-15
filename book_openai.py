# book_openai.py
from docx import Document
from dotenv import load_dotenv
import logging
from openai import OpenAI
import os
from pathlib import Path
from pathlib import Path
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import time
import re
import time
import re
from pydantic import BaseModel

# Load environment variables - This is usually sufficient
# Ensure './api_key.env' exists and contains OPENAI_API_KEY='...'
load_dotenv(dotenv_path=Path("./.env"), verbose=True) # Added verbose=True for debugging


# Check if the key was loaded (optional debug)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logging.error("ERROR: OPENAI_API_KEY not found in environment after loading .env file.")
    # You might want to raise an exception or exit here if the key is absolutely required
    # raise ValueError("OPENAI_API_KEY not found. Please check your ./api_key.env file.")
else:
    logging.info("OpenAI API Key loaded successfully.") # Confirmation
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define data models

class Language(BaseModel):
    language: str

class Translation(BaseModel):
    translation: str

class Chapter(BaseModel):
    title: str
    description: str

class Chapters(BaseModel):
    chapters: list[Chapter]

class Subsection(BaseModel):
    title: str
    description: str

class Subsections(BaseModel):
    subsections: list[Subsection]

class SubsectionContent(BaseModel):
    content: str

# Content Cleaning Function
def clean_content(content):
    """
    Remove lines starting with '###' and empty lines from the content.
    
    Args:
        content (str): The raw content string.
    
    Returns:
        str: The cleaned content string.
    """
    # Remove lines starting with '###'
    content = re.sub(r'^###.*$', '', content, flags=re.MULTILINE)
    
    # Remove empty lines
    content = re.sub(r'\n\s*\n', '\n', content)
    
    # Strip leading/trailing whitespace
    content = content.strip()
    
    return content

# Helper Function to Strip 'Chapter N:' Prefix
def strip_chapter_prefix(chapter_title):
    """
    Remove the 'Chapter N:' prefix from a chapter title.

    Args:
        chapter_title (str): The original chapter title.

    Returns:
        str: The cleaned chapter title without the prefix.
    """
    return re.sub(r'^Chapter\s+\d+:\s*', '', chapter_title, flags=re.IGNORECASE)

# Page Numbering Function
def add_page_number(canvas_obj, doc_obj):
    """Add page number to the footer of each page, centered at the bottom."""
    canvas_obj.saveState()
    page_number_text = f"{doc_obj.page}"
    canvas_obj.setFont('Helvetica', 10)
    page_width = letter[0]  # Width of the page
    canvas_obj.drawCentredString(page_width / 2.0, 0.5 * inch, page_number_text)
    canvas_obj.restoreState()

# Custom DocTemplate with Page Numbering
class MyDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        frame = Frame(
            x1=72,                     # 1-inch margin from the left
            y1=72,                     # 1-inch margin from the bottom
            width=612 - 72*2,          # Page width minus left and right margins
            height=792 - 72*2,         # Page height minus top and bottom margins
            id='F1'
        )
        template = PageTemplate('normal', [frame])
        self.addPageTemplates(template)
        self.toc = TableOfContents()
        self.toc.levelStyles = [
            ParagraphStyle(
                fontName='Helvetica-Bold',
                fontSize=14,
                name='TOCHeading1',
                leftIndent=20,
                firstLineIndent=-20,
                spaceBefore=5,
                leading=16
            ),
            ParagraphStyle(
                fontName='Helvetica',
                fontSize=12,
                name='TOCHeading2',
                leftIndent=40,
                firstLineIndent=-20,
                spaceBefore=0,
                leading=12
            ),
        ]

    def afterFlowable(self, flowable):
        """
        Registers TOC entries.
        """
        if isinstance(flowable, Paragraph):
            text = flowable.getPlainText()
            style = flowable.style.name
            if style == 'ChapterTitle':
                self.notify('TOCEntry', (0, text, self.page))
            elif style == 'SubsectionTitle':
                self.notify('TOCEntry', (1, text, self.page))

    def handle_pageBegin(self):
        super().handle_pageBegin()
        add_page_number(self.canv, self)

class BookOpenAI:
    def __init__(self, model_name="gpt-4o-mini", target_language="english"):
        """
        Initialize the BookOpenAI instance.

        Args:
            model_name (str): The name of the OpenAI model to use.
            target_language (str): The language to generate the book in. Defaults to 'english'.
        """
        self.model_name = model_name
        self.client = OpenAI()
        self.messages = []
        self.chapters = {}
        self.title = ""
        self.description = ""
        self.writing_style = ""
        
    def extract_n_chapters(self, text):
        """
        Extract the number of chapters from the text.

        Args:
            text (str): The text from which to extract the number of chapters.

        Returns:
            int: The extracted number of chapters.
        """
        prompt = f"Extract the number of chapters from the following text: '{text}'"
        messages = [
            {"role": "system", "content": "You are a chapter extraction assistant."},
            {"role": "user", "content": prompt}
        ]

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model_name,
                temperature=1,
                messages=messages,
                response_format=Chapters,
            )
            n_chapters = completion.choices[0].message.parsed.chapters
            logging.info(f"Extracted number of chapters: {n_chapters}")
            return n_chapters
        except Exception as e:
            logging.error(f"Chapter extraction failed: {e}")
            return None
    def extract_language(self, text):


        prompt = f"Extract the language from the following text: '{text}'"
        messages = [
            {"role": "system", "content": "You are a language extraction assistant."},
            {"role": "user", "content": prompt}
        ]


        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model_name,
                temperature=1,
                messages=messages,
                response_format=Language,
            )
            language = completion.choices[0].message.parsed.language
            logging.info(f"Extracted language: {language}")
            return language
        except Exception as e:
            logging.error(f"Language extraction failed: {e}")
            return None

    def generate_chapters(self, title, description, writing_style):
        """
        Generate chapters for the book based on the title and description.

        Args:
            title (str): The title of the book.
            description (str): The description of the book.
            writing_style (str): The writing style to use.
        """
        logging.info("Starting chapter generation...")
        self.title = title
        self.description = description

        self.target_language = self.extract_language(description) or self.extract_language(title)
        if not self.target_language:
            logging.error("Failed to extract language from title or description.")
            return None

        self.writing_style = writing_style

        self.messages = []  # Clear previous messages

        start_time = time.time()

        # Ask the model to generate all necessary chapters
        system_message = f"Generate chapter titles using the book title and description in the following language: '{self.target_language}'."
        user_prompt = f"Book Title: '{title}'\nDescription: '{description}'"

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=Chapters,
            )

            chapters = completion.choices[0].message.parsed.chapters
            logging.info(f"Chapters generated in {time.time() - start_time:.2f} seconds")

        except Exception as e:
            logging.error(f"Failed to generate chapters: {e}")
            return None

        logging.debug(f"Chapters: {chapters}")

        # Store chapters and their descriptions
        for chapter in chapters:
            self.chapters[chapter.title] = {"description": chapter.description, "subsections": {}}
        self.messages.append({"role": "assistant", "content": " ".join([chapter.title for chapter in chapters])})

        return chapters

    def generate_subsections(self, chapters):
        """
        Generate all necessary subsections for each chapter.

        Args:
            chapters (list): A list of chapter titles.
        """
        for chapter in chapters:
            logging.info(f"Generating subsections for chapter: {chapter.title}")
            start_time = time.time()

            self.messages = []  # Clear previous messages for subsections
            subsections = []

            system_message = f"Generate subsections for the chapter titled '{chapter.title}' in the following language: '{self.target_language}'."
            user_prompt = f"Chapter Title: {chapter.title}\nChapter Description: {self.chapters[chapter.title]['description']}"

            try:
                completion = self.client.beta.chat.completions.parse(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format=Subsections,
                )

                subsections = completion.choices[0].message.parsed.subsections

            except Exception as e:
                logging.error(f"Failed to generate subsections for chapter '{chapter.title}': {e}")
                continue

            end_time = time.time()
            logging.info(f"Subsections for chapter '{chapter.title}' generated in {end_time - start_time:.2f} seconds")

            for subsection in subsections:
                self.chapters[chapter.title]["subsections"][subsection.title] = {"description": subsection.description}

            logging.info(f"Subsections generated for chapter: {chapter.title}")

        logging.info("All subsections have been generated.")
        return chapters

    def generate_content(self):
        """
        Generate content for each subsection in each chapter, making it context-aware by including previous messages and chapters.
        """
        logging.info("Starting content generation...")
        start_time = time.time()

        # Prepare a summary of the book's structure to include in the context
        book_structure = ""
        for chapter_title, chapter_data in self.chapters.items():
            book_structure += f"{chapter_title}\n"
            for subsection_title in chapter_data["subsections"]:
                book_structure += f"  Subsection: {subsection_title}\n"

        # Split the book structure into manageable chunks if necessary
        max_structure_length = 1000  # Adjust based on token limits
        if len(book_structure) > max_structure_length:
            book_structure = book_structure[-max_structure_length:]  # Keep the last part

        # Include the book structure as a system message
        structure_message = {"role": "system", "content": "Here is the current book structure:\n" + book_structure}

        for chapter_title, chapter_data in self.chapters.items():
            chapter_description = chapter_data["description"]
            logging.info(f"Starting chapter '{chapter_title}' generation...")
            for subsection_title, subsection_data in chapter_data["subsections"].items():
                logging.info(f"Starting generation of subsection '{subsection_title}' from chapter '{chapter_title}'s ...")
                subsection_description = subsection_data["description"]

                # Build the current prompt
                subsection_prompt = f"""\
Book Title: '{self.title}'
Book Description: '{self.description}'
Current Chapter Title: '{chapter_title}'   
Current Chapter Description: '{chapter_description}'
Current Subsection Title: '{subsection_title}'
Current Subsection Description: '{subsection_description}'
Writing style: '{self.writing_style}'\
"""


                # Prepare messages including all previous messages and the book structure
                context_messages = self.messages.copy()  # Start with all previous messages

                # Add the book structure to the context
                context_messages.append(structure_message)

                # Add the system message and user prompt for the current subsection
                system_message = f"Given the information and the book structure, generate the content in the following language: '{self.target_language}' for the Current Subsection. Return only the subsection content."

                context_messages.append({"role": "system", "content": system_message})
                context_messages.append({"role": "user", "content": subsection_prompt})

                # Manage token limits
                max_tokens = 128000  
                while True:
                    # Estimate the total tokens
                    total_tokens = sum(len(msg['content'].split()) for msg in context_messages)
                    if total_tokens <= max_tokens:
                        break
                    # Remove the oldest message if over the limit
                    elif len(context_messages) > 4:
                        context_messages.pop(0)
                    else:
                        # Can't remove more messages; break to avoid infinite loop
                        break

                # Make the API call with the context messages
                try:
                    completion = self.client.beta.chat.completions.parse(
                        model=self.model_name,
                        messages=context_messages,
                        response_format=SubsectionContent,
                    )

                    subsection_content = completion.choices[0].message.parsed.content

                    self.chapters[chapter_title]["subsections"][subsection_title]["content"] = subsection_content
                    self.messages.append({"role": "assistant", "content": subsection_content})

                except Exception as e:
                    logging.error(f"Failed to generate content for subsection '{subsection_title}': {e}")
                    self.chapters[chapter_title]["subsections"][subsection_title]["content"] = "Content generation failed."

        end_time = time.time()
        logging.info(f"Content generation completed in {end_time - start_time:.2f} seconds")


    def save_as_txt(self, filename):
        logging.info(f"Saving book as TXT: {filename}")
        full_content = f"Book Title: {self.title}\n\n"
        for i, (chapter_title, chapter_data) in enumerate(self.chapters.items()):
            cleaned_chapter_title = strip_chapter_prefix(chapter_title) # Use your helper
            full_content += f"--- Chapter {i+1}: {cleaned_chapter_title} ---\n\n"
            for sub_title, sub_data in chapter_data.get("subsections", {}).items():
                full_content += f"--- Subsection: {sub_title} ---\n"
                content = sub_data.get('content', 'Content not generated.')
                cleaned_content = clean_content(content) # Use your helper
                full_content += f"{cleaned_content}\n\n"
            full_content += "\n"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(full_content)
            logging.info("TXT file saved successfully.")
        except Exception as e:
            logging.error(f"Error saving TXT file: {e}")
            raise # Re-raise the exception

    def save_as_docx(self, filename):
        from docx import Document # Import inside method or at top
        from docx.shared import Inches

        logging.info(f"Saving book as DOCX: {filename}")
        document = Document()
        document.add_heading(self.title, level=0) # Book Title

        for i, (chapter_title, chapter_data) in enumerate(self.chapters.items()):
            cleaned_chapter_title = strip_chapter_prefix(chapter_title) # Use your helper
            document.add_heading(f"Chapter {i+1}: {cleaned_chapter_title}", level=1) # Chapter Title

            for sub_title, sub_data in chapter_data.get("subsections", {}).items():
                document.add_heading(sub_title, level=2) # Subsection Title
                content = sub_data.get('content', 'Content not generated.')
                cleaned_content = clean_content(content) # Use your helper
                document.add_paragraph(cleaned_content) # Add content

            # Add a page break after each chapter except the last
            if i < len(self.chapters) - 1:
                document.add_page_break()

        try:
            document.save(filename)
            logging.info("DOCX file saved successfully.")
        except Exception as e:
            logging.error(f"Error saving DOCX file: {e}")
            raise # Re-raise the exception

    def save_as_pdf(self, filename):
        """
        Save the generated book as a PDF file with a dynamic Table of Contents
        and support for **bold** text. # <--- Updated docstring

        Args:
            filename (str): The name of the PDF file to save.
        """
        logging.info(f"Saving book as PDF: {filename}")
        if not self.chapters:
             logging.error("Cannot save PDF: No chapters generated.")
             raise ValueError("No chapters generated to save.")

        start_time = time.time()
        doc = MyDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()

        # --- Add your custom ParagraphStyles here (TitleCentered, TOCHeader, etc.) ---
        # (Keep the style definitions as they were)
        # Title Style - Centered
        styles.add(ParagraphStyle(
            name='TitleCentered', parent=styles['Title'], alignment=TA_CENTER, spaceAfter=24
        ))
        # TOC Header - Left aligned
        styles.add(ParagraphStyle(
            name='TOCHeader', parent=styles['Heading1'], alignment=TA_LEFT, spaceAfter=12
        ))
        # Chapter Title Style - Centered
        styles.add(ParagraphStyle(
            name='ChapterTitle', parent=styles['Heading1'], fontSize=18, leading=22,
            spaceBefore=12, spaceAfter=12, alignment=TA_CENTER
        ))
        # Subsection Title Style - Center aligned
        styles.add(ParagraphStyle(
            name='SubsectionTitle', parent=styles['Heading2'], fontSize=14, leading=18,
            spaceBefore=12, spaceAfter=6, alignment=TA_CENTER
        ))
        # Content Style - Justified
        styles.add(ParagraphStyle(
            name='Content', parent=styles['BodyText'], fontSize=12, leading=15,
            spaceAfter=12, alignment=TA_JUSTIFY
        ))
        # --- End Style Definitions ---

        story = []
        story.append(Paragraph(self.title, styles['TitleCentered']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Table of Contents", styles['TOCHeader'])) # Changed empty "" to actual text
        story.append(doc.toc)
        story.append(PageBreak())

        first_chapter = True
        for chapter_title_key, chapter_data in self.chapters.items():
            if not first_chapter:
                story.append(PageBreak())
            else:
                first_chapter = False

            cleaned_chapter_title = strip_chapter_prefix(chapter_title_key)
            chapter_para = Paragraph(cleaned_chapter_title, styles['ChapterTitle'])
            story.append(chapter_para)
            story.append(Spacer(1, 12))

            if not chapter_data.get("subsections"):
                story.append(Paragraph("(No subsections generated for this chapter)", styles['Content']))
                continue

            # --- Process Subsections ---
            for subsection_title_key, subsection_data in chapter_data["subsections"].items():
                # Add subsection title
                subsection_para = Paragraph(subsection_title_key, styles['SubsectionTitle'])
                story.append(subsection_para)
                story.append(Spacer(1, 6))

                # Get raw content safely
                raw_content = subsection_data.get('content', 'Content not generated.')

                # Clean basic unwanted lines (optional, depends if clean_content is needed)
                cleaned_content = clean_content(raw_content) # Apply your existing cleaning

                # --- Convert **markdown bold** to <b>reportlab bold</b> ---
                formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_content, flags=re.DOTALL)
                # Using DOTALL flag just in case bold text spans multiple lines, though less common

                # Replace Python newlines with ReportLab <br/> tags AFTER bold conversion
                content_for_pdf = formatted_content.replace('\n', '<br/>')

                # Create the ReportLab Paragraph object
                content_para = Paragraph(content_for_pdf, styles['Content'])
                story.append(content_para)
                story.append(Spacer(1, 12))
            # --- End Subsection Loop ---

        # Build the PDF
        try:
            doc.multiBuild(story)
            logging.info(f"PDF saved successfully in {time.time() - start_time:.2f} seconds.")
        except Exception as e: # Catch generic Exception for build errors
            logging.error(f"Error during PDF build: {e}")
            raise # Re-raise the exception

