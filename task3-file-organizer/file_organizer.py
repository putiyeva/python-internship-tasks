"""Automated File Organizer.

Scans a directory and sorts the files in it into subfolders named after their
extension (``report.pdf`` -> ``pdf/``). Files without an extension go to
``no_extension/``.

Safety rules:
* An existing file at the destination is NEVER overwritten. If the name is
  taken, the incoming file is renamed: ``a.txt`` -> ``a (1).txt`` -> ``a (2).txt``.
* ``--dry-run`` shows exactly what would happen without touching any file.
* One failing file (e.g. missing permissions) never stops the whole run.
"""

import argparse
import logging
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

NO_EXTENSION_FOLDER = "no_extension"
DEFAULT_LOG_FILE = "file_organizer.log"

logger = logging.getLogger("file_organizer")


@dataclass
class MoveResult:
    """Outcome for one file."""

    source: Path
    destination: Optional[Path] = None
    renamed: bool = False
    status: str = "moved"  # moved | would-move | skipped | error
    message: str = ""


# ---------- helpers ----------

def get_folder_name(path: Path) -> str:
    """Return the destination folder name for ``path`` (lower-case extension)."""
    extension = path.suffix.lstrip(".").lower()
    return extension or NO_EXTENSION_FOLDER


def find_destination(
    folder: Path, filename: str, reserved: Set[Path], claim: bool
) -> Tuple[Path, bool]:
    """Find a destination path inside ``folder`` that is guaranteed to be free.

    Returns ``(path, renamed)``. ``renamed`` is True when ``filename`` was
    already taken and a numbered name was chosen instead.

    ``reserved`` holds destinations already chosen earlier in this run (needed
    for dry-run, where nothing is actually created). With ``claim=True`` the
    chosen path is created as an empty file using exclusive mode, so even a
    file appearing at the same moment cannot be overwritten.
    """
    stem, suffix = Path(filename).stem, Path(filename).suffix
    counter = 0
    while True:
        name = filename if counter == 0 else f"{stem} ({counter}){suffix}"
        candidate = folder / name
        if candidate not in reserved and not os.path.lexists(candidate):
            if not claim:
                return candidate, counter > 0
            try:
                with open(candidate, "x"):
                    pass
                return candidate, counter > 0
            except FileExistsError:
                pass  # created by someone else just now, try the next name
        counter += 1


def _prepare_folder(folder: Path, dry_run: bool) -> None:
    """Make sure ``folder`` is a usable real directory (create it unless dry-run)."""
    if folder.is_symlink():
        raise OSError(f"'{folder.name}' is a symbolic link, refusing to use it as a folder")
    if folder.exists() and not folder.is_dir():
        raise OSError(f"a file named '{folder.name}' already exists, cannot create the folder")
    if not dry_run:
        folder.mkdir(exist_ok=True)


# ---------- core ----------

def organize(
    target: Path, dry_run: bool = False, skip: Iterable[Path] = ()
) -> List[MoveResult]:
    """Sort the files directly inside ``target`` into extension folders.

    Hidden files, symbolic links, subfolders and anything listed in ``skip``
    (such as the log file) are left alone.
    """
    target = Path(target)
    if not target.exists():
        raise FileNotFoundError(f"'{target}' does not exist")
    if not target.is_dir():
        raise NotADirectoryError(f"'{target}' is not a directory")
    resolved = target.resolve()
    if resolved == Path(resolved.anchor):
        raise ValueError("refusing to organize a filesystem root")

    skip_paths = {Path(p).resolve() for p in skip}
    results: List[MoveResult] = []
    candidates: List[Path] = []

    for entry in sorted(target.iterdir(), key=lambda p: p.name.lower()):
        if entry.is_symlink():
            results.append(MoveResult(entry, status="skipped", message="symbolic link"))
        elif not entry.is_file():
            continue  # subfolders and special files are ignored silently
        elif entry.name.startswith("."):
            results.append(MoveResult(entry, status="skipped", message="hidden file"))
        elif entry.resolve() in skip_paths:
            results.append(MoveResult(entry, status="skipped", message="log file"))
        else:
            candidates.append(entry)

    if not candidates:
        logger.info("Nothing to organize: no regular files found in %s", target)

    reserved: Set[Path] = set()
    for source in candidates:
        results.append(_move_one(source, target, dry_run, reserved))

    results.sort(key=lambda r: r.source.name.lower())
    return results


