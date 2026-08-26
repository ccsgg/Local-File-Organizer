# 📁 Local File Organizer
A lightweight Python script that automatically organizes messy folders by file type, with duplicate protection, locked-file handling, and undo support.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![License](https://img.shields.io/badge/License-MIT-green)

# Features
- Automatically sorts files into categories
- Supports common Documents, Images, Videos, Audio, Archives, Applications and Code
- Handles duplicate filenames without overwriting existing files
- Skips temporary and incomplete downloads such as ```.crdownload``` and ```.part```
- Detects files that are busy or inaccessible and skips them safely
- Keeps a ```history.json``` log to undo the last organization
- Never silently overwrites an existing file

# How it works
Given a folder like:
```
Downloads/ 
├── report.pdf
├── script.js
├── photo.jpg 
├── song.mp3 
├── project.py
├── image.png
└── archive.zip
```
The organizer automatically transforms it into:
```
Downloads/ 
├── Documents/ 
│   └── report.pdf 
├── Images/ 
│   └── photo.jpg
│   └── image.png
├── Audio/ 
│   └── song.mp3 
├── Code/ 
│   └── project.py 
│   └── script.js
└── Archives/ 
    └── archive.zip
```
Unknown or unspecified file types in ```FILE_CATEGORIES``` are moved to:
```
Others/
```
# Installation
Clone the repository:
```
git clone https://github.com/ccsgg/Local-File-Organizer.git
cd Local-File-Organizer
```
No external dependencies are required.
Python 3.9+ is recommended.

# Usage (CLI)
Run:
```python organizee.py```

Choose between 3 options:
```
📁 Local File Organizer
1 - Sort a folder
2 - Undo the last sort
3 - Exit

> 1
```
Then enter the path:
```
Enter the path of the folder to organize: path/to/Downloads

⏳ Sorting path/to/Downloads...\n

✅ Moved X to NewFile/
✅ Moved Y to NewFile/
✅ Moved Z to NewFile/
✅ ...

📁 Processed X file(s).
📝 History saved to ..\history.json - run 'Undo the last sort' to revert this sort.
```

# Screenshot
<img width="1180" height="445" alt="Local File Organizer Demo" src="https://github.com/user-attachments/assets/57d0b10d-da5e-46c4-8f9b-39d17e7a11e4" />

# Configuration
File categories and supported extensions can be customized in ```FILE_CATEGORIES```.

For example:
```
FILE_CATEGORIES = {
    "Documents": [".pdf", ".docx", ".txt"],
    "Images": [".jpg", ".png", ".webp"],
}
```

Temporary extensions can also be configured through:
```
TEMP_EXTENSIONS = {
    ".crdownload",
    ".part",
    ".download",
    ".tmp",
}
```

## Possible future improvements
- Add recursive folder organization
- Add a simple GUI
- Improve cross-platform locked-file detection
