"""Filesystem helpers: listing photos, validating paths, and moving files."""

from pathlib import Path

from .models import WorkFolder

# Extensions we treat as reviewable photos (JPEG only, per project scope).
PHOTO_EXTS = {".jpg", ".jpeg"}

# Subdirectory names rated photos are moved into, relative to the photo's parent.
GOOD_DIR = "good"
NOT_GOOD_DIR = "not good"
MAYBE_DIR = "maybe"
RATING_DIRS = {GOOD_DIR, NOT_GOOD_DIR, MAYBE_DIR}

# Maps a MoveLog rating value to the subdirectory photos get moved into.
RATING_TO_DIR = {"good": GOOD_DIR, "not_good": NOT_GOOD_DIR, "maybe": MAYBE_DIR}


def is_photo(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in PHOTO_EXTS


def list_photos(folder_path: str) -> list[str]:
    """Return sorted filenames of reviewable photos directly in folder_path.

    Non-recursive. The good/ and not good/ subdirectories are skipped because
    they hold already-rated photos.
    """
    base = Path(folder_path)
    if not base.is_dir():
        return []
    names = [p.name for p in base.iterdir() if is_photo(p)]
    return sorted(names, key=str.lower)


def count_photos(folder_path: str) -> int:
    return len(list_photos(folder_path))


def known_roots() -> list[Path]:
    """Resolved paths of every WorkFolder, used to authorize file access."""
    return [Path(f.path).resolve() for f in WorkFolder.objects.all()]


def is_within_known_folder(target: Path) -> bool:
    """True if target lives inside (or is) one of the registered work folders.

    Guards image serving and rating so the app can only touch files under
    folders the user explicitly added.
    """
    try:
        target = target.resolve()
    except OSError:
        return False
    for root in known_roots():
        if target == root or root in target.parents:
            return True
    return False


def unique_destination(dest_dir: Path, filename: str) -> Path:
    """A non-colliding path inside dest_dir for filename.

    Appends ' (1)', ' (2)', ... before the extension if needed.
    """
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    n = 1
    while True:
        candidate = dest_dir / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def move_for_rating(photo_path: Path, rating_dir: str) -> Path:
    """Move photo_path into rating_dir inside its parent. Returns the new path."""
    parent = photo_path.parent
    dest_dir = parent / rating_dir
    dest_dir.mkdir(exist_ok=True)
    dest = unique_destination(dest_dir, photo_path.name)
    photo_path.rename(dest)
    return dest
