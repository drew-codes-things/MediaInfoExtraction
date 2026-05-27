# MediaInfo Formatter — The Hokan-Sho Network

A Python 3 command-line tool that parses **MediaInfo plain-text reports** (`.MediaInfo.txt`) and produces clean, consistently formatted metadata lines ready to paste into Hokan-Sho release notes, NFOs, or databases.

---

## Requirements

- Python 3.8+
- No external dependencies — standard library only.

---

## Usage

```bash
python main.py
```

You will be prompted to choose a run mode:

### Batch mode (mode 1)
Paste one or more file paths (space-separated or quoted):
```
> "C:/Media/Film.mkv.MediaInfo.txt" "D:/Shows/Episode.mkv.MediaInfo.txt"
```
Optionally apply the same settings (remux flag, source) to all files, or configure each one individually.

### Interactive mode (mode 2)
Enter one file path at a time, answer the prompts, then choose whether to continue.

---

## Output

For each input file a new text file is written alongside it:
```
Formatted - OriginalFilename.mkv.MediaInfo.txt
```

**Example output:**
```
File name: My Movie 2024 2160p Dolby Vision HDR10 Remux Encoded by The Hokan-Sho Network
My Movie 2024 | 45297 kbps | 2160p | 23.976 fps | Main 10@L5.1@High | Dolby Vision | HDR10 | 10 Bit | 1.778 | HEVC | BD | Hokan-Sho
--- Audio ---
English | MLP FBA 16-ch | 7.1 | 48.0 kHz | 7680 kbps | BD | Hokan-Sho
English | AC-3 | 5.1 | 48.0 kHz | 640 kbps | BD | Hokan-Sho
--- Subtitles ---
Subtitles | English | PGS | BD | Hokan-Sho
```

---

## Supported Codecs & Formats

### Video
| Codec | MediaInfo identifier |
|-------|---------------------|
| H.264 / AVC | `AVC` |
| H.265 / HEVC | `HEVC` |
| AV1 | `AV1` |
| VP9 | `VP9` |
| MPEG-4 / Xvid | `MPEG-4 Visual` |
| MPEG-2 | `MPEG Video` |

### HDR
| Format | Detection method |
|--------|----------------|
| Dolby Vision | `Dolby Vision` in HDR format line |
| Dolby Vision + HDR10 | Both extracted from compound line |
| HDR10 | `HDR10` in HDR format line |
| HDR10+ | `HDR10+` in HDR format line |
| HLG | `HLG` in HDR format line |

### Audio
| Format | Label |
|--------|-------|
| Dolby TrueHD Atmos | `MLP FBA 16-ch` |
| Dolby TrueHD | `MLP FBA` |
| DTS:X | `DTS XLL X` |
| DTS-HD Master Audio | `DTS XLL` |
| Dolby Atmos (EAC-3) | `E-AC-3 JOC` |
| Dolby Digital Plus | `E-AC-3` |
| Dolby Digital | `AC-3` |
| FLAC | `FLAC` |
| DTS | `DTS` |
| AAC | `AAC` |
| MP3 | `MP3` |
| Opus | `OPUS` |
| Vorbis | `VORBIS` |

### Subtitles
| Format | Label |
|--------|-------|
| PGS (Blu-ray image subs) | `PGS` |
| ASS / SSA | `ASS` |
| SRT / UTF-8 / SubRip | `SRT` |
| VobSub / DVD image subs | `VobSub` |
| WebVTT | `WebVTT` |

### Sources
| Code | Service |
|------|---------|
| BD | Blu-ray Disc |
| DVD | DVD |
| NF | Netflix |
| CR | Crunchyroll |
| AMZN | Amazon Prime Video |
| HULU | Hulu |
| DSNP | Disney+ |
| ATVP | Apple TV+ |
| PMTP | Paramount+ |
| PCOK | Peacock |

---

## Supported MediaInfo Fields

### Video stream
| Field | Notes |
|-------|-------|
| `Bit rate` | Normalised to kbps |
| `Frame rate` | e.g. `23.976 fps` |
| `Format profile` | e.g. `Main 10@L5.1@High` |
| `HDR format` | Full compound line parsed |
| `Bit depth` | e.g. `10 Bit` |
| `Display aspect ratio` | e.g. `1.778` |
| `Color primaries` | e.g. `BT.2020` |
| `Transfer characteristics` | e.g. `PQ` |
| `Matrix coefficients` | e.g. `BT.2020 non-constant` |
| `Mastering display color primaries` | HDR metadata |
| `Mastering display luminance` | HDR metadata |
| `Maximum Content Light Level` | MaxCLL |
| `Maximum Frame-Average Light Level` | MaxFALL |
| `Codec ID` | e.g. `V_MPEGH/ISO/HEVC` |

### Audio stream (per track)
| Field | Notes |
|-------|-------|
| `Language` | Full name + language code stored separately |
| `Format` | Canonical label via priority table |
| `Commercial name` | e.g. `Dolby TrueHD with Dolby Atmos` |
| `Channels` | Mapped to `7.1`, `5.1`, `2.0` etc. |
| `Channel positions` | Raw layout string |
| `Sampling rate` | Normalised to kHz |
| `Bit rate` | Normalised to kbps |
| `Maximum bit rate` | Used for lossless multichannel tracks |
| `Bit depth` | e.g. `24 Bit` |
| `Bit rate mode` | `Constant` / `Variable` |
| `Compression mode` | `Lossless` / `Lossy` |
| `Default` / `Forced` | Track flags |
| `Number of dynamic objects` | Atmos bed count |
| `Codec ID` | e.g. `A_TRUEHD` |

### Subtitle / Text stream (per track)
| Field | Notes |
|-------|-------|
| `Language` | Full name + language code stored separately |
| `Format` | Normalised to canonical label |
| `Title` | Track title if present |
| `Default` / `Forced` | Track flags |

---

## Key Design Decisions

- **Format priority table** — when MediaInfo outputs compound values like `MLP FBA / MLP FBA 16-ch`, the highest-ranked codec in the priority table wins.
- **Bitrate selection** — lossless multichannel (5.1, 7.1) tracks use `Maximum bit rate`; all other tracks use average `Bit rate`.
- **Channel normalisation** — raw counts (`6 channels`) are mapped to surround labels (`5.1`).
- **HDR compound parsing** — a single HDR format line can carry both Dolby Vision and HDR10 metadata; both are extracted independently.
- **Subtitle normalisation** — `UTF-8` / `SubRip` → `SRT`; `ASS/SSA/ffdshow` → `ASS`; `HDMV PGS` → `PGS`.
- **Quality fallback** — if no quality token is found in the filename, quality is derived from video stream height.

---

## Changelog

### v2.0
- Full rewrite with modular helper functions
- Full HDR parsing: HDR10, HDR10+, Dolby Vision (with profile), HLG
- Extended audio codec support: FLAC, E-AC-3, E-AC-3 JOC, DTS XLL X, AAC, MP3, Opus, Vorbis
- Extended subtitle support: SRT, ASS, PGS, VobSub, WebVTT
- All video colour metadata fields captured (primaries, transfer, matrix, mastering display, MaxCLL/MaxFALL)
- Expanded source list: DSNP, ATVP, PMTP, PCOK
- Bitrate normalisation handles Mb/s, kb/s, and bare bps integers
- Sampling rate normalisation handles all Hz / kHz variants
- Language code and full language name captured separately per track
- Robust section detection with regex anchors
- Per-file settings option in batch mode

### v1.0
- Initial release
