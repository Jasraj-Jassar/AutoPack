import argparse
import re
import shutil
from pathlib import Path


def iter_pdfs(folder: Path, recursive: bool):
    if recursive:
        yield from folder.rglob("*.pdf")
    else:
        yield from folder.glob("*.pdf")


def safe_folder_name(name: str) -> str:
    # Keep it Windows-safe.
    return re.sub(r"[<>:\"/\\\\|?*]", "_", name).strip().rstrip(".")


def move_pdf(pdf: Path, dest_folder: Path):
    dest_folder.mkdir(parents=True, exist_ok=True)
    dest_path = dest_folder / pdf.name
    if dest_path.exists():
        stem = pdf.stem
        suffix = pdf.suffix
        i = 1
        while True:
            candidate = dest_folder / f"{stem} ({i}){suffix}"
            if not candidate.exists():
                dest_path = candidate
                break
            i += 1
    shutil.move(str(pdf), str(dest_path))
    return dest_path


def get_job_from_parts_txt(parts_txt: Path) -> str | None:
    if not parts_txt.is_file():
        return None
    for line in parts_txt.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip().lower().startswith("job:"):
            return line.split(":", 1)[1].strip() or None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Move PDFs from insert-traveler and printing_jobs into Job-named folders at repo root."
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Include PDFs in subfolders",
    )
    args = parser.parse_args()

    root = Path.cwd()
    insert_traveler = root / "insert-traveler"
    printing_jobs = root / "printing_jobs"
    sources = [insert_traveler, printing_jobs]

    job = get_job_from_parts_txt(insert_traveler / "parts.txt")
    if not job:
        print("Error: Could not find Job in insert-traveler\\parts.txt")
        return 2

    history_root = root / "History"
    dest_folder = history_root / safe_folder_name(f"Job - {job}")

    moved = 0
    for src in sources:
        if not src.exists():
            continue
        for pdf in iter_pdfs(src, args.recursive):
            move_pdf(pdf, dest_folder)
            moved += 1

    print(f"Job folder: {dest_folder}")
    print(f"Moved: {moved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
