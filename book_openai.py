# book_openai.py
from docx import Document
from dotenv import load_dotenv
import logging
from openai import OpenAI
import os
from pathlib import Path
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
import time

# Load environment variables
load_dotenv(Path("./api_key.env"))
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define data models
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
        self.target_language = target_language.lower() if target_language else "english"  # Ensure lowercase

    def translate(self, prompt, source_language="english", target=None):
        """
        Translate text from source_language to target language.

        Args:
            prompt (str): The text to translate.
            source_language (str): The language of the input text.
            target (str): The language to translate to. If None, uses self.target_language.

        Returns:
            str: Translated text.
        """
        target = target or self.target_language
        if target == source_language.lower():
            return prompt  # No translation needed

        translate_prompt = f"Translate from {source_language} to {target}: '{prompt}'."

        messages = [
            {"role": "system", "content": "You are a translator assistant."},
            {"role": "user", "content": translate_prompt}
        ]

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model_name,
                temperature=1,
                messages=messages,
                response_format=Translation,
            )
            translation = completion.choices[0].message.parsed.translation
            return translation
        except Exception as e:
            logging.error(f"Translation failed: {e}")
            return prompt  # Fallback to original prompt if translation fails

    def generate_chapters(self, title, description, writing_style, n_chapters):
        """
        Generate chapters for the book based on the title and description.

        Args:
            title (str): The title of the book.
            description (str): The description of the book.
            writing_style (str): The writing style to use.
            n_chapters (int): The number of chapters to generate.
        """
        logging.info("Starting chapter generation...")
        self.title = title
        self.description = description
        self.writing_style = writing_style

        self.messages = []  # Clear previous messages

        start_time = time.time()

        # Loop until the exact number of chapters is generated
        chapters = []
        max_retries = 5  # Set a maximum number of retries to prevent infinite loops
        retries = 0
        while len(chapters) != n_chapters and retries < max_retries:
            retries += 1
            system_message = f"Generate {n_chapters} chapter titles using the book title and description."
            user_prompt = f"Book Title: '{title}'\nDescription: '{description}'"

            # Translate prompts if necessary
            if self.target_language != "english":
                system_message = self.translate(system_message, source_language="english")
                user_prompt = self.translate(user_prompt, source_language="english")

            completion = self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=Chapters,
            )

            chapters = completion.choices[0].message.parsed.chapters
            if len(chapters) != n_chapters:
                logging.warning(f"Expected {n_chapters} chapters, but got {len(chapters)}. Retrying...")

        if len(chapters) != n_chapters:
            logging.error(f"Failed to generate exactly {n_chapters} chapters after {max_retries} retries.")
            # Handle the error as needed, e.g., raise an exception or accept the closest result
            # For this example, we'll accept the closest result
        else:
            logging.info(f"Chapters generated in {time.time() - start_time:.2f} seconds")

        logging.debug(f"Chapters: {chapters}")

        # Store chapters and their descriptions
        for chapter in chapters:
            self.chapters[chapter.title] = {"description": chapter.description, "subsections": {}}
        self.messages.append({"role": "assistant", "content": " ".join([chapter.title for chapter in chapters])})

        return chapters


    def generate_subsections(self, chapters, n_subsections=3):
        """
        Generate subsections for each chapter.

        Args:
            chapters (list): A list of chapter titles.
            n_subsections (int): The number of subsections to generate for each chapter.
        """
        for chapter in chapters:
            logging.info(f"Generating subsections for chapter: {chapter.title}")
            start_time = time.time()

            self.messages = []  # Clear previous messages for subsections
            subsections = []
            max_retries = 5  # Set a maximum number of retries
            retries = 0
            
            while len(subsections) != n_subsections and retries < max_retries:
                retries += 1
                system_message = f"Generate {n_subsections} subsections for chapter titled '{chapter.title}'."
                user_prompt = f"Chapter Title: {chapter.title}\nChapter Description: {self.chapters[chapter.title]['description']}"

                # Translate prompts if necessary
                if self.target_language != "english":
                    system_message = self.translate(system_message, source_language="english")
                    user_prompt = self.translate(user_prompt, source_language="english")

                completion = self.client.beta.chat.completions.parse(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format=Subsections,
                )

                subsections = completion.choices[0].message.parsed.subsections

                if len(subsections) != n_subsections:
                    logging.warning(f"Expected {n_subsections} subsections, but got {len(subsections)}. Retrying...")

            if len(subsections) != n_subsections:
                logging.error(f"Failed to generate exactly {n_subsections} subsections for chapter '{chapter.title}' after {max_retries} retries.")
                # You may choose to raise an error or handle this case as needed.

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
            book_structure += f"Chapter: {chapter_title}\n"
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
                subsection_prompt =     f"""\
                                        Book Title: '{self.title}'
                                        Book Description: '{self.description}'
                                        Current Chapter Title: '{chapter_title}'   
                                        Current Chapter Description: '{chapter_description}'
                                        Current Subsection Title: '{subsection_title}'
                                        Current Subsection Description: '{subsection_description}'
                                        Writing style: '{self.writing_style}'\
                                        """

                # Translate prompts if necessary
                if self.target_language != "english":
                    subsection_prompt = self.translate(subsection_prompt, source_language="english")

                # Prepare messages including all previous messages and the book structure
                context_messages = self.messages.copy()  # Start with all previous messages

                # Add the book structure to the context
                context_messages.append(structure_message)

                # Add the system message and user prompt for the current subsection
                system_message = "Given the information and the book structure, generate the content for the Current Subsection. Return only the subsection content."
                if self.target_language != "english":
                    system_message = self.translate(system_message, source_language="english")
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
                    if len(context_messages) > 4:
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



    def save_as_pdf(self, filename):
        """
        Save the generated book as a PDF file with proper text wrapping and pagination.

        Args:
            filename (str): The name of the PDF file to save.
        """
        logging.info(f"Saving book as PDF: {filename}")
        start_time = time.time()
        
        # Create a SimpleDocTemplate for easier handling of flowables
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Title Style - Centered
        styles.add(ParagraphStyle(
            name='TitleCentered',
            parent=styles['Title'],
            alignment=TA_CENTER,
            spaceAfter=24
        ))
        
        # TOC Header - Left aligned (no longer using the word "Index")
        styles.add(ParagraphStyle(
            name='TOCHeader',
            parent=styles['Heading1'],
            alignment=TA_LEFT,
            spaceAfter=12
        ))
        
        # Chapter Title Style - Centered
        styles.add(ParagraphStyle(
            name='ChapterTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            spaceBefore=12,
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Subsection Title Style - Left aligned
        styles.add(ParagraphStyle(
            name='SubsectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=6,
            alignment=TA_LEFT  # Change to TA_CENTER if you prefer centered subsections
        ))
        
        # Content Style - Justified
        styles.add(ParagraphStyle(
            name='Content',
            parent=styles['BodyText'],
            fontSize=12,
            leading=15,
            spaceAfter=12,
            alignment=TA_JUSTIFY
        ))
        
        # Create a Table of Contents
        toc = TableOfContents()
        toc.levelStyles = [
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
        
        # Container for the PDF elements
        elements = []
        
        # Add Book Title
        elements.append(Paragraph(self.title, styles['TitleCentered']))
        elements.append(Spacer(1, 12))
        
        # Add Table of Contents Header
        elements.append(Paragraph("Table of Contents", styles['TOCHeader']))
        elements.append(Spacer(1, 12))
        
        # Add the Table of Contents
        elements.append(toc)
        elements.append(PageBreak())
        
        # Define a callback function to capture TOC entries
        def after_flowable(flowable):
            """
            Callback function to add entries to the TOC after each flowable is processed.
            """
            if isinstance(flowable, Paragraph):
                text = flowable.getPlainText()
                style = flowable.style.name
                if style == 'ChapterTitle':
                    # Level 0 for chapters
                    toc.addEntry(0, text, doc.canv.getPageNumber())
                elif style == 'SubsectionTitle':
                    # Level 1 for subsections
                    toc.addEntry(1, text, doc.canv.getPageNumber())
        
        # Assign the after_flowable callback to the DocTemplate instance
        doc.afterFlowable = after_flowable
        
        # Add chapters and subsections
        for chapter_title, chapter_data in self.chapters.items():
            # Add chapter title
            chapter_para = Paragraph(chapter_title, styles['ChapterTitle'])
            elements.append(chapter_para)
            elements.append(Spacer(1, 12))
            
            for subsection_title, subsection_data in chapter_data["subsections"].items():
                # Add subsection title
                subsection_para = Paragraph(subsection_title, styles['SubsectionTitle'])
                elements.append(subsection_para)
                elements.append(Spacer(1, 6))
                
                # Add subsection content
                content = subsection_data['content'].replace('\n', '<br/>')  # Preserve line breaks
                content_para = Paragraph(content, styles['Content'])
                elements.append(content_para)
                elements.append(Spacer(1, 12))
            
            # Add a page break after each chapter
            elements.append(PageBreak())
        
        # Define the page numbering callback
        def add_page_number(canvas_obj, doc_obj):
            """Add page number to the footer of each page, centered at the bottom."""
            canvas_obj.saveState()
            page_number_text = f"{doc_obj.page}"
            canvas_obj.setFont('Helvetica', 10)
            page_width = letter[0]  # Width of the page
            canvas_obj.drawCentredString(page_width / 2.0, 0.5 * inch, page_number_text)
            canvas_obj.restoreState()
        
        # Assign the page numbering callback
        doc.build(
            elements,
            onFirstPage=add_page_number,
            onLaterPages=add_page_number
        )
        
        logging.info(f"PDF saved successfully as {filename} in {time.time() - start_time:.2f} seconds")
