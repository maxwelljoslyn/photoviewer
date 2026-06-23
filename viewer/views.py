"""Views: folder management, the review UI, and the JSON API it drives."""

import json
from pathlib import Path
from urllib.parse import quote

from django.http import FileResponse, Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import photos
from .exif import coordinates, describe_location, read_exif
from .models import MoveLog, WorkFolder


# ---------------------------------------------------------------------------
# Folder ordering / queue construction
# ---------------------------------------------------------------------------


def _ordered_folders():
    """Folders in the order we work through them (oldest queued first)."""
    return WorkFolder.objects.order_by("created_at")


def _photo_entry(folder: WorkFolder, name: str) -> dict:
    abspath = str(Path(folder.path) / name)
    return {
        "path": abspath,
        "name": name,
        "folder": folder.label or folder.path,
        "url": reverse("image") + "?path=" + quote(abspath),
    }


def _build_queue() -> list[dict]:
    """Every remaining photo across all folders, in review order."""
    queue = []
    for folder in _ordered_folders():
        for name in photos.list_photos(folder.path):
            queue.append(_photo_entry(folder, name))
    return queue


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


def index(request):
    folders = []
    for f in WorkFolder.objects.order_by("-created_at"):
        folders.append({"obj": f, "remaining": photos.count_photos(f.path)})
    total = sum(f["remaining"] for f in folders)
    return render(
        request,
        "viewer/index.html",
        {"folders": folders, "total_remaining": total},
    )


def review(request):
    return render(request, "viewer/review.html")


# ---------------------------------------------------------------------------
# Folder management API
# ---------------------------------------------------------------------------


@require_POST
def add_folder(request):
    path = (request.POST.get("path") or "").strip()
    label = (request.POST.get("label") or "").strip()
    if not path:
        return HttpResponseBadRequest("path is required")
    resolved = Path(path).expanduser()
    if not resolved.is_dir():
        return HttpResponseBadRequest("Not a directory: %s" % path)
    WorkFolder.objects.get_or_create(path=str(resolved), defaults={"label": label})
    return redirect("index")


@require_POST
def delete_folder(request, folder_id):
    get_object_or_404(WorkFolder, pk=folder_id).delete()
    return redirect("index")


# Where the folder picker opens by default.
DEFAULT_BROWSE_ROOT = Path(
    "/Users/maxwelljoslyn/Pictures/All_Personal_Pictures/camera-pics-2023-onward"
)


def browse(request):
    """List subdirectories of a path for the folder-picker UI."""
    raw = request.GET.get("path", "")
    if raw:
        here = Path(raw).expanduser()
    elif DEFAULT_BROWSE_ROOT.is_dir():
        here = DEFAULT_BROWSE_ROOT
    else:
        here = Path.home()
    here = here.resolve()
    if not here.is_dir():
        return JsonResponse({"error": "Not a directory"}, status=400)
    dirs = []
    try:
        for child in sorted(here.iterdir(), key=lambda p: p.name.lower()):
            if child.is_dir() and not child.name.startswith("."):
                dirs.append({"name": child.name, "path": str(child)})
    except PermissionError:
        return JsonResponse({"error": "Permission denied"}, status=403)
    parent = str(here.parent) if here.parent != here else None
    return JsonResponse(
        {
            "path": str(here),
            "parent": parent,
            "dirs": dirs,
            "photo_count": photos.count_photos(str(here)),
        }
    )


# ---------------------------------------------------------------------------
# Review API
# ---------------------------------------------------------------------------


def photo_queue(request):
    queue = _build_queue()
    return JsonResponse({"photos": queue, "total": len(queue)})


def image(request):
    """Stream a JPEG, but only if it lives under a registered work folder."""
    raw = request.GET.get("path", "")
    if not raw:
        raise Http404("no path")
    target = Path(raw)
    if not photos.is_within_known_folder(target) or not target.is_file():
        raise Http404("not found")
    return FileResponse(open(target, "rb"), content_type="image/jpeg")


def exif(request):
    """Return all EXIF metadata for a photo under a registered work folder."""
    raw = request.GET.get("path", "")
    if not raw:
        raise Http404("no path")
    target = Path(raw)
    if not photos.is_within_known_folder(target) or not target.is_file():
        raise Http404("not found")
    try:
        data = read_exif(target)
    except Exception as e:  # corrupt/odd files shouldn't break the overlay
        return JsonResponse({"exif": {}, "error": str(e)})
    resp = {"exif": data}
    coords = coordinates(data)
    if coords:
        resp["coords"] = {"lat": coords[0], "lon": coords[1]}
        try:
            resp["location"] = describe_location(*coords)
        except Exception:
            resp["location"] = None
    return JsonResponse(resp)


@require_POST
def rate(request):
    data = json.loads(request.body or "{}")
    raw_path = data.get("path", "")
    rating = data.get("rating", "")
    if rating not in photos.RATING_TO_DIR:
        return HttpResponseBadRequest("invalid rating")

    src = Path(raw_path)
    if not photos.is_within_known_folder(src) or not src.is_file():
        return HttpResponseBadRequest("photo not found")

    folder = _folder_for(src)
    if folder is None:
        return HttpResponseBadRequest("no work folder owns this photo")

    dest = photos.move_for_rating(src, photos.RATING_TO_DIR[rating])
    MoveLog.objects.create(
        folder=folder,
        src_path=str(src),
        dest_path=str(dest),
        rating=rating,
    )
    return JsonResponse({"ok": True})


@require_POST
def undo(request):
    last = MoveLog.objects.filter(undone=False).order_by("-created_at").first()
    if last is None:
        return JsonResponse({"ok": False, "reason": "nothing to undo"})
    dest = Path(last.dest_path)
    src = Path(last.src_path)
    if dest.is_file():
        # Restore to the original location (re-resolving collisions just in case).
        restored = photos.unique_destination(src.parent, src.name)
        dest.rename(restored)
        restored_path = str(restored)
    else:
        restored_path = last.src_path
    last.undone = True
    last.save(update_fields=["undone"])
    entry = _photo_entry(last.folder, Path(restored_path).name)
    return JsonResponse({"ok": True, "photo": entry})


def _folder_for(photo_path: Path) -> WorkFolder | None:
    """Find the work folder that directly contains photo_path."""
    parent = str(photo_path.parent)
    for f in WorkFolder.objects.all():
        if str(Path(f.path)) == parent:
            return f
    return None
