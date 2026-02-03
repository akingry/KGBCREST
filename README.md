# KGBCREST

**Kingry Graphical Book Cipher Compression Resistant Encrypted Steganography Tool**

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

The data is embedded in the **Discrete Cosine Transform (DCT)** coefficients of the image — the same frequency domain that JPEG compression operates in. This is why encoded images survive JPEG compression.

#### What is DCT?

The Discrete Cosine Transform converts an 8×8 block of pixels from spatial domain (brightness values) into frequency domain (how quickly brightness changes across the block):

```
Spatial Domain          DCT Frequency Domain
┌─────────────────┐     ┌─────────────────┐
│ Pixel values    │ ──► │ DC | Low freq   │
│ (0-255 each)    │     │ ───┼───────────  │
│                 │     │ Mid│            │
│ 8×8 = 64 pixels │     │ ───┼─── High    │
└─────────────────┘     └─────────────────┘
```

- **DC coefficient** (top-left): Average brightness of the block
- **Low frequencies**: Gradual changes, smooth gradients
- **Mid frequencies**: Edges, textures — **this is where we hide data**
- **High frequencies**: Fine detail, noise — discarded by JPEG

#### Why Mid-Frequency?

JPEG compression:
1. Preserves the DC coefficient (average brightness)
2. Preserves low frequencies (smooth areas)
3. **Mostly preserves mid frequencies** (edges/structure)
4. Aggressively discards high frequencies (fine detail)

By embedding data in **mid-frequency coefficient (4,3)**, we hide information in a region that:
- Survives JPEG quantization (unlike high frequencies)
- Isn't visually obvious (unlike DC/low frequencies)
- Has enough "room" to encode bits robustly

#### Quantization Index Modulation (QIM)

To embed a bit, we use QIM — a technique that quantizes the coefficient to encode 0 or 1:

```
Original coefficient: 127.3

To embed bit = 1:
  quantized = round(127.3 / 150) × 150 = 150
  modified  = 150 + (150 × 0.3) = 195

To embed bit = 0:
  quantized = round(127.3 / 150) × 150 = 150
  modified  = 150 - (150 × 0.3) = 105

Extraction:
  Read coefficient, compare to quantization grid
  If coefficient ≥ quantized → bit = 1
  If coefficient < quantized → bit = 0
```

The **strength parameter (150)** determines the quantization step size:
- Higher strength = more robust to compression, but more visible artifacts
- Lower strength = less visible, but more fragile
- 150 is tuned to survive JPEG quality 60 while remaining visually subtle

#### The Full Process

```
For each 8×8 block in the image:
   1. Extract the block from luminance (Y) channel
   2. Apply 2D DCT transform
   3. Read coefficient at position (4,3)
   4. Modify coefficient using QIM to encode one bit
   5. Apply inverse DCT
   6. Write modified block back to image
```

This embeds **one bit per 8×8 block**, so a 1920×1080 image has:
- (1920/8) × (1080/8) = 240 × 135 = 32,400 blocks
- 32,400 bits available (minus 24-bit header = 32,376 data bits)
- After 7× repetition and RS coding: ~500 usable characters

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
| `source_text.txt` | Shared source text for book cipher |

## Dependencies

```bash
pip install pillow numpy scipy reedsolo
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
