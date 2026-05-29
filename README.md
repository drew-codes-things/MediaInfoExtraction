# MediaInfoExtraction

A Python script that parses advanced MediaInfo `.txt` output files and extracts clean, structured information ready for video encoding workflows.

## Features

- Parses detailed MediaInfo text exports
- Extracts video, audio, and subtitle track information
- Outputs clean JSON or formatted text
- Useful for encoding pipelines, quality control, and archiving

## Installation

```bash
git clone https://github.com/drew-codes-things/MediaInfoExtraction.git
cd MediaInfoExtraction
pip install -r requirements.txt
```

## Usage

```bash
python main.py path/to/mediainfo.txt
```

The script will output parsed data in a readable format (and optionally save it as JSON).

## Requirements

- Python 3.8+
- MediaInfo CLI or GUI (to generate the source .txt file)

## License

MIT License