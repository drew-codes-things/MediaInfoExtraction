#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaInfo Formatter — Hokan-Sho Network Edition
Parses MediaInfo .txt files and outputs formatted, branded metadata lines
ready to paste into Hokan-Sho release notes, NFOs, or databases.
"""

import os
import re
import shlex
from pathlib import Path

ASCII_ART = r"""
 _  _     _               ___ _         _  _    _                   _
| || |___| |_____ _ _ ___/ __| |_  ___  | \| |__| |_ __ _____ _ _ | |__
| __ / _ \ / / _ \ ' \___\__ \ ' \/ _ \ | .` / _` \ V  V / _ \ '_|| / /
|_||_\___/_\_\___/_||_|  |___/_||_\___/ |_|\_\__,_|\_/\_/\___/_|  |_\_\
                  MediaInfo Formatter v2.0 — Hokan-Sho Edition
"""

# ─────────────────────────────── helpers ────────────────────────────────────

def _val(line: str) -> str:
    parts = line.split(":", 1)
    return parts[1].strip() if len(parts) > 1 else parts[0].strip()


def _parse_path(raw: str) -> str:
    """Strip surrounding quotes from a pasted file path.
    Handles single quotes, double quotes, and Windows-style paths
    that may have been drag-and-dropped into the terminal.
    """
    raw = raw.strip()
    try:
        parts = shlex.split(raw)
        if parts:
            return parts[0]
    except ValueError:
        pass
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ('"', "'"):
        return raw[1:-1]
    return raw


def _norm_bitrate(raw: str) -> str:
    """Normalise a MediaInfo bitrate string to 'NNNN kbps'."""
    raw = raw.strip()
    lower = raw.lower()

    num_part = re.split(r'[a-zA-Z]', raw, maxsplit=1)[0].strip()
    num_clean = re.sub(r'[\s,]', '', num_part)

    try:
        val = float(num_clean)
    except ValueError:
        return raw

    if 'mb' in lower or 'mbit' in lower or 'mbps' in lower:
        return f"{int(round(val * 1000))} kbps"
    if 'kb' in lower or 'kbit' in lower or 'kbps' in lower:
        return f"{int(round(val))} kbps"
    if 'b/s' in lower or 'bps' in lower or val > 100_000:
        return f"{int(round(val / 1000))} kbps"
    if val >= 100:
        return f"{int(round(val))} kbps"
    return raw


def _norm_channels(text: str) -> str:
    m = re.search(r"\d+", text)
    if not m:
        return text
    n = int(m.group())
    return {8: "7.1", 6: "5.1", 4: "4.0", 3: "3.0", 2: "2.0", 1: "1.0"}.get(n, text)


def _norm_sampling(text: str) -> str:
    nums = re.sub(r"[^\d]", "", text.split("/")[0])
    if nums:
        hz = int(nums)
        return f"{hz/1000:.1f} kHz" if hz >= 1000 else f"{hz} Hz"
    return text.strip()


def _brand(line: str) -> str:
    """Append ' | Hokan-Sho' branding if not already present."""
    return line if "Hokan-Sho" in line else line + " | Hokan-Sho"


def _height_to_quality(h: int) -> str:
    for limit, label in [(2160, "2160p"), (1440, "1440p"), (1080, "1080p"),
                         (720, "720p"), (480, "480p")]:
        if h >= limit:
            return label
    return f"{h}p"


def _resolve_stem(filepath: str) -> str:
    base = os.path.basename(filepath)
    stem = base[:-14] if base.endswith(".MediaInfo.txt") else ".".join(base.split(".")[:-1])
    for ext in (".mkv", ".mp4", ".avi", ".mov", ".wmv",
                ".flv", ".webm", ".m4v", ".ts", ".m2ts"):
        if stem.lower().endswith(ext):
            stem = stem[: -len(ext)]
            break
    return stem.rstrip(".")


def _extract_quality_from_name(base: str) -> str:
    bracket_parts = [p.split("]")[0].strip() for p in base.split("[") if "]" in p]
    quality_parts = []
    for part in bracket_parts:
        for token in part.split():
            if re.fullmatch(r"\d{3,4}[Pp]", token) or re.fullmatch(r"[48][Kk]", token):
                quality_parts.append(token)
    return quality_parts[0] if quality_parts else "N/A"


# ─────────────────────────────── HDR ────────────────────────────────────────

def _parse_hdr(line: str, info: dict) -> None:
    value = _val(line)
    parts = [p.strip() for p in value.split(",")]
    if any("Dolby Vision" in p for p in parts):
        info["Dolby Vision"] = "Dolby Vision"
        m = re.search(r"Profile\s+([\d.]+)", value)
        if m:
            info["DV Profile"] = m.group(1)
    if any("HDR10+" in p for p in parts):
        info["HDR format"] = "HDR10+"
    elif any(re.search(r"\bHDR10\b", p) for p in parts):
        info["HDR format"] = "HDR10"
    elif any("HLG" in p for p in parts):
        info["HDR format"] = "HLG"


# ─────────────────────────────── audio ──────────────────────────────────────

_FORMAT_PRIORITY = {
    "MLP FBA 16-ch": 10,
    "MLP FBA":        9,
    "DTS XLL X":      8,
    "DTS XLL":        7,
    "E-AC-3 JOC":     6,
    "E-AC-3":         5,
    "FLAC":           5,
    "AC-3":           4,
    "DTS":            3,
    "MP3":            2,
    "AAC":            2,
    "VORBIS":         1,
    "OPUS":           1,
}

_FORMAT_ALIASES = {
    "MLP FBA 16-ch": "TrueHD Atmos",
    "MLP FBA":       "TrueHD",
    "DTS XLL X":     "DTS-X",
    "DTS XLL":       "DTS-HD MA",
    "DTS":           "DTS",
    "E-AC-3 JOC":    "E-AC-3 JOC (Atmos)",
    "E-AC-3":        "E-AC-3",
    "AC-3":          "AC-3",
    "FLAC":          "FLAC",
    "AAC":           "AAC",
    "MP3":           "MP3",
    "VORBIS":        "Vorbis",
    "OPUS":          "Opus",
}


def _audio_fmt(line: str) -> str:
    raw = _val(line)
    candidates = [p.strip() for p in re.split(r"\s*/\s*", raw)]

    best_key, best_score = None, -1
    for cand in candidates:
        score = _FORMAT_PRIORITY.get(cand, 0)
        if score > best_score:
            best_key, best_score = cand, score

    if best_key == "E-AC-3" and any("JOC" in c for c in candidates):
        best_key = "E-AC-3 JOC"

    if best_key not in _FORMAT_ALIASES:
        for token in _FORMAT_PRIORITY:
            if token in raw:
                best_key = token
                break

    return _FORMAT_ALIASES.get(best_key, raw.strip())


def _should_record_format(count: int, ainfo: dict) -> bool:
    if count == 1:
        return True
    return ainfo.get("Channels") in ("7.1", "5.1", "4.0")


# ─────────────────────────────── subtitles ──────────────────────────────────

def _sub_fmt(raw: str) -> str:
    lc = raw.strip().lower()
    if "utf-8" in lc or "subrip" in lc or "srt" in lc:
        return "SRT"
    if "ass" in lc or "ssa" in lc or "ffdshow" in lc:
        return "ASS"
    if "pgs" in lc or "hdmv" in lc:
        return "PGS"
    if "dvd" in lc or "vobsub" in lc:
        return "VobSub"
    if "webvtt" in lc or "vtt" in lc:
        return "WebVTT"
    return raw.strip()


# ─────────────────────────────── core extractor ─────────────────────────────

def extract_info(filepath: str) -> dict:
    info: dict = {"Audio": [], "Subtitles": []}
    info["Complete name"] = _resolve_stem(filepath)
    info["Quality"]       = _extract_quality_from_name(os.path.basename(filepath))

    section    = None
    audio_info : dict = {}
    sub_info   : dict = {}
    lang_cnt   = fmt_cnt = comm_cnt = 0

    with open(filepath, encoding="utf-8", errors="ignore") as fh:
        lines_raw = fh.readlines()

    w = h = None
    for ln in lines_raw:
        if w is None and re.match(r"^Width\s*:", ln):
            nums = re.sub(r"[^\d]", "", _val(ln))
            if nums: w = int(nums)
        if h is None and re.match(r"^Height\s*:", ln):
            nums = re.sub(r"[^\d]", "", _val(ln))
            if nums: h = int(nums)

    if h and info["Quality"] == "N/A":
        info["Quality"] = _height_to_quality(h)

    for line in lines_raw:
        stripped = line.strip()

        if re.match(r"^Video\b",   stripped): section = "Video"; continue
        if re.match(r"^Audio\b",   stripped):
            if audio_info: info["Audio"].append(audio_info)
            audio_info = {}; section = "Audio"; lang_cnt = fmt_cnt = comm_cnt = 0; continue
        if re.match(r"^Text\b",    stripped):
            if sub_info: info["Subtitles"].append(sub_info)
            sub_info = {}; section = "Text"; lang_cnt = 0; continue
        if re.match(r"^(Menu|General)\b", stripped): section = None; continue
        if not stripped: continue

        if section == "Video":
            if re.match(r"^Bit rate\s*:", line) and "Maximum" not in line and "Nominal" not in line:
                info["Bit rate"] = _norm_bitrate(_val(line))
            elif re.match(r"^Frame rate\s*:", line):
                info["Frame rate"] = _val(line).split()[0] + " fps"
            elif re.match(r"^Format profile\s*:", line):
                info["Format profile"] = _val(line)
            elif re.match(r"^HDR format\s*:", line):
                _parse_hdr(line, info)
            elif re.match(r"^Format\s*:", line) and "Format" not in info:
                info["Format"] = _val(line)
            elif re.match(r"^Bit depth\s*:", line):
                info["Bit depth"] = _val(line).replace("bits", "").strip() + " Bit"
            elif re.match(r"^Display aspect ratio\s*:", line) and "Display aspect ratio" not in info:
                info["Display aspect ratio"] = _val(line).split()[0]
            elif re.match(r"^Color primaries\s*:", line):
                info["Color primaries"] = _val(line)
            elif re.match(r"^Transfer characteristics\s*:", line):
                info["Transfer characteristics"] = _val(line)
            elif re.match(r"^Matrix coefficients\s*:", line):
                info["Matrix coefficients"] = _val(line)
            elif re.match(r"^Mastering display color primaries\s*:", line):
                info["Mastering display color primaries"] = _val(line)
            elif re.match(r"^Mastering display luminance\s*:", line):
                info["Mastering display luminance"] = _val(line)
            elif re.match(r"^Maximum Content Light Level\s*:", line):
                info["MaxCLL"] = _val(line)
            elif re.match(r"^Maximum Frame-Average Light Level\s*:", line):
                info["MaxFALL"] = _val(line)
            elif re.match(r"^Codec ID\s*:", line) and "Codec ID" not in info:
                info["Codec ID"] = _val(line)

        elif section == "Audio":
            if re.match(r"^Language\s*:", line) and "Language/" not in line:
                lang_cnt += 1
                if lang_cnt == 1: audio_info["Language code"] = _val(line)
                elif lang_cnt == 2: audio_info["Language"] = _val(line)
            elif re.match(r"^Format\s*:", line):
                fmt_cnt += 1
                if _should_record_format(fmt_cnt, audio_info):
                    audio_info["Format"] = _audio_fmt(line)
            elif re.match(r"^Commercial name\s*:", line):
                comm_cnt += 1
                if comm_cnt == 1: audio_info["Commercial name"] = _val(line)
            elif re.match(r"^Format/Info\s*:", line) and "Format/Info" not in audio_info:
                audio_info["Format/Info"] = _val(line)
            elif re.match(r"^Channels\s*:", line):
                audio_info["Channels"] = _norm_channels(_val(line))
            elif re.match(r"^Channel positions\s*:", line) and "Channel positions" not in audio_info:
                audio_info["Channel positions"] = _val(line)
            elif re.match(r"^Sampling rate\s*:", line):
                audio_info["Sampling rate"] = _norm_sampling(_val(line))
            elif re.match(r"^Maximum bit rate\s*:", line):
                audio_info["Maximum bit rate"] = _norm_bitrate(_val(line))
            elif re.match(r"^Bit rate\s*:", line) and "Maximum" not in line:
                audio_info["Bit rate"] = _norm_bitrate(_val(line))
            elif re.match(r"^Bit depth\s*:", line):
                audio_info["Bit depth"] = _val(line).replace("bits", "").strip() + " Bit"
            elif re.match(r"^Bit rate mode\s*:", line):
                audio_info["Bit rate mode"] = _val(line)
            elif re.match(r"^Compression mode\s*:", line):
                audio_info["Compression mode"] = _val(line)
            elif re.match(r"^Default\s*:", line): audio_info["Default"] = _val(line)
            elif re.match(r"^Forced\s*:",  line): audio_info["Forced"]  = _val(line)
            elif re.match(r"^Number of dynamic objects\s*:", line):
                audio_info["Dynamic objects"] = _val(line)
            elif re.match(r"^Codec ID\s*:", line) and "Codec ID" not in audio_info:
                audio_info["Codec ID"] = _val(line)

        elif section == "Text":
            if re.match(r"^Language\s*:", line) and "Language/" not in line:
                lang_cnt += 1
                if lang_cnt == 1: sub_info["Language code"] = _val(line)
                elif lang_cnt == 2: sub_info["Language"] = _val(line)
            elif re.match(r"^Format\s*:", line) and "Format" not in sub_info:
                sub_info["Format"] = _sub_fmt(_val(line))
            elif re.match(r"^Default\s*:", line): sub_info["Default"] = _val(line)
            elif re.match(r"^Forced\s*:",  line): sub_info["Forced"]  = _val(line)
            elif re.match(r"^Title\s*:",   line) and "Title" not in sub_info:
                sub_info["Title"] = _val(line)

    if audio_info: info["Audio"].append(audio_info)
    if sub_info:   info["Subtitles"].append(sub_info)
    return info


# ─────────────────────────────── output formatter ───────────────────────────

def _rate_key(ainfo: dict) -> str:
    if "Maximum bit rate" in ainfo and ainfo.get("Channels") in ("7.1", "5.1", "4.0"):
        return "Maximum bit rate"
    return "Bit rate"


def format_output(info: dict, is_remux: bool, src: str) -> str:
    title   = info["Complete name"]
    quality = info.get("Quality", "N/A")

    video_parts = [
        title,
        info.get("Bit rate", "N/A"),
        quality,
        info.get("Frame rate", "N/A"),
        info.get("Format profile", "N/A"),
    ]
    if "Dolby Vision" in info: video_parts.append(info["Dolby Vision"])
    if "HDR format"   in info: video_parts.append(info["HDR format"])
    video_parts += [
        info.get("Bit depth", "N/A"),
        info.get("Display aspect ratio", "N/A"),
        info.get("Format", "N/A"),
    ]
    if src: video_parts.append(src)
    video_line = _brand(" | ".join(str(p) for p in video_parts))

    audio_lines = []
    for a in info["Audio"]:
        parts = [
            a.get("Language", a.get("Language code", "N/A")),
            a.get("Format", "N/A"),
            a.get("Channels", "N/A"),
            a.get("Sampling rate", "N/A"),
            a.get(_rate_key(a), "N/A"),
        ]
        if "Bit depth" in a: parts.append(a["Bit depth"])
        if src: parts.append(src)
        audio_lines.append(_brand(" | ".join(str(p) for p in parts)))

    sub_lines = []
    for s in info["Subtitles"]:
        if "Language" not in s and "Language code" not in s:
            continue
        lang = s.get("Language", s.get("Language code", "N/A"))
        fmt  = s.get("Format", "N/A")
        line = f"Subtitles | {lang} | {fmt}"
        if src: line += f" | {src}"
        sub_lines.append(_brand(line))

    fname = title
    if "Dolby Vision" in info: fname += f" {info['Dolby Vision']}"
    if "HDR format"   in info: fname += f" {info['HDR format']}"
    if is_remux: fname += " Remux"
    fname += " Encoded by The Hokan-Sho Network"

    sections = [f"File name: {fname}", video_line]
    if audio_lines:
        sections.append("--- Audio ---")
        sections.extend(audio_lines)
    if sub_lines:
        sections.append("--- Subtitles ---")
        sections.extend(sub_lines)

    return "\n".join(sections)


# ─────────────────────────────── file processor ─────────────────────────────

def process_file(path: str, is_remux: bool, src: str) -> None:
    p = Path(path.strip())
    if not p.is_file():
        print(f"  [!] Not found: {p}")
        return
    info     = extract_info(str(p))
    out_text = format_output(info, is_remux, src)
    out_path = p.with_name(f"Formatted - {p.stem}{p.suffix}")
    out_path.write_text(out_text, encoding="utf-8")
    print(f"  \u2713 Written \u2192 {out_path}")


# ─────────────────────────────── CLI ────────────────────────────────────────

def ask_yes_no(prompt: str, default: str = "y") -> bool:
    default = default.lower()
    suffix  = " [Y/n] " if default == "y" else " [y/N] "
    ans     = input(f"{prompt}{suffix}").strip().lower() or default
    return ans == "y"


SOURCES = {
    "1":  "BD",   "2": "DVD",  "3": "NF",   "4": "CR",
    "5":  "AMZN", "6": "HULU", "7": "DSNP", "8": "ATVP",
    "9":  "PMTP", "10": "PCOK",
}


def choose_source() -> str:
    print("\nMedia source:")
    for k, v in SOURCES.items():
        print(f"  {k}. {v}")
    choice = input("Enter number (default 1 = BD): ").strip() or "1"
    return SOURCES.get(choice, "BD")


def main() -> None:
    print(ASCII_ART)
    print("Select run mode:")
    print("  1. Batch  — paste multiple file paths")
    print("  2. Interactive — one file at a time")
    mode = input("Choose [1/2] (default 1): ").strip() or "1"

    if mode == "1":
        print("\nPaste file paths (space-separated or quoted), then press Enter:")
        raw   = input("> ").strip()
        files = shlex.split(raw)
        if not files:
            print("No files given.")
            return
        same = ask_yes_no("Same settings for every file?", default="y")
        if same:
            is_remux = ask_yes_no("Remux?", default="n")
            src      = choose_source()
            for f in files:
                print(f"\n--- {f} ---")
                process_file(f, is_remux, src)
        else:
            for f in files:
                print(f"\n--- {f} ---")
                is_remux = ask_yes_no("Remux?", default="n")
                src      = choose_source()
                process_file(f, is_remux, src)
    else:
        while True:
            raw = input("\nPath to MediaInfo .txt file (blank to quit): ").strip()
            if not raw:
                break
            f = _parse_path(raw)
            is_remux = ask_yes_no("Remux?", default="n")
            src      = choose_source()
            process_file(f, is_remux, src)
            if not ask_yes_no("Process another file?", default="y"):
                break

    input("\nPress Enter to exit\u2026")


if __name__ == "__main__":
    main()
