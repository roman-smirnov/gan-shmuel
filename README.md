# Gan Shmuel Project

## 🚀 Running the Project

All services are managed via the `run.sh` helper script in the **project root**.

```bash
# Start stacks (implicit "up" command)
./run.sh [--build|-b] (--prod|-p | --test|-t)

# Stop stacks
./run.sh down (--prod|-p | --test|-t | --all)
```

You **must** choose exactly one mode (`--prod` or `--test`) when starting,
and for `down` you can target one mode or `--all`.

---

### 🎛️ Command-line Options

| Flag / Command   | Description                                              |
|------------------|----------------------------------------------------------|
| `-p`, `--prod`   | Use the **production** stack (`project: prod`)           |
| `-t`, `--test`   | Use the **test** stack (`project: test`)                 |
| `--all`          | With `down`, stop **both** prod and test stacks          |
| `-b`, `--build`  | Rebuild images before starting (`docker compose up --build`) |
| `-h`, `--help`   | Show usage and exit                                      |
| `down`           | Subcommand: stop one or both stacks                      |

---

### 🟢 Starting a Stack

```bash
# Production
./run.sh --prod
./run.sh -p

# Test
./run.sh --test
./run.sh -t

# With rebuild
./run.sh --prod --build
./run.sh -p -b
./run.sh --test --build
./run.sh -t -b
```

---

### 🛑 Stopping Services

Use the `down` subcommand to stop services managed by `run.sh`:

```bash
# Stop only the production stack
./run.sh down --prod

# Stop only the test stack
./run.sh down --test

# Stop both stacks (prod + test)
./run.sh down --all
```

> ℹ️ The script runs `docker compose down` **without** `-v`, so named volumes
> (databases, etc.) are preserved.  
> If you want to also remove volumes, you can run manually:
>
> ```bash
> docker compose -p prod down -v
> docker compose -p test down -v
> ```

---

### 🌐 What the script actually does

On every run, the script:

1. `cd`’s into the directory containing `run.sh`.
2. Exports `PROJECT_ROOT` to that directory.
3. Parses your command and flags:
   - default command: `up`
   - optional explicit command: `up` or `down`
4. Sets mode-specific environment variables (`DEVOPS_PORT`, `WEIGHT_PORT`, etc.).
5. Depending on the command:

   **For `up` (default):**

   ```bash
   docker compose -p <prod|test> up [--build] -d
   ```

   Example:

   ```bash
   Running command: docker compose -p prod up --build -d
   ```

   **For `down`:**

   - `down --prod` → `docker compose -p prod down`
   - `down --test` → `docker compose -p test down`
   - `down --all`  → runs `down` for both `prod` and `test`

   Example:

   ```bash
   Running command: docker compose -p test down
   ```

---

### 🌍 Environment per mode

These environment variables are exported **before** `docker compose` is invoked,
so they can be used in your compose files (for `ports:`, `environment:`, etc.).

#### Production mode (`--prod`, `-p`)

```bash
./run.sh --prod
# or
./run.sh -p
```

Sets:

```text
DEVOPS_PORT       = 8081
WEIGHT_PORT       = 8082
BILLING_PORT      = 8083
WEIGHT_MYSQL_PORT = 3037
PROJECT_ROOT      = <absolute path to project root>
```

Docker Compose project name: `prod`  
Containers will look like: `prod-devops-app-1`, `prod-weight-app-1`, etc.

---

#### Test mode (`--test`, `-t`)

```bash
./run.sh --test
# or
./run.sh -t
```

Sets:

```text
DEVOPS_PORT       = 8084
WEIGHT_PORT       = 8085
BILLING_PORT      = 8086
WEIGHT_MYSQL_PORT = 3456
PROJECT_ROOT      = <absolute path to project root>
```

Docker Compose project name: `test`  
Containers will look like: `test-devops-app-1`, `test-weight-app-1`, etc.

> 💡 The different port values allow the **prod** and **test** stacks to run
> in parallel on the same machine, as long as your compose files use these
> variables in their `ports:` mappings.

Example (in `docker-compose.yml`):

```yaml
services:
  devops-app:
    ports:
      - "${DEVOPS_PORT}:5000"

  weight-db:
    ports:
      - "${WEIGHT_MYSQL_PORT}:3306"
```

---

### 📖 Help

Show usage and exit:

```bash
./run.sh --help
# or
./run.sh -h

DUNE 4