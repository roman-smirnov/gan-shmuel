# Gan Shmuel Project

## 🚀 Running the Project

All services are managed via the `run.sh` helper script in the **project root**.

```bash
./run.sh [--build|-b] (--prod|-p | --test|-t)
```

You **must** choose exactly one mode: `--prod` or `--test`.

---

### 🎛️ Command-line Options

| Flag            | Description                                      |
|-----------------|--------------------------------------------------|
| `-p`, `--prod`  | Run the **production** stack (`project: prod`)   |
| `-t`, `--test`  | Run the **test** stack (`project: test`)         |
| `-b`, `--build` | Rebuild images before starting (`--build`)       |
| `-h`, `--help`  | Show usage and exit                              |


### Down a Group of Services 
```
docker compose -p prod down -v
docker compose -p test down -v
```


### 🌐 What the script actually does

On every run, the script:

1. `cd`’s into the directory containing `run.sh`
2. Exports `PROJECT_ROOT` to the current directory
3. Parses your flags
4. Sets mode-specific environment variables
5. Runs:

   ```bash
   docker compose -p <prod|test> up [--build] -d
   ```

You’ll see the exact `docker compose` command printed before it runs, for example:

```bash
Running command: docker compose -p prod up --build -d
```

---

### 🌍 Environment per mode

These environment variables are exported **before** `docker compose` is invoked, so they can be used in your `docker-compose.yml` (for `ports:`, `environment:`, etc.).

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
WEIGHT_MYSQL_PORT = 3038
PROJECT_ROOT      = <absolute path to project root>
```

Docker Compose project name: `test`  
Containers will look like: `test-devops-app-1`, `test-weight-app-1`, etc.

> 💡 The different port values allow the **prod** and **test** stacks to run in parallel on the same machine, as long as your `docker-compose.yml` uses these variables in its `ports:` mappings.

Example (in `docker-compose.yml`):

```yaml
services:
  devops-app:
    ports:
      - "${DEVOPS_PORT}:8080"

  weight-db:
    ports:
      - "${WEIGHT_MYSQL_PORT}:3306"
```

---

### 🛠 Forcing a rebuild

To rebuild images before starting the stack:

```bash
# Production
./run.sh --prod --build
./run.sh -p -b

# Test
./run.sh --test --build
./run.sh -t -b
```

---

### 📖 Help

Show usage and exit:

```bash
./run.sh --help
# or
./run.sh -h
```
Salih is the king
