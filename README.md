# hookdrop

Lightweight webhook receiver with request inspection, replay, and filtering built for local development.

---

## Installation

```bash
pip install hookdrop
```

Or install from source:

```bash
git clone https://github.com/yourname/hookdrop.git && cd hookdrop && pip install -e .
```

---

## Usage

Start a local webhook receiver on port 9000:

```bash
hookdrop listen --port 9000
```

hookdrop will print an inspection URL and begin logging incoming requests:

```
Listening on http://localhost:9000
Inspect requests at http://localhost:9000/__hookdrop__

[POST] /webhook  200  12ms  {"event": "push", "repo": "myproject"}
```

**Replay a captured request:**

```bash
hookdrop replay --id req_4f2a1c
```

**Filter requests by path or method:**

```bash
hookdrop listen --port 9000 --filter-path /webhook --filter-method POST
```

**Forward requests to your local app:**

```bash
hookdrop listen --port 9000 --forward http://localhost:3000/webhook
```

---

## Features

- Instant local endpoint — no tunneling required
- Full request inspection (headers, body, timing)
- One-command replay of any captured request
- Path and method filtering
- Optional forwarding to a local target URL

---

## License

MIT © 2024 Your Name