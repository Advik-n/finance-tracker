"""
OCR Parser for Scanned Bank Statements

Provides OCR-based text extraction for scanned PDFs and images
using Tesseract OCR with image preprocessing for better accuracy.
"""

import io
import re
import logging
from typing import Optional, List, Tuple
import tempfile

logger = logging.getLogger(__name__)


class OCRParser:
    """
    OCR fallback for scanned PDFs and images.
    
    Uses Tesseract OCR with image preprocessing for improved accuracy.
    Supports:
    - Scanned PDF documents
    - Image files (PNG, JPEG, TIFF)
    - Multi-page documents
    """
    
    def __init__(self, tesseract_cmd: str = None, language: str = 'eng'):
        """
        Initialize the OCR parser.
        
        Args:
            tesseract_cmd: Path to tesseract executable (auto-detected if None)
            language: OCR language code (default: 'eng' for English)
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.language = language
        self.tesseract_cmd = tesseract_cmd
        
        # Configure tesseract if path provided
        if tesseract_cmd:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            except ImportError:
                self.logger.warning("pytesseract not installed")
    
    def extract_text(self, image_bytes: bytes) -> str:
        """
        Extract text from an image using Tesseract OCR.
        
        Args:
            image_bytes: Raw image bytes (PNG, JPEG, etc.)
            
        Returns:
            Extracted text string
        """
        try:
            import pytesseract
            from PIL import Image
            import numpy as np
        except ImportError as e:
            self.logger.error(f"OCR dependencies not installed: {e}")
            raise ImportError(
                "OCR requires: pip install pytesseract pillow numpy opencv-python"
            )
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to numpy array for preprocessing
            img_array = np.array(image)
            
            # Preprocess image
            processed = self.preprocess_image(img_array)
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(processed)
            
            # Run OCR with optimized config
            config = self._get_tesseract_config()
            text = pytesseract.image_to_string(
                processed_image,
                lang=self.language,
                config=config
            )
            
            return text
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def extract_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extract text from a scanned PDF using OCR.
        
        Args:
            pdf_bytes: Raw PDF bytes
            
        Returns:
            Extracted text from all pages
        """
        try:
            from pdf2image import convert_from_bytes
        except ImportError:
            self.logger.error("pdf2image not installed")
            raise ImportError("PDF OCR requires: pip install pdf2image")
        
        text_parts = []
        
        try:
            # Convert PDF pages to images
            images = convert_from_bytes(
                pdf_bytes,
                dpi=300,  # Higher DPI for better OCR
                fmt='png'
            )
            
            self.logger.info(f"Processing {len(images)} pages with OCR")
            
            for i, image in enumerate(images):
                self.logger.debug(f"Processing page {i + 1}/{len(images)}")
                
                # Convert PIL Image to bytes
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG')
                img_bytes = img_buffer.getvalue()
                
                # Extract text from page
                page_text = self.extract_text(img_bytes)
                if page_text:
                    text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
            
            return '\n\n'.join(text_parts)
            
        except Exception as e:
            self.logger.error(f"PDF OCR failed: {e}")
            return ""
    
    def preprocess_image(self, image: 'np.ndarray') -> 'np.ndarray':
        """
        Preprocess image for better OCR accuracy.
        
        Operations:
        - Convert to grayscale
        - Deskew (correct rotation)
        - Binarization (Otsu's method)
        - Noise removal
        - Contrast enhancement
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image as numpy array
        """
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.logger.warning("OpenCV not installed, skipping preprocessing")
            return image
        
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()
            
            # Deskew
            gray = self._deskew(gray)
            
            # Noise removal
            gray = self._remove_noise(gray)
            
            # Binarization using Otsu's method
            gray = self._binarize(gray)
            
            # Contrast enhancement
            gray = self._enhance_contrast(gray)
            
            return gray
            
        except Exception as e:
            self.logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    def _deskew(self, image: 'np.ndarray') -> 'np.ndarray':
        """
        Correct image skew/rotation.
        
        Args:
            image: Grayscale image
            
        Returns:
            Deskewed image
        """
        import cv2
        import numpy as np
        
        try:
            # Find edges
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Find lines using Hough transform
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi / 180,
                threshold=100,
                minLineLength=100,
                maxLineGap=10
            )
            
            if lines is None or len(lines) == 0:
                return image
            
            # Calculate average angle
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                # Only consider near-horizontal lines
                if abs(angle) < 30:
                    angles.append(angle)
            
            if not angles:
                return image
            
            median_angle = np.median(angles)
            
            # Skip if angle is very small
            if abs(median_angle) < 0.5:
                return image
            
            # Rotate image
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(
                image,
                rotation_matrix,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            return rotated
            
        except Exception as e:
            self.logger.warning(f"Deskew failed: {e}")
            return image
    
    def _remove_noise(self, image: 'np.ndarray') -> 'np.ndarray':
        """
        Remove noise from image.
        
        Args:
            image: Grayscale image
            
        Returns:
            Denoised image
        """
        import cv2
        
        try:
            # Apply bilateral filter (preserves edges while removing noise)
            denoised = cv2.bilateralFilter(image, 9, 75, 75)
            
            # Apply median blur for salt-and-pepper noise
            denoised = cv2.medianBlur(denoised, 3)
            
            return denoised
            
        except Exception as e:
            self.logger.warning(f"Noise removal failed: {e}")
            return image
    
    def _binarize(self, image: 'np.ndarray') -> 'np.ndarray':
        """
        Convert image to binary using adaptive thresholding.
        
        Args:
            image: Grayscale image
            
        Returns:
            Binarized image
        """
        import cv2
        
        try:
            # Use Otsu's binarization
            _, binary = cv2.threshold(
                image,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            
            return binary
            
        except Exception as e:
            self.logger.warning(f"Binarization failed: {e}")
            return image
    
    def _enhance_contrast(self, image: 'np.ndarray') -> 'np.ndarray':
        """
        Enhance image contrast using CLAHE.
        
        Args:
            image: Grayscale image
            
        Returns:
            Contrast-enhanced image
        """
        import cv2
        
        try:
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
            
            return enhanced
            
        except Exception as e:
            self.logger.warning(f"Contrast enhancement failed: {e}")
            return image
    
    def _get_tesseract_config(self) -> str:
        """
        Get optimized Tesseract configuration.
        
        Returns:
            Tesseract config string
        """
        config_parts = [
            '--oem 3',  # Use LSTM OCR engine
            '--psm 6',  # Assume uniform block of text
            '-c preserve_interword_spaces=1',  # Preserve spaces
        ]
        
        return ' '.join(config_parts)
    
    def extract_tables(self, image_bytes: bytes) -> List[List[List[str]]]:
        """
        Extract tables from an image using OCR with table detection.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            List of tables, each table is a list of rows, each row is a list of cells
        """
        try:
            import pytesseract
            from PIL import Image
            import numpy as np
        except ImportError:
            self.logger.error("OCR dependencies not installed")
            return []
        
        try:
            # Load and preprocess image
            image = Image.open(io.BytesIO(image_bytes))
            img_array = np.array(image)
            processed = self.preprocess_image(img_array)
            processed_image = Image.fromarray(processed)
            
            # Get OCR data with bounding boxes
            data = pytesseract.image_to_data(
                processed_image,
                lang=self.language,
                output_type=pytesseract.Output.DICT
            )
            
            # Group text by lines (same top coordinate within threshold)
            lines = self._group_into_lines(data)
            
            # Convert lines to table format
            tables = [lines]  # Simple: treat entire output as one table
            
            return tables
            
        except Exception as e:
            self.logger.error(f"Table extraction failed: {e}")
            return []
    
    def _group_into_lines(self, ocr_data: dict) -> List[List[str]]:
        """
        Group OCR output into lines based on vertical position.
        
        Args:
            ocr_data: Tesseract output dictionary
            
        Returns:
            List of lines, each line is a list of words
        """
        # Extract words with their positions
        words = []
        for i, text in enumerate(ocr_data['text']):
            if text.strip():
                words.append({
                    'text': text,
                    'top': ocr_data['top'][i],
                    'left': ocr_data['left'][i],
                    'height': ocr_data['height'][i],
                })
        
        if not words:
            return []
        
        # Sort by top position
        words.sort(key=lambda w: (w['top'], w['left']))
        
        # Group into lines (words with similar top position)
        lines = []
        current_line = []
        current_top = None
        threshold = 10  # pixels
        
        for word in words:
            if current_top is None:
                current_top = word['top']
                current_line = [word]
            elif abs(word['top'] - current_top) <= threshold:
                current_line.append(word)
            else:
                # Sort current line by left position and add
                current_line.sort(key=lambda w: w['left'])
                lines.append([w['text'] for w in current_line])
                current_line = [word]
                current_top = word['top']
        
        # Don't forget last line
        if current_line:
            current_line.sort(key=lambda w: w['left'])
            lines.append([w['text'] for w in current_line])
        
        return lines


def check_ocr_dependencies() -> Tuple[bool, List[str]]:
    """
    Check if OCR dependencies are installed.
    
    Returns:
        Tuple of (all_installed, list_of_missing_packages)
    """
    missing = []
    
    try:
        import pytesseract
    except ImportError:
        missing.append('pytesseract')
    
    try:
        from PIL import Image
    except ImportError:
        missing.append('pillow')
    
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
    
    try:
        import cv2
    except ImportError:
        missing.append('opencv-python')
    
    try:
        from pdf2image import convert_from_bytes
    except ImportError:
        missing.append('pdf2image')
    
    return len(missing) == 0, missing
