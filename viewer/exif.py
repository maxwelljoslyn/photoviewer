"""Extract EXIF metadata from a photo for the review overlay.

We pull *everything* the file carries (the main IFD plus the Exif and GPS
sub-IFDs) and coerce each value into something json.dumps can handle. The
overlay is a debugging aid, so unknown tags are surfaced by their hex id
rather than dropped.
"""

from pathlib import Path

from PIL import ExifTags, Image, TiffImagePlugin

# Long byte/string blobs (e.g. MakerNote) are useless in the overlay and can be
# huge; truncate them so the panel stays readable.
_MAX_LEN = 200


def _jsonable(value):
    """Coerce an EXIF value into a JSON-serializable form."""
    if isinstance(value, TiffImagePlugin.IFDRational):
        # Malformed rationals can have a zero denominator; don't crash on them.
        return float(value) if value.denominator else None
    if isinstance(value, bytes):
        text = value.decode("utf-8", "replace").rstrip("\x00")
        return text[:_MAX_LEN] + "…" if len(text) > _MAX_LEN else text
    if isinstance(value, (tuple, list)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, str) and len(value) > _MAX_LEN:
        return value[:_MAX_LEN] + "…"
    return value


def read_exif(path: Path) -> dict:
    """Return all EXIF tags from path as a {name: value} dict (JSON-safe)."""
    with Image.open(path) as img:
        exif = img.getexif()

    out: dict = {}

    def add(tagmap, items):
        for tag_id, value in items.items():
            name = tagmap.get(tag_id, "0x%04x" % tag_id)
            out[name] = _jsonable(value)

    add(ExifTags.TAGS, exif)
    for ifd_id, tagmap in (
        (ExifTags.IFD.Exif, ExifTags.TAGS),
        (ExifTags.IFD.GPSInfo, ExifTags.GPSTAGS),
    ):
        try:
            ifd = exif.get_ifd(ifd_id)
        except Exception:
            continue
        if ifd:
            add(tagmap, ifd)

    return out


# ---------------------------------------------------------------------------
# GPS → place name (fully offline)
# ---------------------------------------------------------------------------


def _to_decimal(dms, ref) -> float | None:
    """Convert a (deg, min, sec) EXIF triple + N/S/E/W ref to signed decimal."""
    if not isinstance(dms, (list, tuple)) or len(dms) != 3:
        return None
    try:
        deg, minute, sec = (float(x) for x in dms)
    except (TypeError, ValueError):
        return None
    dec = deg + minute / 60 + sec / 3600
    return -dec if ref in ("S", "W") else dec


def coordinates(exif: dict) -> tuple[float, float] | None:
    """(lat, lon) in decimal degrees from a read_exif() dict, or None."""
    lat = _to_decimal(exif.get("GPSLatitude"), exif.get("GPSLatitudeRef"))
    lon = _to_decimal(exif.get("GPSLongitude"), exif.get("GPSLongitudeRef"))
    if lat is None or lon is None:
        return None
    # Cameras without a fix sometimes record (0, 0); treat that as no location.
    if lat == 0 and lon == 0:
        return None
    return (lat, lon)


def describe_location(lat: float, lon: float) -> str | None:
    """Nearest 'City, Region, CC' for a coordinate, via the offline dataset.

    Imported lazily: reverse_geocoder builds a k-d tree of ~150k cities on first
    use (a one-time cost on the dev server), so we don't pay for it at startup.
    """
    import reverse_geocoder

    results = reverse_geocoder.search([(lat, lon)], mode=1)
    if not results:
        return None
    r = results[0]
    parts = [r.get("name"), r.get("admin1"), r.get("cc")]
    return ", ".join(p for p in parts if p) or None
