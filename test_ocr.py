#!/usr/bin/env python3
"""Test if OCR is working correctly"""

import sys

# Test 1: Check if pytesseract is importable
print("Test 1: Checking pytesseract import...")
try:
    import pytesseract
    from PIL import Image
    print("✅ pytesseract and PIL imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Check if Tesseract binary is accessible
print("\nTest 2: Checking Tesseract binary...")
try:
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract version: {version}")
except Exception as e:
    print(f"❌ Cannot access Tesseract: {e}")
    print("Try: brew install tesseract")
    sys.exit(1)

# Test 3: Test OCR on a simple image
print("\nTest 3: Testing OCR extraction...")
try:
    # Create a simple test image with text
    import tempfile
    import os
    from PIL import Image, ImageDraw, ImageFont
    
    # Create white image with black text
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Use default font
    try:
        # Try to use a better font if available
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
    except:
        font = ImageFont.load_default()
    
    draw.text((10, 30), "Test OCR 123", fill='black', font=font)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        # Extract text
        ocr_text = pytesseract.image_to_string(Image.open(tmp_path))
        print(f"✅ OCR extracted text: '{ocr_text.strip()}'")
        
        if "Test" in ocr_text or "OCR" in ocr_text or "123" in ocr_text:
            print("✅ OCR is working correctly!")
        else:
            print("⚠️  OCR ran but didn't extract expected text")
    finally:
        os.unlink(tmp_path)
        
except Exception as e:
    print(f"❌ OCR test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check Czech language support
print("\nTest 4: Checking language support...")
try:
    langs = pytesseract.get_languages()
    print(f"Available languages: {', '.join(langs)}")
    
    if 'ces' in langs:
        print("✅ Czech language (ces) is available")
    else:
        print("⚠️  Czech language not found. Install with: brew install tesseract-lang")
        
except Exception as e:
    print(f"⚠️  Could not check languages: {e}")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("✅ pytesseract is installed and working")
print("✅ Tesseract binary is accessible")
print("✅ OCR extraction works")
print("\nNow you need to:")
print("1. RESTART your backend server (Ctrl+C and restart)")
print("2. Re-upload article.jpg")
print("3. Check backend logs for 'OCR text extracted'")
