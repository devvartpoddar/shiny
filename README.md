# shiny

Every Shiny app hosted on yggdrasil, one folder each under `apps/`. The box
serves this repo's `main` checkout at `/ygg/projects/shiny` with Shiny
Server: `apps/<name>/app.py` is `https://apps.<domain>/<name>/`, and the
root lists them.

## Layout

```
apps/<name>/app.py      one app per folder (Shiny for Python, Express style)
apps/<name>/_brand.yml  optional: an app's own look, otherwise the house one
kit/                    what every app shares — page frame, tiles, charts, the database
_brand.yml              the house look (colours, fonts); kit.theme() reads it
pyproject.toml, uv.lock one environment for every app (.venv, built on the box by uv)
.secrets/env            KEY=value lines the apps get as environment (never committed)
```

## Adding an app

1. `mkdir apps/<name>` and write `app.py`. Start from `apps/hello/app.py`:
   `kit.page(...)` first, then tiles, sections and charts from `kit`.
2. Need a library? Add it to `pyproject.toml`, run `uv lock`, commit the lock.
3. Merge to `main`. On the box: `sudo ygg apps sync` (pulls, rebuilds
   `.venv` if the lock moved, restarts every app on its next visit).
4. Share it: a Cloudflare Access application for `apps.<domain>/<name>`
   with the emails that may open it — Dev's, in the Cloudflare dashboard.

The house rules are in `kit` so nobody has to remember them: every tile and
chart is labelled, bars show their values, titles are short, no pies, no
stacked bars. `kit` also has a grid of counts (`heatmap`), a world map from
ISO country codes (`world`), clickable cards and a board of columns
(`card`, `cards`, `board`), and `on_click(input, "<chart id>", fn)`, which
hands a click on any plotly chart to the server (put the key you need in the
trace's customdata).

## Linking an analysis repo

An app imports a project's code, it does not copy it. Once the project repo
has a `pyproject.toml` naming its package, add it here (the WBG one is):

```toml
[project]
dependencies = [..., "wbg_portfolio"]

[tool.uv.sources]
wbg_portfolio = { path = "/ygg/projects/wbg-digital-resilience", editable = true }
```

`uv lock` (the path must exist where you lock: on a laptop or in a cloud
session, link your clone there first), commit, `sudo ygg apps sync`. The app
then does `from wbg_portfolio import app` and runs the live `main` checkout
of that repo: a merge there reaches the app at its next start, with no lock
change. Lock again here only when the project's own dependencies change.

## Keys

What an app needs goes in `.secrets/env` on the box (owned by `ygg-apps`,
mode 0600, one `KEY=value` per line); systemd hands those lines to Shiny
Server, which passes its environment to every app. Example:

```
WBG_OPENROUTER_KEY=sk-...
```

Then `sudo systemctl restart yggdrasil-apps`. Nothing here is ever committed.

## The database

`kit.query_df(sql)` reads `work` (every project's schema) as the `ygg-apps`
role: read on everything the agents made, write only in schema `apps`.
On the box there is no password (peer auth over the socket); on a laptop
set `KIT_DATABASE_URL`.

## Running locally

```
uv sync
uv run shiny run --reload apps/hello/app.py
```

Before saying a page is done, look at it: Claude's `app_screenshot(app)`
returns what the box serves.
