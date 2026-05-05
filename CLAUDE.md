# uspend

Tricount alternative. Slug-based auth (no accounts). Mobile-first. 
Low on resources, must be able to handle hundreds of concurrent users on cheap VPS.
Low-tech, low-complexity, code had to be readable by high school student
Heavily tested.
Not crazy architecture. not too many files, no oop, no complex patterns.

## Commands

```sh
./dev.sh            # run dev server
./dev.sh test       # pytest
./dev.sh lint       # ruff
./dev.sh typecheck  # pyright
```

After every change, run formatter, typecheck, and tests:

```sh
uv run ruff format backend && ./dev.sh lint && ./dev.sh typecheck && ./dev.sh test
```

## Stack

- **Backend:** FastAPI + Jinja2, Python 3.12+
- **Frontend:** Jinja2 templates, vanilla JS, no build step
- **Storage:** in-memory dict by default; Redis when `REDIS_URL` is set
- **i18n:** `i18n/en.json` and `i18n/fr.json` loaded at startup, passed to every template as `t`; language detected from `Accept-Language` header

## Project structure

```
backend/         Python source + tests
frontend/
  templates/     Jinja2 HTML templates
  static/        CSS, JS
i18n/            Translation JSON files (en, fr)
```

## Data model

```
group:    { slug, name, currency, members: [str], spendings: [...] }
spending: { id, paid_by, amount, description, beneficiaries: [str] }
```

## Key design decisions

**Slug-based auth** — no accounts, no passwords. The group URL is the secret. Anyone with the link can add spendings. Identity (who you are in the group) is picked once on first visit and stored in `localStorage`.

**No frontend build** — templates are Jinja2, JS is plain files in `static/`. No npm, no bundler.

**i18n lives in the backend** — translations are loaded server-side and passed to templates as a `t` dict. The frontend never does its own translation lookups. The module is `backend/translations.py` (not `i18n.py`, which conflicts with the `i18n/` directory at repo root).

**Storage is swappable** — `backend/store.py` abstracts get/set. Dev uses a plain dict; production uses Redis via `REDIS_URL`. No ORM, no migrations.

**Settlement algorithm** — minimizes the number of transactions needed to settle all debts. Lives in `backend/algorithm.py`.
