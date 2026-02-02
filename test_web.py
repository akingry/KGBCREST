"""Test the book cipher encoding/decoding with various compression levels."""

import os
import http.server
import socketserver
import threading
import time
from PIL import Image
from book_cipher import encode_image, decode_image, BookCipher

# Test settings
STRENGTH = 150
RS_SYMBOLS = 64
REPETITION = 7

# Create a simple test source text
TEST_SOURCE = """The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs. 
How vexingly quick daft zebras jump! The five boxing wizards jump quickly.
Sphinx of black quartz, judge my vow. Two driven jocks help fax my big quiz.
The jay, pig, fox, zebra and my wolves quack! Sympathizing would fix Quaker objectives.
A wizard's job is to vex chumps quickly in fog. Watch Jeopardy, Alex Trebek's fun TV quiz game.
""" * 20  # Repeat to make it longer

def create_test_source():
    """Create a test source text file."""
    source_path = "test_source.txt"
    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(TEST_SOURCE)
    return source_path

def test_encode_decode(image_path, message, source_path):
    """Test encoding and decoding with various compression levels."""
    print(f"\n{'='*60}")
    print(f"Testing: {image_path}")
    print(f"Message: {message[:50]}{'...' if len(message) > 50 else ''}")
    print(f"{'='*60}")
    
    # Get image info
    img = Image.open(image_path)
    w, h = img.size
    print(f"Image size: {w}x{h}")
    
    # Encode
    encoded_path = f"test_encoded_{os.path.basename(image_path).split('.')[0]}.png"
    print(f"\nEncoding...")
    
    try:
        encode_image(
            image_path, message, encoded_path,
            strength=STRENGTH, rs_symbols=RS_SYMBOLS, repetition=REPETITION,
            source_path=source_path
        )
    except Exception as e:
        print(f"✗ Encoding failed: {e}")
        return False
    
    # Test decoding at various quality levels
    print(f"\nTesting compression survival:")
    print("-" * 40)
    
    results = []
    img_encoded = Image.open(encoded_path)
    
    # PNG (lossless)
    try:
        decoded = decode_image(
            encoded_path, strength=STRENGTH, rs_symbols=RS_SYMBOLS, 
            repetition=REPETITION, source_path=source_path
        )
        match = decoded == message
        results.append(("PNG lossless", match))
        print(f"  PNG lossless:  {'✓ PASS' if match else '✗ FAIL'}")
        if not match:
            print(f"    Expected: {message[:30]}...")
            print(f"    Got:      {decoded[:30]}...")
    except Exception as e:
        results.append(("PNG lossless", False))
        print(f"  PNG lossless:  ✗ FAIL - {e}")
    
    # JPEG at various qualities
    for quality in [90, 80, 70, 60, 55, 50]:
        jpg_path = f"test_q{quality}.jpg"
        img_encoded.save(jpg_path, "JPEG", quality=quality)
        
        try:
            decoded = decode_image(
                jpg_path, strength=STRENGTH, rs_symbols=RS_SYMBOLS,
                repetition=REPETITION, source_path=source_path
            )
            match = decoded == message
            size_kb = os.path.getsize(jpg_path) // 1024
            results.append((f"JPEG q{quality}", match))
            print(f"  JPEG q{quality}:      {'✓ PASS' if match else '✗ FAIL'} ({size_kb}KB)")
        except Exception as e:
            results.append((f"JPEG q{quality}", False))
            print(f"  JPEG q{quality}:      ✗ FAIL - {str(e)[:40]}")
        
        os.remove(jpg_path)
    
    # WebP lossless
    webp_path = "test_lossless.webp"
    img_encoded.save(webp_path, "WEBP", lossless=True)
    try:
        decoded = decode_image(
            webp_path, strength=STRENGTH, rs_symbols=RS_SYMBOLS,
            repetition=REPETITION, source_path=source_path
        )
        match = decoded == message
        results.append(("WebP lossless", match))
        print(f"  WebP lossless: {'✓ PASS' if match else '✗ FAIL'}")
    except Exception as e:
        results.append(("WebP lossless", False))
        print(f"  WebP lossless: ✗ FAIL - {e}")
    os.remove(webp_path)
    
    # Cleanup
    os.remove(encoded_path)
    
    passed = sum(1 for r in results if r[1])
    print(f"\nResult: {passed}/{len(results)} tests passed")
    
    return passed >= 5  # Pass if at least PNG + JPEG 60-90 work


def main():
    print("=" * 60)
    print("BOOK CIPHER STEGANOGRAPHY - COMPRESSION TESTS")
    print("=" * 60)
    
    # Create test source
    source_path = create_test_source()
    print(f"Created test source: {len(TEST_SOURCE)} characters")
    
    # Test messages
    short_msg = "Hello world!"
    medium_msg = "The quick brown fox jumps over the lazy dog."
    
    all_passed = True
    
    # Test fossil2.png (small image)
    if os.path.exists("fossil2.png"):
        if not test_encode_decode("fossil2.png", short_msg, source_path):
            all_passed = False
    else:
        print("\n⚠ fossil2.png not found")
    
    # Test forest.webp (large image)
    if os.path.exists("forest.webp"):
        if not test_encode_decode("forest.webp", medium_msg, source_path):
            all_passed = False
    else:
        print("\n⚠ forest.webp not found")
    
    # Cleanup
    os.remove(source_path)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60)


if __name__ == "__main__":
    main()
