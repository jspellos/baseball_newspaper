# Baseball Newspaper

A local Python project for generating an old-newspaper-style daily MLB page:
completed games from the selected date, box-score summaries, standings, and
traditional season leaders.

## Generate an edition

Generate one static HTML page:

```powershell
python build_newspaper.py --sample
```

The generated page will be written to:

```text
output/daily/sample.html
```

To fetch live MLB data for a specific date:

```powershell
python build_newspaper.py --date 2026-05-29
```

By default, live mode uses yesterday's date.

The generator also maintains:

```text
output/index.html
output/archive.html
```

`index.html` redirects to the latest generated edition. `archive.html` lists
all dated editions.

Generate a printable PDF for an existing dated edition:

```powershell
powershell.exe -ExecutionPolicy Bypass -File ".\export_pdf.ps1" -EditionDate 2026-05-30
```

PDF editions are written to:

```text
output/pdf/
```

## Daily automation

Run the scheduler-friendly wrapper manually:

```powershell
powershell.exe -ExecutionPolicy Bypass -File ".\run_daily.ps1"
```

It generates yesterday's HTML edition, updates the publish-ready `docs/`
folder, and writes a timestamped log under:

```text
output/logs/
```

### Windows Task Scheduler

Create a basic daily task and use:

```text
Program/script:
powershell.exe

Add arguments:
-NoProfile -ExecutionPolicy Bypass -File "C:\Users\jspel\baseball_newspaper\run_daily.ps1"

Start in:
C:\Users\jspel\baseball_newspaper
```

Choose a morning run time after overnight games are likely to be complete.
The wrapper resolves the project directory from its own location, so the
`Start in` field is helpful but not required.

## GitHub Pages

The local daily wrapper copies the clean static website into:

```text
docs/
  index.html
  archive.html
  daily/
```

Logs, cached API responses, and optional PDFs stay local under `output/`.

To publish the site manually after configuring Git:

```powershell
powershell.exe -ExecutionPolicy Bypass -File ".\push_site.ps1"
```

In the GitHub repository, configure Pages:

1. Open `Settings`.
2. Select `Pages` under `Code and automation`.
3. Under `Build and deployment`, select `Deploy from a branch`.
4. Select the `main` branch and the `/docs` folder.
5. Click `Save`.

The hosted site will be:

```text
https://jspellos.github.io/baseball_newspaper/
```

Once the manual push is working reliably, `push_site.ps1` can be called from
the scheduled wrapper to publish each morning automatically.

## Project layout

```text
baseball_newspaper/
  build_newspaper.py
  export_pdf.ps1
  publish_site.ps1
  push_site.ps1
  run_daily.ps1
  docs/
    daily/
  src/
    config.py
    data/
      cache.py
      mlb_api.py
      normalize.py
    render/
      daily_page.py
  templates/
    daily.html
  static/
    newspaper.css
  storage/
    cache/
    raw/
  output/
    daily/
    logs/
    pdf/
```
