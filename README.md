# V2A Converter

A simple Video to Audio converter with drag & drop support.

## Features
- Convert videos to MP3, WAV, FLAC, AAC, OGG
- Drag & drop files into the app
- Batch conversion support
- Progress tracking with ETA
- Custom quality settings

## Quick Start

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Install FFmpeg
Download FFmpeg from https://ffmpeg.org and place `ffmpeg.exe` in the `ffmpeg/` folder.

### 3. Run the App
```bash
python V2A_Converter.py
```

## Building Executable

To create a standalone executable:

### Using PyInstaller
```bash
pip install pyinstaller
```
```
pyinstaller --onefile --windowed --add-data "fonts;fonts" --add-data "ffmpeg;ffmpeg" V2A_Converter.py
```

The executable will be in the `dist/` folder.

## Usage
1. Add video files (drag & drop or use buttons)
2. Select output folder and audio format
3. Choose quality setting
4. Click "Start Conversion"

## Troubleshooting
- **FFmpeg not found?** Check if `ffmpeg.exe` is in the `ffmpeg/` folder
- **Font issues?** App will use system fonts if custom font is missing
- **Permission errors?** Run as administrator or check folder permissions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