def _move_one(
    source: Path, target: Path, dry_run: bool, reserved: Set[Path]
) -> MoveResult:
    folder = target / get_folder_name(source)
    claimed: Optional[Path] = None
    try:
        _prepare_folder(folder, dry_run)
        destination, renamed = find_destination(
            folder, source.name, reserved, claim=not dry_run
        )
        reserved.add(destination)
        if dry_run:
            return MoveResult(source, destination, renamed, "would-move")
        claimed = destination
        shutil.move(str(source), str(destination))
        return MoveResult(source, destination, renamed, "moved")
    except PermissionError as exc:
        _remove_placeholder(claimed, source)
        return MoveResult(source, status="error", message=f"permission denied ({exc})")
    except OSError as exc:
        _remove_placeholder(claimed, source)
        return MoveResult(source, status="error", message=str(exc))


def _remove_placeholder(claimed: Optional[Path], source: Path) -> None:
    """Delete the empty file we reserved if the move failed (never touches the source)."""
    if claimed is not None and source.exists():
        try:
            claimed.unlink()
        except OSError:
            pass


# ---------- reporting ----------

def log_result(result: MoveResult) -> None:
    name = result.source.name
    if result.status in ("moved", "would-move"):
        tag = "MOVED" if result.status == "moved" else "DRY-RUN"
        note = "  (renamed: name already existed)" if result.renamed else ""
        logger.info("[%s] %s: %s -> %s%s", tag, name, result.source, result.destination, note)
    elif result.status == "skipped":
        logger.info("[SKIPPED] %s: %s", name, result.message)
    else:
        logger.error("[ERROR] %s: %s", name, result.message)


def summarize(results: List[MoveResult], dry_run: bool) -> str:
    moved = [r for r in results if r.status in ("moved", "would-move")]
    renamed = sum(1 for r in moved if r.renamed)
    skipped = sum(1 for r in results if r.status == "skipped")
    errors = sum(1 for r in results if r.status == "error")
    verb = "would be moved" if dry_run else "moved"
    return (
        f"Summary: {len(moved)} file(s) {verb} ({renamed} renamed), "
        f"{skipped} skipped, {errors} error(s)."
    )


def setup_logging(log_file: Path) -> List[logging.Handler]:
    """Log to the console (plain) and to ``log_file`` (with timestamps)."""
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for old in list(logger.handlers):
        logger.removeHandler(old)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("%(message)s"))
    handlers: List[logging.Handler] = [console]

    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-7s %(message)s")
        )
        handlers.append(file_handler)
    except OSError as exc:
        print(f"Warning: cannot write log file '{log_file}': {exc}", file=sys.stderr)

    for handler in handlers:
        logger.addHandler(handler)
    return handlers


# ---------- CLI ----------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sort the files in a folder into subfolders by extension. "
        "Existing files are never overwritten."
    )
    parser.add_argument("target", type=Path, help="folder to organize")
    parser.add_argument(
        "--dry-run", action="store_true", help="preview the changes without moving anything"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path(DEFAULT_LOG_FILE),
        help=f"where to write the log (default: {DEFAULT_LOG_FILE})",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = setup_logging(args.log_file)
    try:
        mode = " (dry run, no files will be changed)" if args.dry_run else ""
        logger.info("Organizing %s%s", args.target, mode)
        try:
            results = organize(args.target, dry_run=args.dry_run, skip=[args.log_file])
        except (OSError, ValueError) as exc:
            logger.error("Cannot organize '%s': %s", args.target, exc)
            return 2

        for result in results:
            log_result(result)
        logger.info(summarize(results, args.dry_run))
        return 1 if any(r.status == "error" for r in results) else 0
    finally:
        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())
