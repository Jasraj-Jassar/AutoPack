import argparse
import re
from pathlib import Path


def extract_first_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?i)\b{re.escape(label)}\s*:\s*([^\r\n]+)", text)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def extract_first_part(text: str) -> str | None:
    # First "Part:" on the page wins.
    value = extract_first_value(text, "Part")
    if not value:
        return None

    # If multiple parts are listed, keep the first segment.
    if "/" in value:
        value = value.split("/", 1)[0].strip()

    return value or None


def extract_first_asm(text: str) -> str | None:
    return extract_first_value(text, "Asm")


def extract_first_job(text: str) -> str | None:
    return extract_first_value(text, "Job")


def iter_pdfs(folder: Path, recursive: bool):
    if recursive:
        yield from folder.rglob("*.pdf")
    else:
        yield from folder.glob("*.pdf")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract the first Part: value from each page of PDFs."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=str(Path.cwd() / "insert-traveler"),
        help="Folder with PDFs or a single PDF file (default: ./insert-traveler)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Include PDFs in subfolders",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output file (default: parts.txt in the input folder)",
    )
    args = parser.parse_args()

    try:
        from pypdf import PdfReader
    except Exception:
        print("Missing dependency: pypdf")
        print("Install with: python -m pip install -r requirements.txt")
        return 2

    input_path = Path(args.input)
    if input_path.is_file():
        pdfs = [input_path]
        output_path = Path(args.output) if args.output else input_path.parent / "parts.txt"
    else:
        if not input_path.is_dir():
            print(f"Error: input not found: {input_path}")
            return 2
        pdfs = sorted(iter_pdfs(input_path, args.recursive))
        output_path = Path(args.output) if args.output else input_path / "parts.txt"

    if not pdfs:
        print("No PDFs found.")
        return 0

    rows: list[str] = []
    for pdf in pdfs:
        reader = PdfReader(str(pdf))
        file_rows: list[str] = []
        job_value: str | None = None
        last_part: str | None = None
        last_asm: str | None = None
        range_start: int | None = None
        range_end: int | None = None

        def flush_range():
            if last_part is None or range_start is None or range_end is None:
                return
            if range_start == range_end:
                page_label = f"Page {range_start}"
            else:
                page_label = f"Page {range_start}-{range_end}"
            file_rows.append(f"{page_label}  Asm: {last_asm or ''}  Part: {last_part}")

        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if job_value is None:
                job_value = extract_first_job(text) or None
            part = extract_first_part(text)
            if not part:
                continue
            asm = extract_first_asm(text) or ""
            if last_part is None:
                last_part = part
                last_asm = asm
                range_start = idx
                range_end = idx
                continue

            if part == last_part and asm == last_asm and range_end is not None:
                range_end = idx
                continue

            flush_range()
            last_part = part
            last_asm = asm
            range_start = idx
            range_end = idx

        flush_range()

        if file_rows:
            if job_value:
                rows.append(f"Job: {job_value}")
            rows.append(f"File: {pdf.name}")
            rows.extend(file_rows)
            rows.append("")

    if not rows:
        print("No Part: values found.")
        return 0

    output_text = "\n".join(rows).rstrip() + "\n"
    output_path.write_text(output_text, encoding="utf-8")
    print(f"Wrote {len(rows)} line(s) to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
