"""Build a stand-alone Windows program with PyInstaller.

    python -m pip install pyinstaller
    python build_exe.py

The result is the folder dist/AdventureEngine, holding AdventureEngine.exe,
the adventures folder and the authoring guide. Copy the whole folder to
another computer; it doesn't need Python installed.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist" / "AdventureEngine"


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller isn't installed. First run:\n\n"
              "    python -m pip install pyinstaller\n")
        return 1

    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
        "--name", "AdventureEngine",
        "--distpath", str(OUT),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        str(ROOT / "adventure.pyw"),
    ], cwd=ROOT, check=True)

    # The program looks for these next to the .exe.
    shutil.copytree(ROOT / "adventures", OUT / "adventures", dirs_exist_ok=True)
    (OUT / "docs").mkdir(exist_ok=True)
    for name in ("AUTHORING.md", "notepadpp-adv.xml"):
        shutil.copy2(ROOT / "docs" / name, OUT / "docs" / name)

    print(f"\nDone! Copy this whole folder to share the game:\n    {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
