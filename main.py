#!/usr/bin/env python3
import os
import re
import sys
import shlex
from pathlib import Path

ASCII_ART = r"""
__ ___  ___  ____  ____  ______   __  __
/ |/ /__  ____/ (_)___ _/ _/___ / __/___ / ____/___ _________ ___  ____ _/ /_/ /____ _____
/ /|_/ / _ \/ __ / / __ `// // __ \/ /_/ __ \ / /_ / __ \/ ___/ __ `__ \/ __ `/ __/ __/ _ \/ ___/
/ / / / __/ /_/ / / /_/ // // / / / __/ /_/ / / __/ / /_/ / / / / / / / / /_/ / /_/ /_/ __/ /
/_/ /_/\___/\__,_/_/\__,_/___/_/ /_/_/ \____/ /_/ \____/_/ /_/ /_/ /_/\__,_/\__/\__/\___/_/
"""

DEFAULT_SOURCES = [
    "BD", "DVD", "NF", "CR", "AMZN", "HULU", "DSNP", "ATVP",
    "PMTP", "PCOK", "MAX", "STAN",
    "HMAX", "ITVX", "BBCIPLAYER", "PEACOCK",
]


def load_sources():
    """Load sources from sources.txt next to the script, falling back to hardcoded list."""
    sources_file = Path(__file__).parent / "sources.txt"
    if sources_file.is_file():
        try:
            lines = [l.strip() for l in sources_file.read_text(encoding="utf-8").splitlines() if l.strip()]
            if lines:
                return lines
        except OSError:
            pass
    return DEFAULT_SOURCES


def extract_info(file_path: str) -> dict:
    info = {"Audio": [], "Subtitles": []}
    section = None
    audio_info = subtitle_info = None
    language_cnt = format_cnt = 0

    base = os.path.basename(file_path)
    if base.endswith(".MediaInfo.txt"):
        stem = base[:-13]
        stem = stem.rstrip('.')
    else:
        stem = ".".join(base.split(".")[:-1])

    for ext in (".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"):
        if stem.endswith(ext):
            stem = stem[:-len(ext)]
            break
    stem = stem.rstrip(".")

    bracket_parts = [part.split("]")[0].strip()
                     for part in base.split("[") if "]" in part]
    quality_parts = [q for q in bracket_parts if re.fullmatch(r"\d+p|\d+K", q, re.I)]
    info["Quality"] = " ".join(quality_parts) if quality_parts else "N/A"
    info["Complete name"] = stem

    with open(file_path, encoding="utf-8", errors="ignore") as fh:
        lines = fh.readlines()

    for line in lines:
        stripped = line.strip()
        if re.match(r'^Video\b', stripped):
            section = "Video"
        elif re.match(r'^Audio\b', stripped):
            if audio_info:
                info["Audio"].append(audio_info)
            audio_info = {}
            section = "Audio"; language_cnt = format_cnt = 0
        elif re.match(r'^Text\b', stripped):
            if subtitle_info:
                info["Subtitles"].append(subtitle_info)
            subtitle_info = {}
            section = "Text"; language_cnt = 0
        elif not stripped:
            section = None

        if section == "Video":
            if line.startswith("Bit rate") and "/" not in line:
                info["Bit rate"] = _norm_bitrate(line)
            elif line.startswith("Frame rate"):
                fps = line.split(":", 1)[1].split("(")[0].strip()
                info["Frame rate"] = f"{fps} fps"
            elif line.startswith("Format profile"):
                info["Format profile"] = line.split(":", 1)[1].strip()
            elif line.startswith("HDR format"):
                _handle_hdr(info, line)
            elif "Format " in line:
                vals = line.split(":", 1)[1].split()
                info["Format"] = vals[1] if len(vals) > 1 else vals[0]
            elif line.startswith("Bit depth"):
                info["Bit depth"] = line.split(":", 1)[1].strip().replace("bits", "Bit")
            elif "Display aspect ratio" in line and "Active" not in info:
                raw = line.split(":", 1)[1].strip()
                info["Display aspect ratio"] = _norm_aspect_ratio(raw)

        elif section == "Audio":
            if "Language" in line and "Language_More" not in line:
                language_cnt += 1
                if language_cnt == 2:
                    audio_info["Language"] = line.split(":", 1)[1].strip()
            elif "Format" in line:
                format_cnt += 1
                if _use_this_format(format_cnt, audio_info):
                    audio_info["Format"] = _audio_fmt(line)
            elif "Channel(s)" in line:
                audio_info["Channels"] = _norm_channels(line)
            elif "Sampling rate" in line:
                audio_info["Sampling rate"] = line.split(":", 1)[1].strip()
            elif "Bit rate" in line:
                audio_info["Bit rate"] = _clean_kbps(line)
            elif "Maximum bit rate" in line:
                audio_info["Maximum bit rate"] = _clean_kbps(line)

        elif section == "Text":
            if "Language" in line and "Language_More" not in line:
                language_cnt += 1
                if language_cnt == 2:
                    subtitle_info["Language"] = line.split(":", 1)[1].strip()
            elif "Format" in line:
                raw = line.split(":", 1)[1].strip()
                if raw == "UTF-8" or "ffdshow" in raw.lower():
                    subtitle_info["Format"] = "ASS"
                else:
                    subtitle_info["Format"] = raw

    if audio_info:
        info["Audio"].append(audio_info)
    if subtitle_info:
        info["Subtitles"].append(subtitle_info)

    if info["Quality"] == "N/A":
        _, h = _resolution(lines)
        if h:
            info["Quality"] = _height_to_quality(h)
    return info


