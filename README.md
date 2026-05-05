# envault

> Encrypted `.env` file manager with per-environment secret rotation support.

---

## Installation

```bash
pip install envault
```

---

## Usage

Initialize a new encrypted vault for your project:

```bash
envault init --env production
```

Add and encrypt a secret:

```bash
envault set DATABASE_URL "postgres://user:pass@host/db" --env production
```

Retrieve and inject secrets into your shell environment:

```bash
envault run --env production -- python app.py
```

Rotate secrets for a specific environment:

```bash
envault rotate --env staging
```

Export decrypted values to a plain `.env` file (use with caution):

```bash
envault export --env development --output .env.local
```

Secrets are stored in an encrypted `.envault` file and can be safely committed to version control. Each environment maintains its own encryption key, stored separately in `~/.envault/keys/`.

---

## Project Structure

```
.envault          # Encrypted secrets file (safe to commit)
.envault.lock     # Environment metadata and key references
```

---

## Requirements

- Python 3.8+
- `cryptography` >= 41.0

---

## License

This project is licensed under the [MIT License](LICENSE).