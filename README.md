# Photo Viewer

A fast, keyboard-driven photo culling tool. Runs locally on `localhost`, reads
and moves your JPEGs in place on disk (nothing is copied or uploaded), and
aggressively preloads upcoming images so each rating keypress paints instantly —
no waiting on 20 MB files the way Preview makes you wait.

## Run

```sh
uv run python manage.py migrate      # first time only
uv run python manage.py runserver
```

Then open http://localhost:8000.

## Workflow

1. On the home page, browse your disk and **add** one or more folders to review.
   Folders are non-recursive — only JPEGs directly inside count.
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
   | `J`     | Zoom to 200%                                  |

   When zoomed in, scroll normally to pan; Shift-scroll pans horizontally.

## Notes

- **Storage:** SQLite (`db.sqlite3`) holds only the queued folders and a move
  log for undo. The photo list and counts are read live from disk.
- **Performance:** the next 4 images are fetched and decoded ahead of time, so
  G/N/M advance with no load delay. Tune `PRELOAD_AHEAD` in
  `viewer/templates/viewer/review.html` if you want a deeper buffer.
- **Safety:** the app will only read or move files that live inside a folder you
  explicitly added.