def _norm_bitrate(line):
    raw = line.split(":", 1)[1].strip()
    cleaned = re.sub(r'[^0-9.]', ' ', raw).strip()
    try:
        val = float(cleaned.split()[0]) if cleaned else 0
        if val > 100000:
            return f"{int(val / 1000)} kbps"
        if "mb/s" in raw.lower():
            return f"{int(val * 1000)} kbps"
        if "kb/s" in raw.lower() or "kbps" in raw.lower():
            return f"{int(val)} kbps"
        return f"{int(val)} kbps" if val > 0 else raw
    except (ValueError, IndexError):
        return raw.replace("bits", "Bit")


def _handle_hdr(info, line):
    for part in line.split(":", 1)[1].split("/"):
        part = part.strip()
        if "Dolby Vision" in part:
            info["Dolby Vision"] = "Dolby Vision"
        elif "HDR10+" in part:
            info["HDR format"] = "HDR10+"
        elif "HDR10" in part and "HDR format" not in info:
            info["HDR format"] = "HDR10"


def _use_this_format(cnt, ainfo):
    """
    Decide whether to capture a Format line for an audio track.

    MediaInfo emits two Format lines per track: the first is the container
    format identifier and the second is the actual codec name we want.
    For multichannel tracks (5.1/7.1) the codec name appears on the first
    Format line, so we capture it immediately.
    For stereo or unknown-channel tracks we always capture on cnt == 1
    as a fallback so single-track stereo files are not missed.
    """
    channels = ainfo.get("Channels")
    if channels in {"7.1", "5.1"}:
        return cnt == 1
    return cnt in (1, 2)


def _audio_fmt(line):
    raw = line.split(":", 1)[1].lower()
    parts = line.split(":", 1)[1].split()

    if "truehd" in raw or "mlp fba" in raw:
        if "16-ch" in raw or "atmos" in raw:
            return "MLP FBA 16-ch"
        return "MLP FBA"
    if "dts" in raw:
        if "xll" in raw or "hd master" in raw:
            return "DTS XLL"
        if "x" in raw:
            return "DTS XLL X"
        return "DTS"
    if "ac-3" in raw or "ac3" in raw:
        return "AC-3"
    if "e-ac-3" in raw or "eac3" in raw:
        if "joc" in raw:
            return "E-AC-3 JOC"
        return "E-AC-3"
    if "flac" in raw:
        return "FLAC"
    if "aac" in raw:
        return "AAC"
    if "opus" in raw:
        return "OPUS"
    if "vorbis" in raw:
        return "VORBIS"
    if "mp3" in raw:
        return "MP3"

    fmt = parts[1] if len(parts) > 1 else parts[0]
    return fmt.replace("JOC", "E-AC-3 JOC")


def _norm_channels(line):
    txt = line.split(":", 1)[1].strip()
    m = re.search(r"\d+", txt)
    if not m:
        return txt
    n = int(m.group())
    return {8: "7.1", 6: "5.1", 2: "2"}.get(n, txt)


def _clean_kbps(line):
    """
    Extract and normalise a kbps value from a MediaInfo bit-rate line.

    The raw value is something like "384 kbps" or "384 kb/s". After
    normalising the unit label the string is never a bare digit, so the
    old val.isdigit() guard was never True and the slicing branch was
    dead code. The corrected check strips whitespace and the unit before
    testing, allowing truly bare numeric strings to be returned as-is.
    """
    val = line.split(":", 1)[1].strip().replace("kb/s", "kbps").replace("Kb/s", "kbps")
    numeric_part = val.replace(" ", "").replace("kbps", "")
    if numeric_part.isdigit():
        return numeric_part[:1] + numeric_part[2:]
    return val


def _resolution(lines):
    w = h = None
    for ln in lines:
        if w is None and "Width" in ln:
            w = int("".join(filter(str.isdigit, ln.split(":")[1])))
        if h is None and "Height" in ln:
            h = int("".join(filter(str.isdigit, ln.split(":")[1])))
    return w, h


def _height_to_quality(h):
    return ("2160p" if h >= 2160 else "1440p" if h >= 1440 else
            "1080p" if h >= 1080 else "720p" if h >= 720 else
            "480p" if h >= 480 else f"{h}p")


