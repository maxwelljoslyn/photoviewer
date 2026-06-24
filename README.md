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

## EXIF overlay

A minimizable panel at the bottom-left of `/review` shows the EXIF metadata for
the current photo. Click its header (or press `I`) to expand/collapse it; the
collapsed/expanded state is remembered between sessions. It currently dumps
*every* tag the file carries (main IFD plus the Exif and GPS sub-IFDs) so you
can decide which keys are worth keeping — narrowing the set is a later step.
Metadata is read live from disk via `GET /api/exif?path=…` and is subject to the
same "must live under a registered folder" guard as image serving.

## Notes

- **Storage:** SQLite (`db.sqlite3`) holds only the queued folders and a move
  log for undo. The photo list and counts are read live from disk.
- **Performance:** the next 4 images are fetched and decoded ahead of time, so
  G/N/M advance with no load delay. Tune `PRELOAD_AHEAD` in
  `viewer/templates/viewer/review.html` if you want a deeper buffer.
- **Safety:** the app will only read or move files that live inside a folder you
  explicitly added.
