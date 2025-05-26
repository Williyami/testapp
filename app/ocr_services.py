# app/ocr_services.py
import os
import random
from datetime import datetime, timedelta

def extract_text_from_receipt(filepath):
    """
    Placeholder for OCR processing.
    Simulates extracting data from a receipt file.
    In a real scenario, this would use an OCR library (e.g., Tesseract, Google Cloud Vision AI).
    """
    if not os.path.exists(filepath):
        return {"error": "File not found for OCR"}

    # Simulate OCR extraction - return mock data
    filename = os.path.basename(filepath)
    
    # Mock data based on filename or just random for variety
    mock_data = {
        "ocr_vendor": f"MockVendor_{filename.split('.')[0]}",
        "ocr_amount": round(random.uniform(5.0, 500.0), 2),
        "ocr_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
        "ocr_currency": random.choice(["USD", "EUR", "GBP"]),
        "full_text": f"This is simulated OCR text for {filename}. Content would be here."
    }
    
    # Simulate a small chance of OCR failure or partial data
    if random.random() < 0.1:
        mock_data["ocr_status"] = "PARTIAL_FAILURE"
        mock_data.pop("ocr_amount", None) # Remove some data
    else:
        mock_data["ocr_status"] = "SUCCESS"
        
    return mock_data
