# MediaInfoExtraction

A Python script that parses advanced MediaInfo `.txt` output files and extracts clean, structured information ready for video encoding workflows.

## File Structure

```
MediaInfoExtraction/
├── main.py
├── sources.txt        # optional: add your own source tags here
├── requirements.txt
├── README.md
├── Branded/           # see below
└── LICENSE
```

## Branded/ folder

The `Branded/` subfolder contains a variant of `main.py` (`main.hokan-sho.py`) that produces output
formatted specifically for the **Hokan-Sho** fansub group — it uses a slightly different line format
and source tag conventions. If you are not part of that group you can ignore this folder entirely;
the main `main.py` in the root is the general-purpose version.

## Installation

### Linux (Recommended - Virtual Environment)

```bash
git clone https://github.com/drew-codes-things/MediaInfoExtraction.git
cd MediaInfoExtraction

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### macOS / Windows (Simple Method)

```bash
git clone https://github.com/drew-codes-things/MediaInfoExtraction.git
cd MediaInfoExtraction

pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Batch mode: drag and drop files into the terminal (quoted paths with spaces are supported).

## Custom sources

Create a `sources.txt` file in the same directory as `main.py`, one source tag per line:

```
BD
NF
HMAX
ITVX
BBCIPLAYER
PEACOCK
```

The script reads this on startup. If the file is absent it falls back to the built-in list.

## Requirements

- Python 3.8+
- MediaInfo CLI or GUI (to generate the `.txt` files)

## License

MIT License
