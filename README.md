# MediaInfoExtraction

Parses MediaInfo text output into normalized release/encoding metadata lines.

## Scripts

- `main.py`: general formatter.
- `Branded/main.hokan-sho.py`: branded output variant.

## Usage

```bash
python main.py
```

Optional: add custom source tags in `sources.txt` (one tag per line).

## Requirements

- Python 3.8+
- No third-party Python dependencies.
- MediaInfo output `.txt` files as input.

## License

MIT

