# Icon Extractor for Windows

A desktop application that extracts icons from running Windows applications and UWP (Universal Windows Platform) apps in real-time.

## Features

- Displays icons from active windows in real-time
- Supports both traditional Win32 applications and UWP apps
- Shows window title and process name
- Right-click menu to save icons as PNG files
- Always stays on top of other windows

## Requirements
- Windows 10 & 11

## Installation
Download the [latest](https://github.com/amnweb/icon-extractor/releases/latest) installer from the releases page

## Winget Installation
```
winget install --id AmN.IconExtractor
```

## Running from source
1. Install Python 3.12 or later
2. Clone this repositorys
3. Install dependencies:
```sh
pip install -r requirements.txt
```
4. Run the application:
```sh
python main.py
```

