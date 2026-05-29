# MediaInfoExtraction

A Python script that parses advanced MediaInfo `.txt` output files and extracts clean, structured information ready for video encoding workflows.

## File Structure

```
MediaInfoExtraction/
├── main.py
├── requirements.txt
├── README.md
└── LICENSE
```

## Installation (Recommended: Virtual Environment)

### On Linux / macOS

```bash
git clone https://github.com/drew-codes-things/MediaInfoExtraction.git
cd MediaInfoExtraction

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### On Windows

```bash
git clone https://github.com/drew-codes-things/MediaInfoExtraction.git
cd MediaInfoExtraction

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

```bash
python main.py path/to/mediainfo.txt
```

## Requirements

- Python 3.8+
- MediaInfo CLI or GUI

## License

MIT License