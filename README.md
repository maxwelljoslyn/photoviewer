# Photo Viewer

A fast, keyboard-driven photo culling tool. Runs locally, reads and moves your JPEGs in place on disk, and aggressively preloads upcoming images so each rating keypress paints instantly.

## Run

```sh
uv run python manage.py migrate      # first time only
uv run python manage.py runserver 9000
```

Then open http://localhost:9000.

## Workflow

1. On the home page, browse your disk and **add** one or more folders to review.
   Folders are non-recursive: only JPEGs directly inside count.
2. Click **Start reviewing** (or just go to `/review`). It works through every
   queued folder automatically; you never pick files or IDs by hand.
3. Rate with the keyboard. Rated photos are moved into a subdirectory of their
   own folder:

   | Key     | Action                                       |
   |---------|----------------------------------------------|
   | `G`     | Good → moves photo into `good/`              |
   | `N`     | Not good → moves photo into `not good/`      |
   | `M`     | Maybe → moves photo into `maybe/`            |
   | `U`     | Undo the last move (works across restarts)   |
   | `0`     | Reset zoom to fit the whole photo            |
   | `Space` | Zoom in another 25%                           |
   | `J`     | Zoom in another 100%                          |
   | `K`     | Zoom out 100% (never below fit)              |
   | `I`     | Toggle the EXIF overlay (bottom-left)        |

   Zoom is anchored to the center of the viewport so it expands around whatever
   you're looking at. Arrow keys scroll the image.

   When zoomed in, scroll normally to pan; Shift-scroll pans horizontally.

## Browsing rated photos

Each queued folder on the home page has **Browse** links for its `good/`,
`maybe/` and `not good/` subfolders. They open the same viewer in browse mode
(`/review?folder=<path>`): no rating, just flipping through the photos in
filename order with the same preloading, zoom and EXIF overlay.

| Key     | Action                                       |
|---------|----------------------------------------------|
| `←`/`→` | Previous / next photo                        |
| `↑`/`↓` | Scroll the image                             |
| `S`     | Star / unstar the photo                      |
| `T`     | Toggle the thumbnail strip                   |

The other zoom/EXIF keys work as in review mode. Only folders inside a queued
folder can be browsed, so keep a folder queued if you want to browse its
results later.

The thumbnail strip above the status bar shows the photos currently loaded in
memory around the current one (2 behind, 4 ahead); click one to jump to it.
Its on/off state is remembered between sessions.

## Stars

Stars mark standouts independently of rating: `S` works in review mode and
browse mode, on a photo in any folder. Use them to pick the handful worth
posting out of a `good/` folder, or to flag a `maybe/` or `not good/` photo for
a second look. A star stays with its photo when rating or undo moves the file
(moves made outside the app lose the star).

The home page shows a **★ Starred** link that browses every starred photo
across all folders, and each browse link shows how many of its photos are
starred. Stars live in SQLite alongside the move log, so run `migrate` after
pulling this change.

## EXIF overlay

A minimizable panel at the bottom-left of `/review` shows the EXIF metadata for
the current photo. Click its header (or press `I`) to expand/collapse it; the
collapsed/expanded state is remembered between sessions. It currently dumps
*every* tag the file carries (main IFD plus the Exif and GPS sub-IFDs).
Metadata is read live from disk via `GET /api/exif?path=…` and is subject to the
same "must live under a registered folder" constraint as image serving.

## Notes

- **Storage:** SQLite (`db.sqlite3`) holds only the queued folders and a move
  log for undo. The photo list and counts are read live from disk.
- **Performance:** the next 4 images are fetched and decoded ahead of time, so
  G/N/M advance with no load delay. Tune `PRELOAD_AHEAD` in
  `viewer/templates/viewer/review.html` if you want a deeper buffer.
- **Safety:** the app will only read or move files that live inside a folder you
  explicitly added.
