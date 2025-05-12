from typing import Optional
from pathlib import Path
import PyPDF2
from docx import Document
from src.core.custom_logger import CustomLogger

class TextExtractor:
    """A class to extract text from PDF and DOCX files with proper error handling."""

    def __init__(self, logger: Optional[CustomLogger] = None):
        """
        Initialize TextExtractor with a custom logger.
        
        Args:
            logger (Optional[CustomLogger]): Custom logger instance
        """
        self.logger = logger or CustomLogger("TextExtractor")

    def extract_from_pdf(self, file_path: str | Path) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_path (str | Path): Path to the PDF file
            
        Returns:
            str: Extracted text content
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"PDF file not found: {file_path}")

            self.logger.info(f"Extracting text from PDF: {file_path}")
            text_content = []

            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())

            extracted_text = ' '.join(text_content)
            self.logger.debug(f"Successfully extracted {len(extracted_text)} characters from PDF")
            return extracted_text

        except PyPDF2.errors.PdfReadError as e:
            self.logger.error(f"Error reading PDF file: {e}")
            raise ValueError(f"Invalid PDF file: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error while processing PDF: {e}")
            raise

    def extract_from_docx(self, file_path: str | Path) -> str:
        """
        Extract text from a DOCX file.
        
        Args:
            file_path (str | Path): Path to the DOCX file
            
        Returns:
            str: Extracted text content
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not a valid DOCX
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"DOCX file not found: {file_path}")

            self.logger.info(f"Extracting text from DOCX: {file_path}")
            doc = Document(file_path)
            text_content = []

            for paragraph in doc.paragraphs:
                text_content.append(paragraph.text)

            extracted_text = ' '.join(text_content)
            self.logger.debug(f"Successfully extracted {len(extracted_text)} characters from DOCX")
            return extracted_text

        except Exception as e:
            self.logger.error(f"Error processing DOCX file: {e}")
            raise ValueError(f"Invalid DOCX file or processing error: {e}")

    def extract_text(self, file_path: str | Path) -> str:
        """
        Extract text from either PDF or DOCX file based on file extension.
        
        Args:
            file_path (str | Path): Path to the file
            
        Returns:
            str: Extracted text content
            
        Raises:
            ValueError: If the file format is not supported
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()

        if file_extension == '.pdf':
            return self.extract_from_pdf(file_path)
        elif file_extension == '.docx':
            return self.extract_from_docx(file_path)
        else:
            error_msg = f"Unsupported file format: {file_extension}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
def test_text_extractor(resume_path: str | Path):
    """
    Test the TextExtractor class with a sample PDF and DOCX file.
    """
    logger = CustomLogger("TextExtractor")
    text_extractor = TextExtractor(logger=logger)
    try:
        extracted_text = text_extractor.extract_text(resume_path)
        logger.info("Text extraction completed successfully.")  
        return extracted_text  # Print the extracted text
    except Exception as e:
        logger.error(f"Failed to extract text: {e}")
        return None          
