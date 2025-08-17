"""
QR Code Scanner Utility for EasyJet Tool Inventory System
Handles QR code detection and decoding from images and live camera feed
"""
import cv2
import numpy as np
from pyzbar import pyzbar
from PIL import Image
import logging
from typing import List, Tuple, Optional
import qrcode
import io

class QRCodeScanner:
    """QR code scanner and generator for tool inventory"""
    
    def __init__(self):
        self.qr_detector = cv2.QRCodeDetector()
        
    def decode_qr_codes(self, image: np.ndarray) -> List[str]:
        """
        Decode QR codes from an image
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of decoded QR code data strings
        """
        try:
            qr_codes = []
            
            # Method 1: Using pyzbar
            barcodes = pyzbar.decode(image)
            for barcode in barcodes:
                if barcode.type == 'QRCODE':
                    qr_data = barcode.data.decode('utf-8')
                    qr_codes.append(qr_data)
                    logging.info(f"QR code detected (pyzbar): {qr_data}")
            
            # Method 2: Using OpenCV QR detector (fallback)
            if not qr_codes:
                data, bbox, _ = self.qr_detector.detectAndDecode(image)
                if data:
                    qr_codes.append(data)
                    logging.info(f"QR code detected (OpenCV): {data}")
            
            return qr_codes
            
        except Exception as e:
            logging.error(f"Error decoding QR codes: {e}")
            return []
    
    def decode_from_file(self, image_path: str) -> List[str]:
        """
        Decode QR codes from an image file
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of decoded QR code data strings
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                logging.error(f"Could not load image from {image_path}")
                return []
            
            return self.decode_qr_codes(image)
            
        except Exception as e:
            logging.error(f"Error decoding QR code from file: {e}")
            return []
    
    def decode_from_pil_image(self, pil_image: Image.Image) -> List[str]:
        """
        Decode QR codes from a PIL Image
        
        Args:
            pil_image: PIL Image object
            
        Returns:
            List of decoded QR code data strings
        """
        try:
            # Convert PIL Image to OpenCV format
            image_array = np.array(pil_image)
            
            # Convert RGB to BGR if needed
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            return self.decode_qr_codes(image_array)
            
        except Exception as e:
            logging.error(f"Error decoding QR code from PIL image: {e}")
            return []
    
    def generate_qr_code(self, data: str, size: int = 10, border: int = 4) -> Image.Image:
        """
        Generate QR code for given data
        
        Args:
            data: Data to encode in QR code
            size: Size of QR code boxes
            border: Border size around QR code
            
        Returns:
            PIL Image of the QR code
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            logging.info(f"QR code generated for data: {data}")
            
            return qr_image
            
        except Exception as e:
            logging.error(f"Error generating QR code: {e}")
            return None
    
    def generate_tool_qr_code(self, tool_code: str, tool_name: str = "", 
                             size: int = 10, border: int = 4) -> Tuple[Image.Image, str]:
        """
        Generate QR code specifically for tool inventory
        
        Args:
            tool_code: Unique tool code
            tool_name: Optional tool name for labeling
            size: Size of QR code boxes
            border: Border size around QR code
            
        Returns:
            Tuple of (QR code PIL Image, QR code data)
        """
        try:
            # QR code data format for tools
            qr_data = tool_code
            
            qr_image = self.generate_qr_code(qr_data, size, border)
            
            return qr_image, qr_data
            
        except Exception as e:
            logging.error(f"Error generating tool QR code: {e}")
            return None, ""
    
    def generate_batch_qr_codes(self, tool_data: List[dict], 
                               output_dir: str = "qr_codes/") -> dict:
        """
        Generate QR codes for multiple tools
        
        Args:
            tool_data: List of dictionaries containing tool information
            output_dir: Directory to save QR code images
            
        Returns:
            Dictionary with results of QR code generation
        """
        try:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            results = {
                'success': [],
                'failed': [],
                'total': len(tool_data)
            }
            
            for tool in tool_data:
                tool_code = tool.get('tool_code', '')
                tool_name = tool.get('tool_name', '')
                
                if not tool_code:
                    results['failed'].append({'tool': tool, 'error': 'Missing tool_code'})
                    continue
                
                try:
                    qr_image, qr_data = self.generate_tool_qr_code(tool_code, tool_name)
                    
                    if qr_image:
                        # Save QR code image
                        filename = f"{tool_code.replace('/', '_').replace(' ', '_')}_qr.png"
                        filepath = os.path.join(output_dir, filename)
                        qr_image.save(filepath)
                        
                        results['success'].append({
                            'tool_code': tool_code,
                            'tool_name': tool_name,
                            'qr_data': qr_data,
                            'filepath': filepath
                        })
                        
                    else:
                        results['failed'].append({'tool': tool, 'error': 'QR generation failed'})
                        
                except Exception as e:
                    results['failed'].append({'tool': tool, 'error': str(e)})
            
            logging.info(f"Batch QR generation completed: {len(results['success'])} success, {len(results['failed'])} failed")
            return results
            
        except Exception as e:
            logging.error(f"Error in batch QR code generation: {e}")
            return {'success': [], 'failed': [], 'total': 0, 'error': str(e)}
    
    def enhance_image_for_qr_detection(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image quality for better QR code detection
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Enhanced image as numpy array
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply various enhancement techniques
            enhanced_images = []
            
            # Original grayscale
            enhanced_images.append(gray)
            
            # Gaussian blur removal (sharpen)
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(gray, -1, kernel)
            enhanced_images.append(sharpened)
            
            # Histogram equalization
            equalized = cv2.equalizeHist(gray)
            enhanced_images.append(equalized)
            
            # Adaptive threshold
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, 11, 2)
            enhanced_images.append(adaptive)
            
            # Try QR detection on each enhanced version
            for enhanced in enhanced_images:
                qr_codes = self.decode_qr_codes(enhanced)
                if qr_codes:
                    return enhanced
            
            # Return original if no QR codes found in any version
            return gray
            
        except Exception as e:
            logging.error(f"Error enhancing image: {e}")
            return image
    
    def detect_qr_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect potential QR code regions in an image
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of bounding boxes (x, y, width, height) for potential QR regions
        """
        try:
            regions = []
            
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Use pyzbar to detect potential QR regions
            barcodes = pyzbar.decode(gray)
            for barcode in barcodes:
                if barcode.type == 'QRCODE':
                    # Get bounding box
                    x = min([point[0] for point in barcode.polygon])
                    y = min([point[1] for point in barcode.polygon])
                    w = max([point[0] for point in barcode.polygon]) - x
                    h = max([point[1] for point in barcode.polygon]) - y
                    regions.append((x, y, w, h))
            
            return regions
            
        except Exception as e:
            logging.error(f"Error detecting QR regions: {e}")
            return []
    
    def validate_tool_qr_code(self, qr_data: str) -> bool:
        """
        Validate if QR code data represents a valid tool code
        
        Args:
            qr_data: Decoded QR code data
            
        Returns:
            True if valid tool code format, False otherwise
        """
        try:
            # Tool code validation rules
            if not qr_data or len(qr_data.strip()) == 0:
                return False
            
            # Check length (typically 3-20 characters)
            if len(qr_data) < 3 or len(qr_data) > 20:
                return False
            
            # Check for basic alphanumeric pattern (adjust as needed)
            import re
            pattern = r'^[A-Z0-9\-_]+$'
            if not re.match(pattern, qr_data.upper()):
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error validating QR code: {e}")
            return False
    
    def create_qr_code_with_logo(self, data: str, logo_path: Optional[str] = None, 
                                size: int = 10, border: int = 4) -> Image.Image:
        """
        Create QR code with optional logo overlay
        
        Args:
            data: Data to encode
            logo_path: Optional path to logo image
            size: QR code size
            border: Border size
            
        Returns:
            PIL Image with QR code and logo
        """
        try:
            # Generate basic QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for logo
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Add logo if provided
            if logo_path and os.path.exists(logo_path):
                logo = Image.open(logo_path)
                
                # Calculate logo size (10% of QR code)
                qr_width, qr_height = qr_image.size
                logo_size = min(qr_width, qr_height) // 10
                
                # Resize logo
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # Calculate position (center)
                logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
                
                # Paste logo onto QR code
                if logo.mode != 'RGBA':
                    logo = logo.convert('RGBA')
                qr_image.paste(logo, logo_pos, logo)
            
            return qr_image
            
        except Exception as e:
            logging.error(f"Error creating QR code with logo: {e}")
            return self.generate_qr_code(data, size, border)

# Additional utility functions
def create_qr_code_label(tool_data: dict, qr_image: Image.Image) -> Image.Image:
    """
    Create a labeled QR code with tool information
    
    Args:
        tool_data: Dictionary containing tool information
        qr_image: QR code image
        
    Returns:
        PIL Image with QR code and label
    """
    try:
        from PIL import ImageDraw, ImageFont
        
        # Create a larger canvas for the label
        canvas_width = max(qr_image.width, 300)
        canvas_height = qr_image.height + 100  # Extra space for text
        
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        
        # Paste QR code centered horizontally
        qr_x = (canvas_width - qr_image.width) // 2
        canvas.paste(qr_image, (qr_x, 10))
        
        # Add text labels
        draw = ImageDraw.Draw(canvas)
        
        try:
            # Try to use a nice font
            font_large = ImageFont.truetype("arial.ttf", 16)
            font_small = ImageFont.truetype("arial.ttf", 12)
        except (OSError, IOError):
            # Fall back to default font
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Tool information
        tool_code = tool_data.get('tool_code', 'Unknown')
        tool_name = tool_data.get('tool_name', 'Unknown Tool')
        category = tool_data.get('category', 'Unknown Category')
        
        # Draw text
        text_y = qr_image.height + 20
        
        # Tool code (large)
        text_width = draw.textlength(tool_code, font=font_large)
        text_x = (canvas_width - text_width) // 2
        draw.text((text_x, text_y), tool_code, fill='black', font=font_large)
        
        # Tool name
        text_y += 25
        text_width = draw.textlength(tool_name, font=font_small)
        text_x = (canvas_width - text_width) // 2
        draw.text((text_x, text_y), tool_name, fill='black', font=font_small)
        
        # Category
        text_y += 20
        text_width = draw.textlength(category, font=font_small)
        text_x = (canvas_width - text_width) // 2
        draw.text((text_x, text_y), category, fill='gray', font=font_small)
        
        return canvas
        
    except Exception as e:
        logging.error(f"Error creating QR code label: {e}")
        return qr_image