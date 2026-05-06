# uspend

Shared expense tracker. No accounts, just share the link.
Your groups are stored in local storage.

### [Live demo](https://count.ynn.ovh)

## Features

- **No accounts**. the group URL is the secret.
- **Minimal transactions**. settlement algorithm minimizes the number of transfers
- **i18n**. language auto-detected from browser
- **Lightweight**. runs on a cheap VPS; in-memory for local dev, Redis in production. No frontend libs.
- **Secure**. built-in rate-limiting

## Run locally

```sh
pip install -e ".[dev]"
cd backend && uvicorn main:app --reload
```

Requires Python 3.12+.

## Deploy

```sh
docker compose up -d
```

Set `REDIS_URL` for persistence. Set `RATE_LIMIT` (requests/minute per IP, default 120).

## Stack

FastAPI, Jinja2, Vanilla JS, Redis

## Licence

GPLv3
