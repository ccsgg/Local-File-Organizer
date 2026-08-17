import shutil
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime

# add more file extensions if some are missing
FILE_EXTENSIONS = {
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".ppt", ".pptx", ".csv", ".md", ".rtf", ".xls", ".ods"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".bmp", ".webp"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".flv"],
    "Audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg"],
    "Archives": [".zip", ".rar", ".tar", ".gz", ".7z"],
    "Applications": [".exe", ".msi", ".dmg", ".iso", ".apk"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".yml", ".yaml"],
}
INCOMPLETE_DOWNLOAD_EXTENSIONS = {".crdownload", ".part", ".partial", ".download", ".tmp", ".temp"}
HISTORY_FILENAME = "history.json"

# returns the SHA256 hash of a file to compare and avoid duplicates 
def get_file_hash(path: Path, chunk_size = 65536) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# checks if two files are identical by comparing their sizes and hashes
def files_are_identical(path1: Path, path2: Path) -> bool:
    try:
        if path1.stat().st_size != path2.stat().st_size: # first check file sizes to avoid unnecessary hashing
            return False
        return get_file_hash(path1) == get_file_hash(path2)
    except OSError:
        return False

def get_unique_destination(destination_folder: Path, file_name: str) -> Path:
    destination = destination_folder / file_name
    if not destination.exists():
        return destination
    
    stem = Path(file_name).stem
    suffix = Path(file_name).suffix
    counter = 1
    while True:
        candidate_name = destination_folder / f"{stem} ({counter}){suffix}"
        if not candidate_name.exists():
            return candidate_name
        counter += 1
        
def is_file_locked_or_incomplete(file_path: Path, stability_wait_time: float = 0.3):
    ext = file_path.suffix.lower()
    name = file_path.name.lower()
    
    if ext in INCOMPLETE_DOWNLOAD_EXTENSIONS:
        return True, "File has an incomplete download extension."
    
    if name.startswith("~$") or name.startswith(".~lock."):
        return True, "File is likely locked by an other application (e.g., Microsoft Office...)."
    
    try:
        stat_before = file_path.stat()
    except OSError:
        return True, "File is inaccessible (permission denied or locked)."
    
    if time.time() - stat_before.st_mtime < 5:  # file modified in the last 5 seconds
        time.sleep(stability_wait_time)
        try:
            stat_after = file_path.stat()
        except OSError:
            return True, "File is inaccessible (permission denied or locked)."
        if stat_before.st_size != stat_after.st_size:
            return True, "File size is changing, likely being written to."
    
    return False, None # file is not locked or incomplete

def save_history(parent_folder: Path, moves: list):
    history_file = parent_folder / HISTORY_FILENAME
    with open(history_file, "w", encoding="utf-8") as file: # open in write mode to overwrite the history file each time to keep it up to date
        json.dump(moves, file, indent=2, ensure_ascii=False) # convert moves to JSON and write to file with indentation for better readability
        
def undo_last_sort(target_path: str):
    parent_folder = Path(target_path)
    history_file = parent_folder / HISTORY_FILENAME
    
    if not history_file.exists():
        print(f"❌ No history file found in {parent_folder} - cannot undo.")
        return
    
    with open(history_file, "r", encoding="utf-8") as file:
        moves = json.load(file)
        
    if not moves:
        print(f"❌ No moves recorded in history - nothing to undo.")
        return
    
    print(f"⏳ Undoing last sort in {parent_folder}...\n")
    restored_files = 0
    errors = 0
    
    for entry in reversed(moves):
        current_path = Path(entry["destination"])
        original_path = Path(entry["source"])
        
        if not current_path.exists():
            print(f"❌ File {current_path} does not exist - cannot restore.")
            errors += 1
            continue
        
        original_path.parent.mkdir(parents=True, exist_ok=True)  # ensure the original directory exists
        
        if original_path.exists():
            original_path = get_unique_destination(original_path.parent, original_path.name)
            
        try:
            shutil.move(str(current_path), str(original_path))
            print(f"✅ Restored {current_path.name} to {original_path}")
            restored_files += 1
        except OSError as e:
            print(f"❌ Error occurred while restoring {current_path.name}: {e}")
            errors += 1
                
    known_folders = set(FILE_EXTENSIONS.keys()) | {"Others"}
    for folder in parent_folder.iterdir():
        if folder.is_dir() and folder.name in known_folders:
            try:
                folder.rmdir()
                print(f"🗑️ Removed empty folder {folder}")
            except OSError as e:
                pass  # Folder not empty or other error, ignore for now
    try: 
        history_file.unlink(missing_ok=True)  # remove the history file after undoing
    except OSError as e:
        print(f"⚠️ Cannot delete {HISTORY_FILENAME} : {e}")
            
    print(f"\n✅📁 Restored {restored_files} files. {errors} errors occurred during restoration.")
        
def organize_folder(target_path):
    parent_folder = Path(target_path)
    
    if not parent_folder.exists():
        print(f"❌ Folder {target_path} doesn't exist.")
        return
    
    print(f"⏳ Sorting {parent_folder}...\n")
    
    files_processed = 0
    duplicates_skipped = 0
    locked_skipped = 0
    moves_log = []
    
    for element in list(parent_folder.iterdir()):
        if element.is_dir():
            continue
        
        if element.name == HISTORY_FILENAME:
            continue
        
        locked, reason = is_file_locked_or_incomplete(element)
        if locked:
            print(f"⏸️ Skipped ({reason}): {element.name}")
            locked_skipped += 1
            continue
        
        extension = element.suffix.lower()
        category = "Others"
        for ctg, extensions in FILE_EXTENSIONS.items():
            if extension in extensions:
                category = ctg
                break
            
        destination_folder = parent_folder / category
        destination_folder.mkdir(exist_ok=True)
        destination_path = destination_folder / element.name
        
        if destination_path.exists():
            if files_are_identical(element, destination_path):
                print(f"⏭️ Duplicate ignored (identical file already exists): {element.name}")
                duplicates_skipped += 1
                continue
            
            destination_path = get_unique_destination(destination_folder, element.name)
            print(f"♻️ Name already used, renamed to: {destination_path.name}")
            
        try:
            source_str = str(element)
            shutil.move(source_str, str(destination_path))
            print(f"✅ Moved {element.name} to {category}/")
            moves_log.append({
                "source": source_str,
                "destination": str(destination_path),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            })
            files_processed += 1
        except OSError as e:
            print(f"⚠️ Could not move {element.name} (locked?): {e}")
            locked_skipped += 1
            
        if moves_log:
            save_history(parent_folder, moves_log)
            
    print(f"📁 Processed {files_processed} file(s).")
    if duplicates_skipped:
        print(f"⏭️ {duplicates_skipped} duplicate(s) ignored.")
    if locked_skipped:
        print(f"⏭️ {locked_skipped} file(s) skipped (locked/incomplete).")
    if moves_log:
        print(f"📝 History saved to {parent_folder / HISTORY_FILENAME} - run undo to revert this sort.\n")
            
if __name__ == "__main__":
    print("File Organizer")
    print("1. Sort a folder")
    print("2. Undo the last sort")
    choice = input("Choice (1/2): ").strip()
    
    if choice == "2":
        target_path = input("Path of the folder to restore: ").strip()
        undo_last_sort(target_path)
    else:
        target_path = input("Enter the path of the folder to organize: ").strip()
        organize_folder(target_path)