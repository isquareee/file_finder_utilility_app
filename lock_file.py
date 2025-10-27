"""
lock_file.py - Creates a locked file THEN exits
Run this BEFORE starting the File Organizer app
"""

import os
import sys

# Path to your test folder
TEST_FOLDER = "test-files"

# Create a locked file
locked_file_path = os.path.join(TEST_FOLDER, "LOCKED_FILE.txt")

print("=" * 60)
print("Permission Error Demo - File Locker")
print("=" * 60)

# Check if file already exists and is locked
if os.path.exists(locked_file_path):
    try:
        # Try to open it for writing (will fail if locked)
        with open(locked_file_path, "a") as f:
            pass
        print(f"\n⚠️  File exists but is not locked: {locked_file_path}")
        print("Deleting and recreating...")
        os.remove(locked_file_path)
    except PermissionError:
        print(f"\n✅ File already locked: {locked_file_path}")
        print("You can run the File Organizer now!")
        sys.exit(0)

# Create the locked file
with open(locked_file_path, "w") as f:
    f.write("This file is currently OPEN and cannot be moved!\n")
    f.write("The File Organizer should skip this file gracefully.\n")

print(f"\n✅ Created file: {locked_file_path}")
print("\n" + "=" * 60)
print("NOW LOCK THE FILE MANUALLY:")
print("=" * 60)

if sys.platform == "win32":
    print("\n🪟 WINDOWS - Option 1 (Easy):")
    print("   1. Open File Explorer")
    print(f"   2. Navigate to: {os.path.abspath(TEST_FOLDER)}")
    print("   3. Double-click LOCKED_FILE.txt to open in Notepad")
    print("   4. KEEP NOTEPAD OPEN (don't close it!)")
    print("   5. Now run your File Organizer app")
    print("\n🪟 WINDOWS - Option 2 (Properties):")
    print("   1. Right-click LOCKED_FILE.txt")
    print("   2. Select Properties")
    print("   3. Check 'Read-only' checkbox")
    print("   4. Click OK")
else:
    print("\n🍎 MAC/LINUX:")
    print("   Run this command:")
    print(f"   chmod 444 {locked_file_path}")
    print("\n   Or use this one-liner:")
    print(f"   python -c \"import os; os.chmod('{locked_file_path}', 0o444)\"")

print("\n" + "=" * 60)
print("DEMO STEPS:")
print("=" * 60)
print("1. Lock the file using method above")
print("2. Run: python main.py")
print("3. Browse to 'test-files' folder")
print("4. Click 'Scan Directory'")
print("5. Click 'Organize Checked Files'")
print("6. Watch for Permission Error warning!")
print("\n💡 The app should skip the locked file gracefully")
print("=" * 60)