def _norm_aspect_ratio(txt):
    txt = txt.strip()
    if ":" in txt:
        try:
            w, h = map(float, txt.split(":"))
            if h > 0:
                return f"{w / h:.3f}"
        except (ValueError, ZeroDivisionError):
            pass
    return txt


def format_output(info, is_remux, src):
    vline = (f"Video: {info['Complete name']} / {info.get('Bit rate','N/A')} / "
             f"{info['Quality']} / {info.get('Frame rate','N/A')} / "
             f"{info.get('Format profile','N/A')} /")
    if "Dolby Vision" in info:
        vline += f" {info['Dolby Vision']} /"
    if "HDR format" in info:
        vline += f" {info['HDR format']} /"
    vline += (f" {info.get('Bit depth','N/A')} / "
              f"{info.get('Display aspect ratio','N/A')} / "
              f"{info.get('Format','N/A')} / {src}")

    audio = []
    for a in info["Audio"]:
        ln = "Audio:"
        for k in ("Language", "Format", "Channels", "Sampling rate"):
            if k in a:
                ln += f" {a[k]} /"
        rate_key = "Maximum bit rate" if a.get("Channels") in {"7.1", "8"} else "Bit rate"
        if rate_key in a:
            ln += f" {a[rate_key].replace(' ', '').replace('kbps', ' kbps')} /"
        ln += f" {src}"
        audio.append(ln)

    subs = []
    for s in info["Subtitles"]:
        if {"Language", "Format"} <= s.keys():
            subs.append(f"Subtitles: {s['Language']} / {s['Format']} / {src}")

    clean_name = re.sub(r'\s*\[\d+[pK]\]', '', info['Complete name'], flags=re.IGNORECASE).strip()
    fname = clean_name
    if info.get('Quality') and info['Quality'] != "N/A":
        fname += f" [{info['Quality']}]"
    if "Dolby Vision" in info:
        fname += f" [{info['Dolby Vision']}]"
    if "HDR format" in info:
        fname += f" [{info['HDR format']}]"
    if is_remux:
        fname += " [Remux]"

    return f"File name: {fname}\n\n{vline}\n\n" + "\n".join(audio) + "\n\n" + "\n".join(subs)


def process_file(path, is_remux, src):
    p = Path(path.strip('"'))
    if not p.is_file():
        print(f"[!] Not found: {p}")
        return
    try:
        info = extract_info(str(p))
        out_text = format_output(info, is_remux, src)
        out_path = p.with_name(f"Formatted - {p.stem}{p.suffix}")
        try:
            out_path.write_text(out_text, encoding="utf-8")
            print(f"[OK] {out_path}")
        except OSError as e:
            print(f"[!] Could not write output file '{out_path}': {e}")
            print(f"    Tip: check that the folder is not read-only or network-mounted.")
    except Exception as e:
        print(f"[!] Error processing {p.name}: {e}")


def ask_yes_no(prompt, default="y"):
    default = default.lower()
    assert default in {"y", "n"}
    suffix = "[Y/n]" if default == "y" else "[y/N]"
    ans = input(f"{prompt} {suffix}: ").strip().lower()
    if not ans:
        ans = default
    return ans == "y"


def choose_source(sources):
    print("\nChoose media source:")
    for i, s in enumerate(sources, 1):
        print(f"{i}. {s}")
    choice = input(f"Enter (1-{len(sources)}) [1]: ").strip() or "1"
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(sources):
            return sources[idx]
    except ValueError:
        pass
    return sources[0]


def main():
    print(ASCII_ART)
    sources = load_sources()

    print("Select run mode:")
    print("1. Batch - drag and drop files or paste quoted paths")
    print("2. Interactive - one path at a time")
    mode = input("Choose 1 or 2 [1]: ").strip() or "1"

    if mode == "1":
        print("\nDrag and drop your file(s) here (quoted paths are supported), then press Enter:")
        raw = input("> ").strip()
        files = shlex.split(raw)
        if not files:
            print("No files given."); return

        same = ask_yes_no("\nUse the SAME settings for every file?", default="y")
        if same:
            is_remux = ask_yes_no("Remux?", default="n")
            src = choose_source(sources)
            for f in files:
                process_file(f, is_remux, src)
        else:
            for f in files:
                print(f"\n--- {f} ---")
                is_remux = ask_yes_no("Remux?", default="n")
                src = choose_source(sources)
                process_file(f, is_remux, src)

    else:
        while True:
            f = input("\nEnter path to MediaInfo.txt file: ").strip()
            if not f:
                break
            is_remux = ask_yes_no("Remux?", default="n")
            src = choose_source(sources)
            process_file(f, is_remux, src)
            if not ask_yes_no("Process another file?", default="y"):
                break

    input("\nDone. Press Enter to exit...")


if __name__ == "__main__":
    main()
