import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path

DEFAULT_PRINTER = "Kyocera TASKalfa 3501i"
DEFAULT_SLEEP_SECONDS = 1.5


def find_sumatra(explicit_path: str | None) -> str | None:
    if explicit_path:
        p = Path(explicit_path)
        return str(p) if p.is_file() else None

    local_appdata = os.environ.get("LOCALAPPDATA")
    appdata = os.environ.get("APPDATA")
    script_dir = Path(__file__).resolve().parent

    candidates = [
        os.environ.get("SUMATRA_PDF"),
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        str(script_dir / "SumatraPDF.exe"),
        str(Path.cwd() / "SumatraPDF.exe"),
        str(Path.cwd() / "SumatraPDF" / "SumatraPDF.exe"),
        str(script_dir / "SumatraPDF" / "SumatraPDF.exe"),
        str(Path(local_appdata) / "SumatraPDF" / "SumatraPDF.exe") if local_appdata else None,
        str(Path(appdata) / "SumatraPDF" / "SumatraPDF.exe") if appdata else None,
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return c

    which = shutil.which("SumatraPDF.exe") or shutil.which("SumatraPDF")
    return which


def iter_pdfs(folder: Path, recursive: bool):
    if recursive:
        yield from folder.rglob("*.pdf")
    else:
        yield from folder.glob("*.pdf")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print all PDFs in a folder to tabloid, one-sided, fit to printable area."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=str(Path.cwd() / "printing_jobs"),
        help="Folder containing PDFs (default: ./printing_jobs)",
    )
    parser.add_argument(
        "--printer",
        default=DEFAULT_PRINTER,
        help=f"Printer name (default: {DEFAULT_PRINTER})",
    )
    parser.add_argument(
        "--sumatra",
        default=None,
        help="Full path to SumatraPDF.exe (optional if installed in default locations)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Include PDFs in subfolders",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=DEFAULT_SLEEP_SECONDS,
        help="Seconds to wait between print jobs (default: 1.5)",
    )

    args = parser.parse_args()
    folder = Path(args.folder)

    if not folder.is_dir():
        print(f"Error: folder not found: {folder}")
        return 2

    sumatra = find_sumatra(args.sumatra)
    if not sumatra:
        print("Error: SumatraPDF not found.")
        print("Install SumatraPDF or pass --sumatra with the full path to SumatraPDF.exe.")
        return 3

    pdfs = sorted(iter_pdfs(folder, args.recursive))
    if not pdfs:
        print("No PDFs found.")
        return 0

    print(f"Using printer: {args.printer}")
    print(f"SumatraPDF: {sumatra}")
    print(f"PDF count: {len(pdfs)}")

    # Sumatra settings: fit to printable area, tabloid paper, one-sided
    print_settings = "fit,paper=tabloid,duplex=off"

    failures = 0
    for pdf in pdfs:
        print(f"Printing: {pdf}")
        cmd = [
            sumatra,
            "-print-to",
            args.printer,
            "-print-settings",
            print_settings,
            "-silent",
            str(pdf),
        ]
        try:
            completed = subprocess.run(cmd, check=False)
            if completed.returncode != 0:
                failures += 1
                print(f"Failed: {pdf} (exit {completed.returncode})")
        except Exception as e:
            failures += 1
            print(f"Failed: {pdf} ({e})")

        time.sleep(args.sleep)

    if failures:
        print(f"Done with {failures} failure(s).")
        return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
