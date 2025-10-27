# config.py

FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx"],
    "Audio": [".mp3", ".wav", ".aac", ".flac"]
}

# Optional regex-based smart rules. Each key is a category name and the value
# is a list of regular expressions. If a filename matches a regex it will be
# categorized into the corresponding category. These are applied after the
# extension-based mapping.
REGEX_RULES = {
    # simple date-like patterns often used in documents/backups
    "Documents": [r"\b\d{4}[-_]\d{2}[-_]\d{2}\b", r"\b\d{2}[-_]\d{2}[-_]\d{4}\b"],
}
