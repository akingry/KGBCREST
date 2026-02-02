# StegoTool

A steganography tool that hides secret messages in images using a **book cipher** combined with **DCT watermarking**. Messages survive JPEG compression down to quality 60.

## Quick Start

**Double-click `run.bat`** — this starts the server and opens your browser to the tool.

Or manually:
```bash
python server.py
```
Then open http://localhost:8080

## How It Works

### The Book Cipher

Messages are encoded using character positions in a shared source text file (`source_text.txt`). Each character is found in the source text, and its **relative position** from the previous character is recorded.

**Example:** Encoding "The"
- Find `'T'` at position 325 → record: **325** (first character, absolute)
- Find `'h'` at position 225 → record: **-100** (100 characters backwards)
- Find `'e'` at position 228 → record: **+3** (3 characters forwards)

Result: `[325, -100, +3]`

The cipher always finds the **nearest occurrence** of each character (forward or backward), minimizing the numbers stored.

### Encoding Pipeline

```
Message
    ↓
┌─────────────────┐
│   BOOK CIPHER   │  Characters → relative positions in source text
└─────────────────┘
    ↓
┌─────────────────┐
│   COMPRESSION   │  zlib compresses the position data (40-60% reduction)
└─────────────────┘
    ↓
┌─────────────────┐
│  REED-SOLOMON   │  Adds 64 parity symbols for error recovery
└─────────────────┘
    ↓
┌─────────────────┐
│   REPETITION    │  Each bit repeated 7× (majority vote recovery)
└─────────────────┘
    ↓
┌─────────────────┐
│ DCT WATERMARK   │  Embedded in frequency domain coefficients
└─────────────────┘
    ↓
Encoded Image
```

### DCT Watermarking

The data is embedded in the **Discrete Cosine Transform** coefficients of the image — the same domain JPEG compression uses. This is why encoded images survive JPEG compression.

- One bit embedded per 8×8 pixel block
- Uses mid-frequency coefficient at position (4,3)
- Quantization Index Modulation (QIM) for robust embedding
- Strength setting: 150 (tuned for JPEG Q60 survival)

## Capacity

Message capacity depends on image size:

| Image Size | Resolution | Approximate Capacity |
|------------|------------|---------------------|
| VGA | 640×480 | ~75 characters |
| HD | 1280×720 | ~250 characters |
| Full HD | 1920×1080 | ~500 characters |
| 4K | 3840×2160 | ~2000 characters |

## JPEG Survival

Tested results:

| Format | Quality | Result |
|--------|---------|--------|
| PNG | lossless | ✓ Works |
| JPEG | 90 | ✓ Works |
| JPEG | 80 | ✓ Works |
| JPEG | 70 | ✓ Works |
| JPEG | 60 | ✓ Works |
| JPEG | 55 | ✗ Fails |
| WebP | lossless | ✓ Works |
| WebP | 80 | ✓ Works |

## Files

| File | Description |
|------|-------------|
| `run.bat` | Start the server and open browser |
| `server.py` | Python web server backend |
| `web_client.html` | Web interface (served by server.py) |
| `book_cipher.py` | Core encoding/decoding algorithms |
| `stego_gui.py` | Alternative Tkinter GUI application |
| `source_text.txt` | Shared source text for book cipher |

## Dependencies

```bash
pip install pillow numpy scipy reedsolo
```

## Alternative: GUI Application

Instead of the web interface, you can use the Tkinter GUI:

```bash
python stego_gui.py
```

## Technical Details

### Settings (tuned for JPEG Q60 survival)

```python
STRENGTH = 150      # DCT modification strength
RS_SYMBOLS = 64     # Reed-Solomon parity symbols
REPETITION = 7      # Bit repetition count
```

### Position Encoding

- **Zigzag encoding**: Converts signed integers to unsigned for efficient storage
- **Varint encoding**: Variable-length encoding (small numbers = fewer bytes)
- **zlib compression**: Further reduces data size

### Error Correction

1. **Reed-Solomon**: Adds 64 parity bytes, can correct up to 32 byte errors
2. **Repetition**: Each bit repeated 7 times, majority vote recovers from noise

## Limitations

1. **Source text required**: The `source_text.txt` file must contain all characters in your message
2. **Image modification**: Cropping or resizing the image will break the watermark
3. **Compression floor**: JPEG quality below 60 corrupts the embedded data
4. **Capacity**: Limited by image size (see capacity table above)

## License

MIT License
