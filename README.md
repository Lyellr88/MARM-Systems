[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/lyellr88-marm-memory-badge.png)](https://mseep.ai/app/lyellr88-marm-memory)

<div align="center">
<picture>
<img src="https://raw.githubusercontent.com/Lyellr88/marm-memory/MARM-main/assets/marm-logo.png"
     alt="marm-memory - persistent local memory server for AI agents (Model Context Protocol)"
     width="900"
     height="250">
</picture>
<h1 align="center">marm-memory v2.48.0 - Give your AI Agents a permanent memory in 60 seconds</h1>

[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://github.com/Lyellr88/marm-memory/blob/MARM-main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.4-blue)](https://fastapi.tiangolo.com/)
[![Docker Pulls](https://img.shields.io/docker/pulls/lyellr88/marm-mcp-server)](https://hub.docker.com/r/lyellr88/marm-mcp-server)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/marm-mcp-server?period=total&units=NONE&left_color=GREY&right_color=BLUE&left_text=pip-downloads)](https://pepy.tech/projects/marm-mcp-server)
[![PyPI Version](https://img.shields.io/pypi/v/marm-mcp-server)](https://pypi.org/project/marm-mcp-server/)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-LIVE-blue)](https://registry.modelcontextprotocol.io/?q=marm-mcp)

[![Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/nhyJWPz2cf)
[![Publish](https://github.com/Lyellr88/marm-memory/actions/workflows/publish-mcp.yml/badge.svg?branch=MARM-main)](https://github.com/Lyellr88/marm-memory/actions/workflows/publish-mcp.yml)
[![CodeQL](https://github.com/Lyellr88/marm-memory/actions/workflows/github-code-scanning/codeql/badge.svg?branch=MARM-main)](https://github.com/Lyellr88/marm-memory/security/code-scanning)
[![marm-memory MCP server](https://glama.ai/mcp/servers/Lyellr88/marm-memory/badges/score.svg)](https://glama.ai/mcp/servers/Lyellr88/marm-memory)

> Contributions welcome! Browse [open issues](https://github.com/Lyellr88/marm-memory/issues) to contribute, or join the [MARM Discord](https://discord.gg/nhyJWPz2cf) to share workflows, get setup help, and connect with other builders.

</div>

## Table of Contents

- [Quick Start](#quick-start)
- [Why MARM Memory](#why-marm-memory)
- [Performance & Scaling Benchmarks](#performance--scaling-benchmarks)
- [MCP Client Setup](#mcp-client-setup-for-http--stdio)
- [Runtime CLI Commands](#runtime-cli-commands)
- [Complete MCP Tool Suite](#complete-mcp-tool-suite-14-tools)
- [Using MARM: Talk, Don't Call Tools](#using-marm-talk-dont-call-tools)
- [Understanding MARM Memory](#understanding-marm-memory)
- [Knowledge Graphs: Code & Concepts](#knowledge-graphs-code--concepts)
- [Architecture & Internals](#architecture--internals)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Project Documentation](#project-documentation)

## Quick Start

1. Install and initialize with your preferred agent profiles:

```bash
pip install marm-mcp-server
marm-memory init --g-claude --g-codex --g-gemini
```

> **Also available: --g-qwen and --g-kiro. Run without flags to install into your current project folder instead of home**

1. Hand off to your AI companion. Tell your agent:

> **"Use the marm-init skill to set up MARM."**

1. Interact: Your agent will handle the entire setup (Python/Docker, HTTP/STDIO, keys, and client configs) interactively right inside your chat.

**Manual setup**

Prefer to wire it up yourself:

> Replace "agent" with your client’s CLI command (for example, claude, gemini, or qwen). For Codex, use codex mcp add marm-memory --url http://localhost:8001/mcp instead.

| If you are... | Start the server | Connect your MCP client |
| --------------- | ------------------ | ------------------------- |
| **Solo developer / researcher** | `marm-memory start` | `"agent" mcp add --transport http marm-memory http://localhost:8001/mcp` |
| **Private local STDIO user** | `marm-mcp-stdio` | `"agent" mcp add --transport stdio marm-memory-stdio marm-mcp-stdio` |
| **Multiple agents sharing memory** | `marm-memory start --profile swarm` | `"agent" mcp add --transport http marm-memory http://localhost:8001/mcp` |
| **Private high-throughput swarm** | `marm-memory start --profile swarm-max` | `"agent" mcp add --transport http marm-memory http://localhost:8001/mcp` |
| **Trusted private lab/server** | `marm-memory start --profile trusted` | `"agent" mcp add --transport http marm-memory http://localhost:8001/mcp` |

- ⚡ Fastest HTTP Startup: Run marm-memory fast-start-http to spin up the local runtime, launch the console, and open it in your browser immediately.
- 🖥️ Web Console: Run marm-memory console to view the local UI app instantly (no Node.js required).
- ⚙️ Lifecycle Management: Manage the background daemon using status, logs --follow, restart, and stop.
- 💡 Quick Flags: Use --no-console or --no-browser to restrict startups. Run marm-memory --help for full command lists.

## Why MARM Memory

**Your AI forgets everything. MARM Memory doesn't.**

marm-memory gives your agents a private, shared memory for the context that normally gets lost between chats: decisions, research, fixes, notes, and project history. Switch from Claude Code to Codex or Gemini without losing the context already gathered.

It brings three things together:

- 🧠 **Core Memory (7 tools)** stores conversations, notes, notebook entries, and summaries so they stay searchable.
- 💻 **Code Graph (5 tools)** maps your repository so agents can find symbols, follow code paths, and understand the project without rereading it all. Point it at a repo once and it keeps itself current as you work.
- 🧩 **Concept Graph (2 tools)** connects people, decisions, errors, and ideas from your stored memories, with links back to relevant code when available. It builds itself as you store memories.

All 14 tools work over HTTP and STDIO. Your agents share the same local memory across sessions instead of starting from scratch each time. The bundled Console App provides a browsable view of **Memories**, the **Knowledge Graph**, and **Indexed Projects**, including progress for graph builds and repository indexing. Indexing a repository creates its independent Code Graph, which you can explore from Knowledge Graph → Code Explorer even before storing any memories.

### How It Works

| Layer | What it does | Why it matters |
| ------- | -------------- | ---------------- |
| **Memory model** | Sessions, structured logs, notebooks, summaries, and semantic memories | Keeps project history searchable instead of trapped in one chat |
| **Scale layer** | SQLite WAL mode, connection pooling, serialized write queue, and HTTP rate-limit presets | Lets one server support solo use, multi-agent work, and swarm-style bursts |
| **Intelligence layer** | FTS filter, semantic re-rank, bounded semantic fallback, auto-classification, write-time consolidation, and compaction candidates | Keeps recall useful as memory grows instead of letting duplicates pile up |
| **Code graph layer** | Repo indexing, symbol lookup, call tracing, architecture overview, and change-impact analysis | Gives agents project structure without rereading the whole codebase |
| **Concept graph layer** | Entity and relationship extraction from stored memories, with links back into the code graph | Connects decisions, errors, tools, and people across sessions instead of leaving them as flat text |
| **Token layer** | Lightweight 7-tool core surface (14 total with bundled graph tools), semantic re-rank before retrieval, and write-time deduplication | Reduces tokens sent to the model on every recall and cost stays predictable as memory scales |
| **Deployment layer** | Pip, Docker, STDIO, HTTP, and managed `swarm`, `swarm-max`, and `trusted` profiles | Lets you run private local memory or shared multi-agent memory with the same MCP surface |

See [Performance & Scaling Benchmarks](#performance--scaling-benchmarks) for retrieval latency, concurrency, and write-cost numbers, and [Architecture & Internals](#architecture--internals) for the mechanisms behind each layer.

### Runtime CLI Commands

`marm-memory` is the local runtime manager installed with the Python package. These are the normal operational commands; use `marm-memory <command> --help` for flags and command-specific examples.

**Daily runtime work**

```bash
marm-memory fast-start-http                # start HTTP, Console, and open the browser
marm-memory start                          # start or reuse the managed HTTP runtime
marm-memory start --profile swarm          # shared multi-agent preset
marm-memory stop                           # stop the managed runtime safely
marm-memory restart                        # restart the managed runtime
marm-memory status                         # inspect runtime, database, queue, and graph status
marm-memory logs --follow                  # follow bounded runtime logs
marm-memory console                        # start or reuse the bundled local Console
```

**Transports and setup**

```bash
marm-memory http                           # run HTTP in the foreground
marm-memory stdio                          # run the strict local MCP STDIO transport
marm-memory init                           # install the MARM skill into detected agents (project scan)
marm-memory init --g-claude                # install the skill into the home-folder claude directory
marm-memory doctor                         # diagnose the local install
marm-memory key init                       # create or reuse ~/.marm/.env without displaying the key
marm-memory key path                       # print the managed key-file path
marm-memory key reveal                     # explicitly display the managed key
marm-memory console --import-key           # open an authenticated local Console session
marm-memory upgrade --check                # compare the installed package with PyPI
marm-memory uninstall                      # preview package removal; always preserves ~/.marm
```

**Knowledge, projects, and maintenance**

```bash
marm-memory knowledge status               # Indexers, models, and how far behind automatic indexing is
marm-memory knowledge build --all          # Rebuild the whole concept graph (new memories index themselves)
marm-memory knowledge auto off             # Stop indexing memories automatically (on, off, status)
marm-memory projects list                  # List all tracked workspaces
marm-memory projects index <path>          # Add a repo to the code graph (kept current after that)
marm-memory projects status                # Inspect target repo graph readiness
marm-memory projects auto off              # Stop re-indexing repos automatically (on, off, status)
marm-memory maintenance status             # Check internal database optimization state
marm-memory maintenance embeddings migrate # Upgrade old 384-dim vectors to 512-dim
marm-memory maintenance chunks rechunk     # Recalibrate long memory text splits
```

Docker commands are documented separately below because they require explicit data mounts, network exposure, and key-handling choices.

## Performance & Scaling Benchmarks

MARM is tuned for fast recall first, even as memory grows and long memories are chunked behind the scenes.

These measurements use the fastembed-backed `jinaai/jina-embeddings-v2-small-en` encoder and a throwaway local SQLite database. Every timed path calls the shipped `MARMMemory` code, not a benchmark-local reimplementation. Sections 1-4 are timings from a single run of [`scripts/benchmarking/performance/bench_hotpath.py`](scripts/benchmarking/performance/bench_hotpath.py) on local hardware; absolute milliseconds vary by machine, so treat the scaling shape as the signal. Section 5 is a separate accuracy benchmark ([`run_eval.py`](scripts/benchmarking/accuracy/locomo/run_eval.py)) measuring retrieval rather than speed, and its latest row is a controlled before and after, explained there.

### 1. Retrieval Latency Scaling

End-to-end `recall_similar` latency (includes query encoding).

| Session Size ($N$) | Min Latency | Median Latency | p95 Latency |
| :--- | :--- | :--- | :--- |
| **N = 100** | 7.4 ms | 7.9 ms | 9.4 ms |
| **N = 250** | 11.9 ms | 13.5 ms | 15.4 ms |
| **N = 500** | 10.9 ms | 11.8 ms | 13.4 ms |
| **N = 1,000** | 13.3 ms | 13.5 ms | 15.6 ms |
| **N = 2,000** | 17.5 ms | 18.2 ms | 19.6 ms |
| **N = 4,000** | 23.8 ms | 25.9 ms | 30.9 ms |

Run-to-run variance at small $N$ is larger than the gap between adjacent sizes, which is why N = 250 reads slower than N = 500 here. Treat the trend from N = 1,000 upward as the real signal.

### 2. Encoder + Concurrency

- **Cold model load:** `893ms`
- **Warm encode:** median `3.8ms`, p95 `4.3ms`
- **Concurrent recall:** 10 gathered recalls completed in `151.5ms` vs `176.0ms` serial (`gather/serial = 0.86`). Do not read that as parallelism: repeated runs of this same benchmark land anywhere from `0.63` to `0.86`, so the ratio is not stable enough to claim a speedup. The path is serialized around shared encoder and SQLite work by design, and any apparent gain is measurement noise.

### 3. Write-Time Ingestion Cost

- **Consolidation off:** median `6.5ms`, p95 `7.6ms`
- **Consolidation on:** median `58.1ms`, p95 `106.5ms`
- **Tradeoff:** write-time dedupe/clustering adds `9.0x` median cost so recall stays fast and the store stays cleaner over time. Consolidation is off by default.

### 4. Recall Scaling: Full Scan vs Production Hybrid

Why recall stays flat as memory grows: Instead of scanning every vector, production recall uses an FTS keyword pre-filter to narrow the candidate pool, then re-ranks using a blended semantic + BM25 + temporal score. Both benchmark columns represent authentic asynchronous code paths timed with precomputed vectors to isolate retrieval speed from raw encoding overhead. Tests alternate execution to ensure completely unbiased cache conditions.

| Session Size ($N$) | Full Semantic Scan | Production Hybrid | Speedup | FTS candidates |
| :--- | :--- | :--- | :--- | :--- |
| **N = 100** | 3.3 ms | 6.6 ms | 0.5x | 85 / 200 |
| **N = 500** | 16.3 ms | 11.6 ms | 1.4x | 200 / 200 |
| **N = 1,000** | 31.1 ms | 14.7 ms | 2.1x | 200 / 200 |
| **N = 2,000** | 63.5 ms | 19.0 ms | 3.3x | 200 / 200 |
| **N = 4,000** | 127.2 ms | 29.1 ms | 4.4x | 200 / 200 |
| **N = 10,000** | 316.7 ms | 53.8 ms | 5.9x | 200 / 200 |

The full scan grows roughly linearly with $N$ while hybrid recall grows far more slowly, so the advantage still widens with session size. At very small $N$ the pre-filter is not worth its overhead and hybrid is slower.

### 5. LoCoMo Retrieval Accuracy

All 10 LoCoMo conversations are ingested through `marm_log_entry` (5,882 memories), then top-5 `marm_smart_recall` results are scored against 1,977 evidence-annotated questions. No answer-generation model or LLM judge is involved, so this measures whether the right memory is retrieved, not whether an agent answers correctly with it.

| Configuration | Any evidence hit | All evidence hit | Mean evidence recall |
| :--- | :--- | :--- | :--- |
| MiniLM baseline | 37.5% | 29.5% | not published |
| Jina v2 Small (v2.29.0) | 53.0% | 43.4% | 47.6% |
| v2.33.1 through v2.44.3 | 62.9 - 63.5% | 53.1 - 53.5% | 57.4 - 57.9% |
| **v2.44.4 (log lane fix)** | **69.1 - 69.6%** | **58.2 - 58.6%** | **63.0 - 63.5%** |

The last row is a controlled comparison, same build and data with the log lane as the only variable. That lane previously substring-matched the whole query against log topics and summaries, so a natural-language question never matched and it scored 0.0% on all 1,977 questions. It now tokenizes the query and reaches 53.3% on its own. Ranges rather than single figures because the semantic lane varies about half a point between runs, so a sub-point difference is not a result.

Multi-hop remains the weakest category at 44.9%, and single-hop evidence recall is 36.6% against a 66.2% any-hit rate, so the lane often surfaces some of a question's evidence rather than all of it. Reproduce with [`run_eval.py`](scripts/benchmarking/accuracy/locomo/run_eval.py).

### 6. vs Competitors: Architecture

MARM targets a specific niche: local-first memory for MCP-connected coding agents, not general personalization memory or a full agent runtime. Here's how it differs architecturally from established names in AI agent memory:

| | MARM | Mem0 | Letta (MemGPT) | Zep / Graphiti | agentmemory |
| --- | --- | --- | --- | --- | --- |
| **Type** | Memory engine, MCP-native | Memory layer API | Full agent runtime | Temporal knowledge graph | Memory engine, MCP-native |
| **Required infrastructure** | No separate data service (embedded SQLite) | Vector DB (Qdrant/pgvector) | Postgres + vector DB | Neo4j | Separate `iii-engine` runtime |
| **Deployment** | Local-first by default; Docker for shared/remote | Cloud API or self-hosted | Self-hosted or cloud | Cloud or self-hosted | Local-first |
| **Retrieval model** | Hybrid: FTS5 BM25 exact lane + semantic rerank | Vector + graph + key-value | Vector archival store + agent-managed core memory | Temporal knowledge graph (fact validity windows) | BM25 + vector + graph (RRF fusion) |
| **Write capture** | Explicit tool calls from the connected agent | Explicit `add()` calls (some integrations auto-extract) | Agent self-edits its own memory | Explicit API calls | Hook-based, automatic (no explicit calls needed) |
| **Code structure awareness** | Bundled code graph + concept graph, fused with memory | Not built in | Not built in | Not built in | Not built in (pairs with a separate project) |
| **Framework lock-in** | None (any MCP client) | None | High (must run within Letta) | None | None (any MCP client) |

**Disclaimers & Accuracy:** Competitor landscapes evolve rapidly. The matrix above reflects core architectural traits as of Q3 2026, based on public documentation and READMEs, not internal testing of each system. If any data point regarding an alternative framework has changed or is misrepresented, please open an issue or submit a Pull Request to update the table. We actively welcome corrections from peer maintainers.

## MCP Client Setup for HTTP & STDIO

**Manual pip install**

```bash
pip install marm-mcp-server
```

### Use this quick rule of thumb to choose your setup

- Local HTTP/STDIO = fastest single-machine setup.
- Docker HTTP = shared/always-on server (key required).
- Docker STDIO = private containerized local use (no HTTP key).

**Swarm / multi-agent note:** The write queue is enabled by default to serialize memory writes through one worker. For shared HTTP deployments, use `marm-memory start --profile swarm` (200 RPM) or `--profile swarm-max` (600 RPM). `--profile trusted` disables rate limiting entirely for private deployments. STDIO is still best for private single-agent/local use. See [Swarm & multi-agent presets](#swarm--multi-agent-presets) for the full table.

<details>
<summary><strong>Local pip HTTP </strong></summary>

> "agent" refers to claude, gemini, grok, qwen, or any MCP client. Codex uses --url instead of --transport to add MCP tools.

```bash
pip install marm-mcp-server
marm-memory start
# Stuck on client setup? Open a Q&A thread: https://github.com/Lyellr88/marm-memory/discussions
# most agents use this --transport command
"agent" mcp add --transport http marm-memory http://localhost:8001/mcp
codex mcp add marm-memory --url http://localhost:8001/mcp
```

Default pip/local startup is zero-config: MARM binds to localhost and does not require a key unless you expose it with `SERVER_HOST=0.0.0.0`.

</details>

<details>
<summary><strong>Local pip STDIO</strong></summary>

```bash
pip install marm-mcp-server
python -m marm_mcp_server.server_stdio
# most agents use this --transport command
"agent" mcp add --transport stdio marm-memory-stdio marm-mcp-stdio
codex mcp add marm-memory-stdio -- marm-mcp-stdio
```

Replace `marm-mcp-stdio` with `python -m marm_mcp_server.server_stdio` if using a virtualenv or a path-based setup. Works with Claude Code, Cursor, VS Code, Qwen, and Gemini CLI. STDIO stays a single local process with no port and no API key, and exposes the same 14 tools as HTTP.

</details>

<details>
<summary><strong>Local Python swarm modes (HTTP & STDIO)</strong></summary>

Use HTTP when multiple agents need to share one live MARM server. STDIO is still best for private single-agent use because each client owns its own local process.

```bash
# HTTP shared server, normal multi-agent use
marm-memory start --profile swarm

# HTTP shared server, heavier private swarm
marm-memory start --profile swarm-max

# HTTP trusted private lab/server, rate limiting disabled
marm-memory start --profile trusted

# STDIO remains keyless/private and does not use swarm flags
marm-mcp-stdio
```

</details>

---

<details>
<summary><strong>Docker HTTP (key required)</strong></summary>

> Docker HTTP requires an API key because it exposes MARM as a network server; STDIO stays local to the client process and does not need one.

If you installed MARM through pip, the product CLI can safely preview or run the same setup. It uses a loopback port by default, preserves `~/.marm`, stores the generated key in `~/.marm/.env` rather than shell history, and refuses to replace an existing container.

```bash
marm-memory docker command                 # preview the exact HTTP command
marm-memory docker run                     # create the managed HTTP container
marm-memory docker stdio-command           # print a Docker STDIO client command
marm-memory docker status
marm-memory docker logs --follow
marm-memory docker stop

# Optional: mount repositories read-only for code indexing.
marm-memory docker run --repo /absolute/path/to/repository

# Optional: preview or explicitly write a Compose configuration.
marm-memory docker compose
marm-memory docker compose --yes
```

The HTTP `run`, `command`, and `compose` commands accept the same operational flags:

| Flag | Purpose |
| --- | --- |
| `--data-dir <absolute path>` | Persistent host directory mounted at `/home/marm/.marm`. Defaults to `~/.marm`; this holds memory, indexes, logs, and the managed key file. |
| `--env-file <path>` | Explicit Docker env file. It must already contain `MARM_API_KEY`; without this flag, MARM uses `~/.marm/.env` and creates a key there only when `docker run` or `docker compose --yes` needs one. |
| `--port <number>` | Host HTTP port. Default: `8001`. |
| `--expose-network` | Bind the host port to `0.0.0.0` instead of loopback. This is deliberate network exposure; configure a firewall and TLS proxy. |
| `--profile standard\|swarm\|swarm-max\|trusted` | Select the same write-queue and rate-limit preset as native HTTP startup. |
| `--rate-limit-rpm <number>` | Override the selected profile's HTTP rate limit. `0` disables rate limiting. |
| `--repo <absolute path>` | Repeatable read-only repository mount for code indexing. MARM reports each corresponding `/workspace/repo-N` path to index inside the container. |
| `--tag <tag>` | Official image tag. Default: `latest`. |
| `--pull` | Pull the selected image before creating a new HTTP container. |
| `--name <name>` | Managed container name. MARM refuses to replace an existing container with that name. |
| `--memory <limit>` / `--cpus <limit>` | Optional Docker resource limits. |
| `--dry-run` | `docker run` only: print the planned command without creating a container or key file. `docker command` is always a preview. |

For example:

```bash
# Shared local server with a custom data path and two repositories for indexing.
marm-memory docker command \
  --profile swarm \
  --data-dir /srv/marm-data \
  --repo /srv/projects/api \
  --repo /srv/projects/web

# Execute the reviewed command, pulling the image first.
marm-memory docker run --profile swarm --data-dir /srv/marm-data --pull
```

Docker STDIO is separate from Docker HTTP: `marm-memory docker stdio-command` uses `docker run -i --rm`, has no port and no bearer key, but still mounts the data directory so SQLite memory persists after the short-lived container exits. Use `--data-dir` and `--tag` with that command when needed. There are no separate `docker key` or `docker mount` commands; `--env-file` and `--data-dir` make those choices explicit in the generated HTTP command.

`marm-memory docker pull` only downloads an image. `marm-memory docker maintenance embeddings migrate` runs against the same data mount and refuses while the managed HTTP container is running. The helper is available only with the pip-installed `marm-memory` command; Docker-only users can use the raw commands below.

```bash
# Step 1: generate key (do not add < > around the key)
docker run --rm lyellr88/marm-mcp-server:latest --generate-key

# Step 2: run server
docker pull lyellr88/marm-mcp-server:latest
docker run -d --name marm-mcp-server \
  -p 127.0.0.1:8001:8001 \
  -e SERVER_HOST=0.0.0.0 \
  -e MARM_API_KEY=your-generated-key \
  -v ~/.marm:/home/marm/.marm \
  lyellr88/marm-mcp-server:latest

# Step 3: connect client
"agent" mcp add --transport http marm-memory http://localhost:8001/mcp --header "Authorization: Bearer your-generated-key"

# PowerShell: set this before starting/restarting Codex
$env:MARM_API_KEY="your-generated-key"
codex mcp add marm-memory --url http://localhost:8001/mcp --bearer-token-env-var MARM_API_KEY

# Quick auth smoke test
curl -i -H "Authorization: Bearer $env:MARM_API_KEY" http://127.0.0.1:8001/mcp
```

`--bearer-token-env-var` takes the environment variable name, not the raw key. Start or restart Codex from the same shell after setting `$env:MARM_API_KEY`. For local Docker smoke tests, `MARM_API_KEY=test` is fine and avoids shell escaping problems; use a generated key for real deployments. A `406 Not Acceptable` from the smoke-test `GET /mcp` means auth reached the MCP endpoint; `401 Unauthorized` means the key is missing or mismatched.

</details>

<details>
<summary><strong>Docker HTTP swarm mode</strong></summary>

```bash
# --swarm: write queue on, 200 RPM - recommended for multi-agent shared servers
docker run -d --name marm-mcp-server \
  -p 127.0.0.1:8001:8001 \
  -e SERVER_HOST=0.0.0.0 \
  -e MARM_API_KEY=your-generated-key \
  -v ~/.marm:/home/marm/.marm \
  lyellr88/marm-mcp-server:latest --swarm
```

</details>

<details>
<summary><strong>Docker graph indexing: mount the repo</strong></summary>

Docker graph tools run inside the container, so they cannot see host paths unless you mount them at `docker run`.

```powershell
$env:MARM_API_KEY="test"

# The second -v line mounts your repo; adjust the host path to your project
docker run -d --name marm-mcp-server `
  -p 127.0.0.1:8001:8001 `
  -e SERVER_HOST=0.0.0.0 `
  -e MARM_API_KEY=$env:MARM_API_KEY `
  -v ~/.marm:/home/marm/.marm `
  -v C:\Users\lyell\Desktop\marm-memory:/workspace/marm-memory `
  lyellr88/marm-mcp-server:latest
```

Then index the container path, not the Windows host path:

```text
marm_graph_index(repo_path="/workspace/marm-memory")
```

Graph tools must use the container path. Mounts cannot be added to an already-running container; stop and restart the container with the repo mount when you want Docker graph indexing.

</details>

<details>
<summary><strong>Docker STDIO (no HTTP key)</strong></summary>

Docker STDIO includes the same built-in marm-graph tools; no extra image or install step is required.

```bash
docker run --rm -i \
  -v ~/.marm:/home/marm/.marm \
  --entrypoint python \
  lyellr88/marm-mcp-server:latest \
  -m marm_mcp_server.server_stdio
```

</details>

---

<details>
<summary><strong>Support notes</strong></summary>

- Docker HTTP requires a key; Docker STDIO does not.
- If you get `401`, verify key match and client restart after env var changes.
- For full key setup, rotation, and troubleshooting: [INSTALL-DOCKER.md](docs/INSTALL-DOCKER.md)

</details>

### Connect your client

Start the server (`python -m marm_mcp_server`), then wire up your client below. Every block assumes the default local install (no key). For Docker or exposed servers, add the `Authorization: Bearer` header shown in each client's collapsible.

<details>
<summary><strong>Claude Code</strong></summary>

```bash
claude mcp add --transport http marm-memory http://localhost:8001/mcp
```

Claude Code supports HTTP, SSE, and STDIO through `claude mcp add`; use HTTP for MARM. For STDIO: `claude mcp add --transport stdio marm-memory-stdio marm-mcp-stdio`.

</details>

<details>
<summary><strong>VS Code / GitHub Copilot Agent</strong></summary>

Add to `.vscode/mcp.json` in your workspace. Use `marm-memory-local` for direct Python installs; `marm-memory-docker` for Docker or exposed/key mode.

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "marm-api-key",
      "description": "MARM API Key for Docker or exposed server mode",
      "password": true
    }
  ],
  "servers": {
    "marm-memory-local": {
      "type": "http",
      "url": "http://localhost:8001/mcp"
    },
    "marm-memory-docker": {
      "type": "http",
      "url": "http://localhost:8001/mcp",
      "headers": {
        "Authorization": "Bearer ${input:marm-api-key}"
      }
    }
  }
}
```

Open `.vscode/mcp.json`, click **Start** above the server you want, then use Copilot Agent or any extension that consumes VS Code's native MCP registry.

</details>

<details>
<summary><strong>Cursor</strong></summary>

Add to `.cursor/mcp.json` in your workspace. Cursor uses `mcpServers`, not VS Code's `servers` root.

```json
{
  "mcpServers": {
    "marm-memory-local": {
      "type": "http",
      "url": "http://localhost:8001/mcp"
    },
    "marm-memory-docker": {
      "type": "http",
      "url": "http://localhost:8001/mcp",
      "headers": {
        "Authorization": "Bearer ${env:MARM_API_KEY}"
      }
    }
  }
}
```

For Docker/key mode, launch Cursor with `MARM_API_KEY` set in the environment.

</details>

<details>
<summary><strong>Codex CLI</strong></summary>

Codex uses `codex mcp add` or TOML config at `~/.codex/config.toml` (`%USERPROFILE%\.codex\config.toml` on Windows).

```bash
# Direct Python install - no key needed
codex mcp add marm-memory --url http://localhost:8001/mcp

# Docker or SERVER_HOST=0.0.0.0 - key required (set MARM_API_KEY in your shell first)
codex mcp add marm-memory --url http://localhost:8001/mcp --bearer-token-env-var MARM_API_KEY
```

```toml
[mcp_servers."marm-memory"]
url = "http://localhost:8001/mcp"
enabled = true
bearer_token_env_var = "MARM_API_KEY"
```

</details>

<details>
<summary><strong>Gemini CLI</strong></summary>

```bash
# Direct Python install - no key needed
gemini mcp add --transport http marm-memory http://localhost:8001/mcp

# Docker or SERVER_HOST=0.0.0.0 - key required
gemini mcp add --transport http marm-memory http://localhost:8001/mcp --header "Authorization: Bearer your-generated-key"
```

Equivalent `~/.gemini/settings.json` (user scope) or project `.gemini/settings.json`:

```json
{
  "mcpServers": {
    "marm-memory": {
      "httpUrl": "http://localhost:8001/mcp",
      "headers": {
        "Authorization": "Bearer your-generated-key"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Qwen Code</strong></summary>

```bash
# Direct Python install - no key needed
qwen mcp add --transport http marm-memory http://localhost:8001/mcp

# Docker or SERVER_HOST=0.0.0.0 - key required
qwen mcp add --transport http marm-memory http://localhost:8001/mcp --header "Authorization: Bearer your-generated-key"
```

Equivalent `.qwen/settings.json` (project) or `~/.qwen/settings.json` (user):

```json
{
  "mcpServers": {
    "marm-memory": {
      "httpUrl": "http://localhost:8001/mcp",
      "headers": {
        "Authorization": "Bearer your-generated-key"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>xAI / Grok Remote MCP</strong></summary>

xAI connects from its own infrastructure, so `localhost` will not work. Expose MARM behind HTTPS and set `MARM_API_KEY`.

```json
{
  "type": "mcp",
  "server_url": "https://your-marm-domain.example.com/mcp",
  "server_label": "marm-memory",
  "authorization": "Bearer your-generated-key"
}
```

</details>

Full platform walkthroughs, key setup, and OS-specific notes: [Windows](docs/INSTALL-WINDOWS.md#client-connections) · [macOS](docs/INSTALL-MACOS.md#start-marm-yourself) · [Linux](docs/INSTALL-LINUX.md#client-connections) · [Docker/key mode](docs/INSTALL-DOCKER.md#client-connections) · [Other platforms](docs/INSTALL-PLATFORMS.md)

> Using a client that isn't listed? [Open an issue](https://github.com/Lyellr88/marm-memory/issues/new/choose) and let us know; client adapters are a first-class feature request.

<details>
<summary><strong>System requirements, data location & backup</strong></summary>

**Requirements**

- **Python**: 3.10 or higher
- **SQLite3**: Included with Python (no separate install needed)
- **Storage**: ~100MB minimum for initial setup, scales with memory database size
- **RAM**: 512MB minimum (varies by concurrent clients and database size)
- **OS**: Windows, macOS, Linux

**Data location**

- **Location**: `~/.marm/` (Linux/macOS) or `%USERPROFILE%\.marm\` (Windows)
- **Contents**: SQLite database with all memories, sessions, and notebooks; the concept graph lives in its own `~/.marm/index/` database
- **Backup**: Copy the entire `~/.marm/` directory to preserve all data
- **Privacy**: Everything stays on your machine, no cloud sync or external storage

**Verify installation**

Use the MCP server health endpoint for the fastest live check:

```bash
curl http://localhost:8001/health
```

Expected output includes server version, feature availability (semantic search status), database connection status, and service health status.

</details>

## Complete MCP Tool Suite (14 Tools)

**💡 Pro Tip:** You don't need to manually call these tools! Just tell your AI agent what you want in natural language:

- *"Claude, log this session as 'Project Alpha' and add this conversation as 'database design discussion'"*
- *"Remember this code snippet in your notebook for later"*
- *"Search for what we discussed about authentication yesterday"*

The AI agent will automatically use the appropriate tools. Manual tool access is available for power users who want direct control.

### 🧠 Core Memory (7 tools)

| Tool | What it does | Key parameters |
| ------ | -------------- | ---------------- |
| `marm_smart_recall` | Hybrid memory recall with an additive, bounded concept/code graph sidecar when a compatible graph exists | `query`, `limit`, `session_name`, `search_all`, `detail=1/2/3`, `project`, `platform`, `exact_mode` |
| `marm_log_entry` | Add structured session log entries; each entry is also embedded into semantic memory so `marm_smart_recall` can find it | `entry`, `session_name` |
| `marm_log_show` | Display all entries and sessions, with filtering | `session_name` |
| `marm_delete` | Delete a log session, log entry, or notebook entry | `type`, `target`, `session_name`, `project`, `platform` |
| `marm_summary` | Cached, paste-ready session summaries with intelligent truncation | `session_name` |
| `marm_notebook` | Session-scoped scratch pad plus promotion to a permanent, graph-linked doc | `action="add"\|"use"\|"show"\|"status"\|"clear"\|"save"`, `name`, `data`, `session_name`, `project`, `platform` |
| `marm_compaction` | Agent-assisted memory cleanup with a reviewable audit trail | `action="status"\|"candidates"\|"review"\|"stage"\|"apply"\|"discard"` |

### 🕸️ Code Graph (5 tools)

| Tool | What it does | Key parameters |
| ------ | -------------- | ---------------- |
| `marm_graph_index` | Index a repo into the code-structure graph, check status, list projects, or turn automatic re-indexing on and off | `repo_path`, `project`, `action` |
| `marm_code_lookup` | Find symbols, text patterns, or a symbol's source; use instead of grep/glob | `kind="auto"\|"symbol"\|"text"\|"snippet"` |
| `marm_graph_trace` | Trace call paths and data flow from a function | `direction`, `mode` |
| `marm_graph_architecture` | Architecture overview: modules, node/edge breakdown, schema | `project` |
| `marm_graph_impact` | Blast radius of code changes: git diff → affected symbols + risk | `since`, `base_branch`, `depth` |

### 🧩 Concept Graph (2 tools)

| Tool | What it does | Key parameters |
|------|--------------|----------------|
| `marm_concept_build` | Rebuild the graph, or index memories stored before automatic indexing. New memories are indexed on their own | `session_name`, `project`, or `search_all=True` (one required) |
| `marm_concept_recall` | Explicitly query entities, relationships, and linked code symbols | `query`, `depth` (1-5), `direction`, `project`, `platform` |

All 14 tools are available on both HTTP and STDIO. Behind the tool surface, the server handles lifecycle setup, protocol refresh, docs indexing, date context, summary-cache maintenance, write queue handling, concept indexing, code re-indexing as repos change, project/platform attribution, and health checks automatically; none of those consume the agent's attention or tokens. The two graph engines start lazily on first use and never block the 7 core memory tools if they fail to start. See [Architecture & Internals](#architecture--internals) for the mechanisms.

## Using MARM: Talk, Don't Call Tools

MARM handles lifecycle work internally. Docs and session state initialize on the first real tool call, and packaged docs are indexed into the `marm_system` memory namespace with source-file hash tracking, so your agent can answer MARM usage questions from memory itself.

### Example Workflow: Cross-AI Research Project

A realistic workflow showing MARM in action. **Scenario:** you're researching authentication patterns for a new project using multiple AI clients.

#### Phase 1: Route Session (Claude)

``` markdown
You: "Claude, create a MARM session called 'auth-research-2025-01'"
Claude calls: marm_log_entry(entry="Session: auth-research")
Result: Session routed to auth-research-[today]. MARM lifecycle/docs initialize automatically.
```

#### Phase 2: Capture Research (Claude)

``` markdown
You: "Summarize OAuth2 vs JWT for API authentication and save it"
Claude calls: marm_log_entry(entry="Research: OAuth2 is token-based with refresh cycles, better for delegated access. JWT is stateless, good for microservices...", session_name="auth-research-2025-01")
Result: Research captured in the active session log and marked for summary-cache refresh
```

#### Phase 3: Add Reusable Reference (Claude)

``` markdown
You: "Save a JWT validation code snippet to my notebooks as 'jwt-validation-pattern'"
Claude calls: marm_notebook(action="add", name="jwt-validation-pattern", data="def verify_jwt(token):\n  # validation logic...")
Result: Reusable snippet stored for future projects
```

#### Phase 4: Recall Context (Gemini)

``` markdown
You: "Gemini, what authentication approaches did we research? Activate the JWT pattern."
Gemini calls: marm_smart_recall("authentication patterns", search_all=True)
Gemini calls: marm_notebook(action="use", names="jwt-validation-pattern")
Result: Gemini sees previous research + has JWT code available as context
```

#### Phase 5: Synthesis & Summary (Qwen)

``` markdown
You: "Qwen, pull everything from the auth research and create a summary"
Qwen calls: marm_smart_recall("authentication", session_name="auth-research-2025-01", limit=20)
Qwen calls: marm_summary(session_name="auth-research-2025-01")
Result: Qwen generates an implementation guide from all captured research
```

#### Phase 6: End Session (Claude)

``` markdown
You: "Log final decision - we're using JWT for APIs, and OAuth2 for user auth"
Claude calls: marm_log_entry(entry="DECISION: JWT for API auth, OAuth2 for user flows. Rationale: stateless APIs + delegated user access", session_name="auth-research-2025-01")
Result: Decision logged and searchable by all future AI clients
```

**Result**: Three different AI clients collaboratively researched a topic, shared insights, and documented decisions. All without re-explaining the project to each new AI.

### Advanced patterns

<details>
<summary><strong>Project memory architecture & knowledge base development</strong></summary>

```txt
Project Structure:
├── project-name-planning/          # Initial design and requirements
├── project-name-development/       # Implementation details
├── project-name-testing/           # QA and debugging notes
├── project-name-deployment/        # Production deployment
└── project-name-retrospective/     # Lessons learned
```

Knowledge base loop:

1. **Capture**: Use `marm_log_entry` for structured session learnings
2. **Organize**: Create themed sessions for knowledge areas
3. **Synthesize**: Regular `marm_summary` for knowledge consolidation
4. **Apply**: Convert summaries to `marm_notebook(action="add", ...)` entries

Multi-AI collaboration: each AI works in dedicated sessions on its strengths, uses `marm_smart_recall` to build on the others' work, then a collaborative session combines the insights.

</details>

<details>
<summary><strong>Pro tips & best practices</strong></summary>

- **Session naming**: Include the LLM name for cross-referencing
- **Strategic logging**: Focus on key decisions, solutions, discoveries, configurations
- **Global search**: Use `search_all=True` to search across all sessions
- **Natural language search**: "authentication problems with JWT tokens" beats "auth error"
- **Layered recall depth**: `detail=1` returns a short summary view (~200 chars), `detail=2` a larger context view (~500 chars), `detail=3` full memory content
- **Notebook stacking**: Combine multiple entries for complex workflows
- **Compaction**: Let MARM surface compaction candidates, then use `marm_compaction` to stage, review, apply, or discard summaries
- **Session lifecycle**: Start → Work → Reference → Review staged compaction when MARM asks

</details>

## Understanding MARM Memory

Two searches, two very different problems, one tool:

```txt
User: "I discussed machine learning algorithms yesterday"
MARM Search: Finds related memories about "ML models", "neural networks", "AI training"

User: "What was the COMPACTION_TRIGGER_COUNT setting?"
MARM Search: Finds the exact config memory even if the rest of the text differs
```

The first query is about *meaning*, so MARM reranks candidates with local vector embeddings — RAG-style semantic search without a hosted vector database. The second is *syntax-shaped* (a config key), so MARM detects that automatically and routes it through deterministic exact matching instead. This exact-retrieval lane is the difference between a memory system that works in demos and one that answers the questions developers actually ask: config keys, CLI flags, file paths, API names, error strings. Pure-semantic memory systems fail at exactly those queries.

<details>
<summary><strong>How the recall pipeline works under the hood</strong></summary>

MARM uses **filter→rerank hybrid recall** plus an exact retrieval lane:

1. **Exact lane** (`exact_mode="auto"`, the default): config keys, CLI flags, file paths, API/tool names, dotted namespaces, HTTP routes, URLs, and quoted command strings are detected and routed through deterministic FTS5 BM25 with a LIKE fallback. No embeddings involved, so results are stable and literal.
2. **Filter→rerank lane**: natural-language queries first pull a bounded candidate set from the FTS index (`FTS_CANDIDATE_LIMIT`, default 200), then semantic embeddings rerank those candidates by meaning. Conservative temporal weighting gives fresher memories a modest boost when matches are otherwise close.
3. **Bounded semantic fallback**: when FTS coverage is weak or unusable, MARM falls back to a bounded semantic scan (`RECALL_SCAN_LIMIT`). If the response includes `recall_scan_truncated=true`, the fallback hit its cap; narrow the session/query or raise the env var for larger stores.
4. **Chunk-aware scoring**: long memories (roughly 180+ words) are embedded as overlapping chunk rows internally, and recall collapses chunk scores back to one parent memory using the best-matching chunk. Both the rerank lane and the fallback lane are chunk-aware.

This is why recall latency stays nearly flat as the store grows (see [benchmarks](#performance--scaling-benchmarks)): the semantic rerank always scores a bounded set instead of scanning every embedding.

**Exact recall control:** `exact_mode="auto"` is usually right. Use `exact_mode="exact"` when a query must match literal text such as `RECALL_SCAN_LIMIT`, `--generate-key`, or `settings.py`. Use `exact_mode="semantic"` when a syntax-looking query should still be treated as meaning-based recall.

</details>

### Memory types & classification

1. **Context Logs** - Auto-classified conversation memories
2. **Manual Entries** - Explicitly saved important information
3. **Notebook Entries** - Reusable instructions and knowledge
4. **Session Summaries** - Compressed conversation history

MARM automatically categorizes content on write: **Code** (programming snippets and technical discussions), **Project** (work conversations and planning), **Book** (literature, learning materials, research), and **General** (everything else).

### Project & platform attribution

MARM stores nullable `project` and `platform` columns on memories, log entries, and notebook entries. The project is detected from the working directory and the platform from the connecting client (Claude Code, VS Code, Cursor, ...); `MARM_PROJECT` and `MARM_PLATFORM` override detection. `marm_smart_recall(project=..., platform=...)` scopes recall without changing the default unfiltered behavior, so one shared server can hold several projects without cross-contamination.

## Knowledge Graphs: Code & Concepts

MARM ships two graph systems that complement the memory store: a **code graph** that understands your repository's structure, and a **concept graph** that understands what your stored memories are about. When both are indexed for the same project, concept entities cross-link to code symbols.

### Code Graph: repo indexing and code lookup

`marm-graph` is bundled into both transports. It indexes a repository once, then lets agents ask code-structure questions without repeatedly scanning files:

```text
Use marm_graph_index to index this repository.
Then use marm_code_lookup when you need symbols, files, or source snippets.
Use marm_graph_trace for call paths, marm_graph_architecture for an overview, and marm_graph_impact for change-risk checks.
```

The recommended agent workflow: index once, then `marm_code_lookup` before broad file reads, `marm_graph_trace` when callers/callees or data-flow context matters, `marm_graph_architecture` for orientation, and `marm_graph_impact` before risky refactors. One graph query replaces dozens of grep/read cycles, which is where the token savings come from.

Once a repository is indexed, MARM keeps it current on its own. A filesystem watcher notices a save, a commit, a branch switch, or a merge and re-indexes shortly after, debounced so a burst of changes becomes one pass rather than one per file. A periodic reconciliation pass catches anything a watcher event missed and is the only trigger for a directory that is not a git repo. To index only on request instead:

```text
marm-mcp-server projects auto off
```

An agent can do the same with `marm_graph_index(action="auto_off")`, and `action="auto_status"` reports what is being watched and when each project was last indexed. The switch persists across restarts and beats the `GRAPH_AUTO_INDEX` environment variable.

Under the hood, the engine is [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) (MIT), a zero-dependency static binary that parses 158 languages through tree-sitter with Hybrid LSP type resolution for the major ones, indexes an average repository in seconds, and answers symbol search and call tracing in well under a second. Measured on a 149,107-node graph over the persistent connection MARM holds: symbol search 146ms, call tracing 67ms, and the full architecture overview 1.23s, which is the one query that is not sub-second. MARM pins a specific release, verifies its tool schema on startup, and routes the upstream tool set through 5 focused MCP tools so the model surface stays small. The graph backend starts lazily on first graph-tool use, so memory, logging, notebook, and summary tools still start fast. In Docker, the engine binary is baked into the image; local pip installs fetch it on first graph use (~269MB, one time).

**Degraded mode:** if the graph engine fails to start (no network for the first-run download, disk full, schema drift) or `GRAPH_ENABLED=false` is set, graph tools return `{"status": "error", "message": "graph backend unavailable"}` while the other 9 tools keep working normally. Graph failures can never take down memory.

### Concept Graph: what your memories are about

MARM extracts a knowledge graph from the memories you store, producing typed entities (**concepts, decisions, patterns, errors, tools, people, organizations**) connected by typed relationships (**fixes, implements, depends_on, uses, causes, replaces, extends**). This happens on its own: storing a memory queues it, and a background worker adds it to the graph roughly 30 seconds later. `marm_concept_build` is still there for a full or scoped rebuild. Once there is a graph, `marm_smart_recall` adds bounded related entities, relationships, and linked code as a `graph_context` sidecar without changing primary memory ranking. `marm_concept_recall` remains available for explicit graph exploration:

```text
marm_concept_recall(query="write queue")            → the entity, its relationships, linked code symbols
marm_concept_recall(query="related to SQLite", depth=3) → multi-hop traversal of everything connected
```

How to use it:

- **Automatic by default**: new memories reach the graph without a tool call. Set `CONCEPT_AUTO_INDEX=false` to go back to manual builds only, which stops the worker but keeps recording queue rows, so turning it back on picks up everything written while it was off; `CONCEPT_INDEX_DEBOUNCE_SECONDS` (30) and `CONCEPT_INDEX_BATCH_SIZE` (20) control the pace.
- **Safe on both transports at once**: a leased lock in the memory database keeps a rebuild in one process from dropping graph tables while another process is writing to them. A build that finds the graph busy says so instead of colliding.
- **Failure never reaches your memories**: indexing runs on a durable queue outside the write path. Extraction problems retry, a memory that fails repeatedly is parked with its error, and the memory itself stores and recalls normally throughout.
- **Clearing a backlog costs some recall speed**: entity extraction is CPU-bound, so while the worker is working through a queue, measured recall goes from ~8ms to ~16ms median on a real 768-memory corpus. Writes are unaffected. It only applies while a backlog is draining, which for most people is once, after the upgrade rebuild. Reproduce it with `scripts/benchmarking/performance/bench_concept_worker.py --from-live`.
- **Build for the backlog**: `marm_concept_build` scoped to a `session_name`, `project`, or `search_all=True` indexes memories stored before automatic indexing existed, and rebuilds after an upgrade that requires one.
- **Upgrade twice so far**: graphs built before platform attribution, or before compaction sources replaced summaries as the indexed rows, require `marm_concept_build(search_all=True)`. A full build backs up and resets only the derived concept database; targeted builds refuse to guess platform ownership.
- **Whole scope, paged**: builds read every memory in scope. `CONCEPT_BUILD_ROW_CAP` (default 500) is the page size, so lowering it makes a build read more, smaller pages rather than skipping the rest.
- **Compacted sessions**: the original memories are indexed and the generated summary is not, so concepts stay attributed to where they were actually stated.
- **Recall fails open**: a missing, empty, incompatible, or unavailable concept graph never blocks normal memory recall. The response reports graph status separately.
- **Code cross-linking**: when the code graph has indexed the same project, concept entities that match code symbols get linked, connecting "what we decided" to "where it lives in the code."
- **Bundled extraction runtime**: the spaCy runtime and English extraction model ship with MARM but load only on the first extraction, which now happens on its own shortly after the first memory is stored rather than when you run a build. If a damaged or partial installation makes them unavailable, both concept tools degrade cleanly while core memory remains available; run `marm-memory knowledge status`, then reinstall MARM if needed.
- **Isolated storage**: the concept graph lives in its own SQLite database (`~/.marm/index/marm_index.db`) with its own connection pool, so concept-graph writes can never block or corrupt the production memory database.
- **Console atlas**: the Knowledge Graph opens in a compact, deterministic connected sample for fast navigation. Choose **Render all _N_ nodes** when you need the complete atlas. Full-atlas mode keeps background relationship lines hidden until you hover or select a node, so its direct connections remain readable without drawing the whole spiderweb at once.

This fills the cross-session structure gap that flat memory search leaves open: sessions organize memories, but the concept graph *connects* them, so "what depends on the write queue?" is answerable even when the answer spans five sessions from three different agents.

## Architecture & Internals

Everything above runs on a small number of deliberate mechanisms. This section is the full map, so you (or your agent) never have to guess what the server is doing.

### Storage engine

- **SQLite in WAL mode** at `~/.marm/marm_memory.db` with a connection pool (5 connections). WAL keeps readers unblocked during writes, which matters when several agents recall while one writes.
- **FTS5 full-text index** (`memories_fts`) is maintained as an external-content table over the memories table and powers both the exact lane (BM25) and the filter stage of hybrid recall.
- **Chunk storage**: memories past ~180 words are split into overlapping 150-token chunks (50-token overlap) in a `memory_chunks` table, each with its own embedding. Recall scores chunks and collapses to the parent memory.
- **Embeddings** come from the fastembed-backed `jinaai/jina-embeddings-v2-small-en` encoder: 33M parameters, 512 dimensions, an 8,192-token context window, and an Apache-2.0 license. It does not require separate query/document text prefixes. The encoder is lazily loaded on first semantic use and serialized behind a lock so concurrent encodes can't corrupt each other. If it is unavailable, writes still succeed; memories are stored without embeddings until it loads. Semantic scoring runs as a single NumPy batch (matrix cosine) rather than a Python loop.
- **The concept graph gets its own database** (`~/.marm/index/marm_index.db`) and its own pool, reusing the same pool implementation but never sharing connections with the memory store. Deliberate isolation: an experimental graph build must not be able to stall the production WAL. The one exception is the indexing queue, which lives in the memory database on purpose so a memory and its indexing task commit together; the graph itself stays derived and disposable.

### Write path

- **Serialized write queue** (enabled by default): all memory writes flow through one internal async worker, eliminating SQLite writer contention under multi-agent load. The queue is generic; compaction applies go through the same worker, so there is exactly one writer no matter which subsystem is writing. `MAX_QUEUE_SIZE` bounds it.
- **Write-time consolidation** (opt-in, `CONSOLIDATION_ENABLED=1`) runs two layers before a memory lands:
  - **Layer 1, exact dedup**: a SHA-256 hash of normalized content is checked within the session; hash hits are verified against the actual content before deduplicating, so a hash collision stores a new row instead of silently merging different content.
  - **Layer 2, semantic merge**: near-duplicates above `CONSOLIDATION_THRESHOLD` cosine similarity are merged rather than accumulated. This never blocks a write; if the encoder isn't available, the write proceeds unconsolidated.
  - The tradeoff is measured and published: roughly 9x median write cost (58ms vs 6.5ms) in exchange for a store that stays clean, because reads dominate memory workloads. See section 3 of the benchmarks above.
- **Concept indexing is a durable outbox**: a write records an indexing task in the same transaction as the memory, so a memory cannot exist without one. A background worker drains that queue and writes the concept graph. Nothing on the write path waits for extraction, and a process killed mid-extraction loses no work because the task is a row rather than an in-memory job. Both transports run a worker, so the two coordinate through a leased lock in the memory database rather than an in-process lock, which would not span them.
- **Compaction** (opt-in, `COMPACTION_ENABLED=1`) is Layer 3: after enough writes in a session, a background pass detects clusters of related memories using cosine similarity plus union-find connected components, gated by minimum cluster size, minimum age, and an active-session grace period so it never compacts work in flight. MARM then injects a bounded request asking the connected agent to summarize each cluster: `candidates` → `stage` → `review` → `apply` or `discard`. Source memory IDs are preserved on apply, so compacted summaries stay traceable to their originals. Staged summaries expire (`COMPACTION_STAGING_TTL_HOURS`), nudges are capped and cooldown-limited, and the injection has a byte budget. The design is honest about what LLMs are for: MARM detects, the agent summarizes, and a human-reviewable stage/apply/discard loop gates the destructive step.

### Recall path

Covered in [Understanding MARM Memory](#understanding-marm-memory): exact lane (FTS5 BM25 + LIKE fallback), filter→rerank (bounded FTS candidates → batch semantic rerank → temporal blend), bounded semantic fallback with an explicit truncation flag, and chunk-collapse scoring. Recall depth (`detail=1/2/3`) controls how much of each memory is returned, and every MCP response passes through a **1MB response limiter** that truncates content intelligently instead of breaking the protocol.

### Code graph subprocess protocol

The bundled graph engine runs as a supervised child process, not an import:

- **Transport**: newline-delimited JSON-RPC 2.0 over the child's stdio, with a verified handshake (initialize → capture server version → initialized notification).
- **Envelope care**: responses are scanned for the first JSON-parseable content item rather than assuming index 0, because the upstream binary can prepend an update notice. Tool errors arrive as `result.isError`, not JSON-RPC errors, and are converted to clean `{"status": "error"}` dicts with the upstream's own remediation hint attached.
- **Serialization**: one lock guards each write+read round trip on the single stdin pipe; async callers go through `asyncio.to_thread` so the event loop never blocks on subprocess IO.
- **Crash recovery**: stderr is drained on a background thread, child EOF/crash is detected, and the process is transparently respawned on the next call. Timeouts are deliberately *not* treated as crashes; a long index run may still be working, and killing it would destroy in-flight work.
- **Supervision**: a lazy singleton supervisor owns the client for the process lifetime. Startup is triggered by the first graph-tool call or by the auto-index worker if the engine binary is already downloaded, never raises into the MCP layer, and verifies the pinned binary's tool schema so upstream drift is caught at startup instead of mid-call.
- **Auto re-indexing is filesystem watched, with a git content signature and a reconciliation fallback**: a bundled watcher wakes the worker on a save, commit, branch switch, or merge; matching events are debounced so a burst becomes one re-index. For a git repository, the trigger is confirmed by hashing the diff against `HEAD` plus a fingerprint of non-ignored untracked files, computed outside the engine so an idle check costs no engine lock and two different edits to the same already-modified file are told apart instead of read as identical. A periodic reconciliation pass catches a missed watcher event, covers a filesystem that cannot be watched, and is the only trigger for a directory that is not a git repo. Git runs with `core.fsmonitor` disabled and a scrubbed environment, since that setting names a program git would otherwise execute from a watched repository.
- **One gate for every store mutation**: manual indexes on all three surfaces, the auto-index worker, and project deletion all pass through a single leased row in the memory database. HTTP and STDIO are separate processes with separate engine children over one shared engine store, so an in-process lock cannot span them. The lease is released when the engine call actually returns rather than when its caller stops waiting: a cancelled request cannot hand the store to another process while the engine is still writing to it.

### Security & rate limiting

- **Two-mode auth gate**: keyless on loopback (`127.0.0.1`), `MARM_API_KEY` (Bearer) mandatory the moment the server is network-exposed (`SERVER_HOST=0.0.0.0`, Docker). `--generate-key` produces one. Safe by default, zero setup friction locally.
- **IP-based rate limiting** with sliding windows and temporary blocks, tuned through CLI presets rather than a config maze (table below).
- **Local-first**: everything lives under `~/.marm/`; no cloud sync, no telemetry, no external storage.
- **Graceful shutdown**: SIGTERM/SIGINT handlers drain and close the connection pool cleanly, and an internal event system runs automation callbacks with per-callback error isolation and timeouts so one bad hook can't wedge the server.

### Swarm & multi-agent presets

| Flag | Rate Limit | Write Queue | Use When |
| ------ | ------------ | ------------- | ---------- |
| *(none)* | 80 RPM | enabled | Normal local use and small 3-5 agent setups |
| `--swarm` | 200 RPM | enabled | Shared HTTP server, roughly 15-30 agents depending on write style |
| `--swarm-max` | 600 RPM | enabled | Heavier local/private swarm, roughly 50-100 agents depending on write style |
| `--trusted` | disabled | enabled | Private/trusted deployments only |
| `--rate-limit-rpm N` | N RPM | unchanged | Custom override; 0 disables limiting |

The write queue serializes memory writes regardless of preset; swarm flags tune the HTTP rate limit on top of that. The queue controls write ordering; consolidation and compaction are separate memory-maintenance layers. This stack (WAL + pooling + one serialized writer + RPM presets) is intentionally scoped to "SQLite, many agents, one machine"; distributed multi-node memory is out of scope for the current design.

### Self-maintaining documentation

Packaged docs are indexed into the `marm_system` memory namespace on startup and refreshed every 50 tool calls, with source-file hash tracking so unchanged docs are skipped and changed or deleted rows are re-indexed. Connected agents can answer MARM usage questions with `marm_smart_recall` instead of you pasting docs at them.

### Configuration reference

<details>
<summary><strong>Environment variables (defaults in parentheses)</strong></summary>

| Variable | Default | What it controls |
| ---------- | --------- | ------------------ |
| `SERVER_HOST` | `127.0.0.1` | Bind address; `0.0.0.0` exposes the server and makes `MARM_API_KEY` mandatory |
| `SERVER_PORT` | `8001` | HTTP port |
| `MARM_API_KEY` | *(empty)* | Bearer key for network-exposed deployments |
| `MARM_DB_PATH` | `~/.marm/marm_memory.db` | Memory database location |
| `MARM_CONCEPT_DB_PATH` | `~/.marm/index/marm_index.db` | Concept graph database location |
| `MARM_PROJECT` / `MARM_PLATFORM` | *(auto-detected)* | Override project/platform attribution |
| `MARM_RATE_LIMIT_RPM` | `80` | Requests per minute per IP (presets override) |
| `WRITE_QUEUE_ENABLED` | `1` | Serialize writes through one worker |
| `FTS_CANDIDATE_LIMIT` | `200` | BM25 candidates fetched before semantic reranking; raise for stores with weak keyword overlap, lower to tighten results to the closest keyword matches |
| `RECALL_SCAN_LIMIT` | `10000` | Cap on the semantic fallback scan; `recall_scan_truncated=true` in responses means it was hit |
| `FTS_QUERY_MODE` | `or_nostop` | How semantic recall builds its keyword query: `or_nostop` ignores filler words then matches any remaining term, `or` matches any term, `and` requires every term (the pre-2.31.0 behavior). The exact/lexical lane always requires every term. |
| `FTS_EXTRA_STOPWORDS` | *(empty)* | Comma-separated extra words to ignore when building keyword queries, for terms so common in your store they carry no signal |
| `HYBRID_SEARCH_TEXT_WEIGHT` | `0.05` | How much the keyword score influences ranking. Set from a benchmark sweep; accuracy peaks across `0.04`-`0.08` and falls off sharply above `0.10`. At `0.0`, keyword matching narrows which memories are considered but does not reorder them. |
| `FTS_LONE_HIT_SCORE` | `1.0` | Keyword score used when only one memory matches, or when every match ties. Lower it on small stores if a single keyword match should not count as a perfect one. |
| `SEMANTIC_SEARCH_ENABLED` | `1` | Set to `0` to run without the embedding model: nothing is loaded, no embeddings are written, and recall falls back to keyword matching. Useful on low-memory hosts, or to see how recall behaves when the model is unavailable. `marm-memory doctor` reports when it is off. |
| `TEMPORAL_WEIGHT` / `TEMPORAL_HALF_LIFE_DAYS` | `0.1` / `30` | Strength and decay of the recency boost |
| `CONSOLIDATION_ENABLED` | `0` | Write-time dedup + semantic merge |
| `CONSOLIDATION_THRESHOLD` | `0.92` | Cosine similarity needed to merge near-duplicates. Compared against meaning-similarity alone, not the blended ranking score |
| `COMPACTION_ENABLED` | `0` | Background cluster detection + agent-assisted compaction |
| `COMPACTION_TRIGGER_COUNT` | `5` | Writes per session before a compaction pass |
| `COMPACTION_SIMILARITY_THRESHOLD` / `COMPACTION_MIN_CLUSTER_SIZE` / `COMPACTION_MIN_AGE_HOURS` | `0.88` / `3` / `24` | Cluster detection gates |
| `COMPACTION_STAGING_TTL_HOURS` | `168` | How long staged summaries wait before expiring |
| `GRAPH_ENABLED` | `true` | Kill switch for the 5 code-graph tools |
| `GRAPH_AUTO_INDEX` | `true` | Automatic re-indexing of repos already in the code graph. A saved switch from `projects auto off` or `marm_graph_index(action="auto_off")` overrides this, so a value set here cannot re-enable what a user turned off |
| `GRAPH_AUTO_INDEX_DEBOUNCE_SECONDS` | `2` | Quiet period after a watcher event before a repo is evaluated, so a burst of saves becomes one re-index. Minimum 0.5 |
| `GRAPH_AUTO_INDEX_RECONCILE_SECONDS` | `300` | Fallback pass that catches a missed watcher event, covers a filesystem that cannot be watched, and is the only trigger for a directory that is not a git repo. Minimum 60. Replaces the deprecated `GRAPH_AUTO_INDEX_FULL_INTERVAL`, whose value carries over automatically if this is unset. `GRAPH_AUTO_INDEX_INTERVAL` (the old fixed poll) is deprecated and no longer read for anything but a warning |
| `GRAPH_AUTO_INDEX_MODE` | `moderate` | Index depth for automatic re-indexes: `full`, `moderate`, or `fast`. Anything else warns and falls back |
| `GRAPH_AUTO_INDEX_LEASE_SECONDS` | `120` | How long the indexing gate stays owned once nothing is renewing it. A running index renews its own lease, so this bounds how long a *killed* process blocks indexing, not how long an index may take |
| `GRAPH_AUTO_INDEX_PROJECT_TTL` | `300` | How long the list of watched projects is trusted before it is re-read from the engine |
| `CONCEPT_BUILD_ROW_CAP` | `500` | Memory rows read per page during a concept-graph build. Not a cap on the build: every memory in scope is read either way |
| `CONCEPT_AUTO_INDEX` | `true` | Automatic concept indexing of new memories. `false`, `0`, `no`, or `off` stops the worker and leaves builds manual. Writes still record queue rows either way |
| `CONCEPT_INDEX_DEBOUNCE_SECONDS` | `30` | Quiet period after a write before indexing starts, so a burst becomes one pass |
| `CONCEPT_INDEX_BATCH_SIZE` | `20` | Memories indexed per batch, capped at 500. Lowering it does not reduce contention; it measured slightly worse |
| `CONCEPT_INDEX_BATCH_PAUSE_MS` | `250` | Pause between batches while clearing a backlog. Cuts worst-case recall during indexing from ~270ms to ~80ms for about 18% longer drain. `0` disables it |
| `CONCEPT_INDEX_LEASE_SECONDS` | `300` | How long a claimed indexing task stays owned once nothing is renewing it. Work in progress renews its own lease, so this bounds how long a *killed* process holds tasks, not how long a batch may take. Reclaimed tasks spend no attempt |
| `CONCEPT_INDEX_MAX_ATTEMPTS` | `3` | Failed attempts before a memory is parked with its error instead of retried |

</details>

## Troubleshooting

<details>
<summary><strong>Upgrading Embeddings</strong></summary>

The Jina v2 Small default uses 512-dimensional embeddings; older `all-MiniLM-L6-v2` data is 384-dimensional and must be re-embedded. Stop every MARM HTTP and STDIO process, then run:

```bash
marm-memory maintenance embeddings migrate
```

It re-embeds memory, chunk, and any existing concept-graph vectors (notebook scratch entries no longer carry embeddings), reports progress, verifies both databases, and is resumable after an interruption. It refuses to start against a live HTTP server; STDIO processes cannot be detected reliably and must be stopped manually.

### Repair Chunked Memories

Memories over 500 words are also stored as smaller chunks. Chunk sizing changed across versions, and the migration above re-embeds chunks without re-splitting them, so older chunks keep stale boundaries. Stop every MARM process, then run:

```bash
marm-memory maintenance chunks rechunk
```

It re-splits stale chunks, fills in any lost to an interrupted write, and drops chunks from memories now under the threshold. Memories already correct are skipped without loading the encoder, so rerunning costs nothing. Same live-server guard as above, plus it refuses when stored vectors do not match the configured embedding model: migrate first in that case. Recall works without this, just less accurately on long memories.

</details>

<details>
<summary><strong>Server issues</strong></summary>

**Server won't start**

- Check Python version: `python --version` (must be 3.10+)
- Verify port 8001 isn't in use: `lsof -i :8001` (macOS/Linux) or `netstat -ano | findstr :8001` (Windows)
- Check for permission errors in home directory (`~/.marm/` must be readable/writable)
- See platform-specific troubleshooting: [INSTALL-DOCKER.md](docs/INSTALL-DOCKER.md), [INSTALL-WINDOWS.md](docs/INSTALL-WINDOWS.md), [INSTALL-MACOS.md](docs/INSTALL-MACOS.md), [INSTALL-LINUX.md](docs/INSTALL-LINUX.md)

**STDIO connection fails**

- Verify `marm-mcp-stdio` is on your PATH after pip install: `marm-mcp-stdio --help`
- Alternatively, use: `python -m marm_mcp_server.server_stdio`
- Check AI client documentation for STDIO transport requirements
- Try direct execution to see error messages: `python -m marm_mcp_server.server_stdio`

</details>

<details>
<summary><strong>Connection & integration</strong></summary>

**AI client can't connect to MARM**

- Verify the server is running with `curl http://localhost:8001/health`
- Check the firewall isn't blocking port 8001
- For STDIO: use `marm-mcp-stdio` (console script) or `python -m marm_mcp_server.server_stdio`
- Restart both server and AI client

**Tools not appearing in AI client**

- Verify HTTP mode with `curl http://localhost:8001/health`
- Check server logs for initialization errors
- Disconnect and reconnect AI client to refresh tool list
- Both HTTP and STDIO expose 14 tools: 7 core memory/logging/notebook/compaction tools, 5 bundled code-graph tools, and 2 concept-graph tools

**Graph tools return `graph backend unavailable`**

- Confirm `GRAPH_ENABLED` is not set to `false` (affects both HTTP and STDIO; graph tools have full parity across both transports)
- First graph use may take longer while the pinned codebase-memory engine starts or downloads locally
- In Docker, the graph engine binary is baked into the image; local pip installs may fetch it on first graph use
- Core memory tools continue working even when graph startup fails

**Concept tools return `entities_extracted: 0`**

- First confirm that a scoped concept build actually includes memories with extractable entities.
- Run `marm-memory knowledge status`; if it reports a missing runtime or model, repair the install with `python -m pip install -U --force-reinstall marm-mcp-server`.

**New memories are not showing up in the graph**

- Run `marm-memory knowledge status`. `index_queue.pending` is how many memories are waiting; `index_queue.parked` is how many gave up. `auto_index: false` means indexing is switched off.
- Give it the debounce interval (30 seconds by default) plus extraction time. A burst of writes is indexed as one pass, not one per memory.
- Check that `CONCEPT_AUTO_INDEX` is not set to `false`, `0`, `no`, or `off`.
- A graph awaiting a rebuild is not indexed into. If the Console or `marm-memory knowledge status` reports `rebuild_required`, run `marm_concept_build(search_all=True)` once; queued memories are picked up after it.
- Automatic indexing only covers memories written since the upgrade. Run a build once to bring in everything older.
- A memory that fails extraction three times is parked rather than retried forever. The reason is recorded with the task.

**Code changes are not showing up in the code graph**

- Run `marm-memory projects auto status`. `enabled: false` means automatic re-indexing is switched off; `source: override` means a saved switch is what turned it off, not the environment.
- The repo has to be indexed once before it is watched. `marm-memory projects list` shows what is enrolled.
- Give it the debounce window (2 seconds by default) plus index time. If nothing happens after that, the reconciliation pass (5 minutes by default) is the backstop.
- A project deleted from the Console stays suppressed on purpose, so a stale watch list cannot recreate it. Indexing it explicitly re-enrolls it.
- Automatic indexing needs the graph engine, which stays dormant until the engine binary has been downloaded. Any graph tool call downloads it once.

**An index returns `index_in_progress`**

- Another MARM process holds the indexing gate, usually the other transport's poller or a Console index job. Deleting a project reports the same thing, since a delete during an index would be undone by it. Run it again in a moment.

**A build returns `build_in_progress`**

- Another MARM process is writing the graph, usually the other transport's indexing worker. Builds are short unless it is a full rebuild; run it again in a moment.

**A build returns `lock_lost`**

- The build was stalled long enough for another process to take over the graph, so it stopped partway rather than writing alongside it. Usually a suspended machine or a debugger pause. Whatever it indexed before stopping is kept, and re-running the build finishes the rest.

</details>

<details>
<summary><strong>Memory & data issues</strong></summary>

**Memories not saving**

- Verify `~/.marm/` directory exists and has write permissions
- Check available disk space
- Test with simple memory: ask AI to save a single line and check with `marm_log_show`
- For HTTP mode, verify server health with `curl http://localhost:8001/health`

**Search returns no results**

- Verify memories exist: use `marm_log_show` to list entries
- Use `search_all=True` to search across all sessions
- Try simpler, more general search queries
- Wait a few seconds; first semantic search loads the ML model

**Memories appear then disappear**

- Check if MARM was restarted or crashed (data persists in `~/.marm/`)
- Verify disk space didn't fill up
- Check system logs for database errors

**Lost or corrupted data**

- Stop the server immediately
- Check `~/.marm/` directory for backup copies (if you created them)
- Restore from backup: copy your backup `~/.marm/` back to the home directory
- Restart server

**Database locked error**

- Close all AI client connections
- Stop the server: `Ctrl+C`
- Back up the entire database directory: `cp -r ~/.marm ~/.marm.backup`
- Check for processes holding the database: `lsof ~/.marm/marm_memory.db` (macOS/Linux) or check Task Manager (Windows)
- If a process is holding the lock, terminate it
- Verify database integrity: `sqlite3 ~/.marm/marm_memory.db "PRAGMA integrity_check;"`
- If integrity check fails, restore from your backup
- If integrity check passes, the lock should be released; restart server

</details>

<details>
<summary><strong>Performance</strong></summary>

**Slow search results**

- First search is slower (model loads from disk); subsequent searches are faster
- Large databases (1000+ memories) may take a few seconds
- Limit searches: use `limit=10` instead of unlimited results
- Use `marm_summary` to compress old sessions

**Server using too much memory**

- Notebooks with many entries can accumulate; use `marm_notebook(action="clear")` to prune active entries
- Close unused AI client connections
- Use `marm_compaction(action="review")` to inspect staged compaction summaries when compaction is enabled

</details>

<details>
<summary><strong>Common error messages</strong></summary>

| Error | Cause | Solution |
| ------- | ------- | ---------- |
| `address already in use` | Port 8001 occupied | Kill process on 8001 or use different port |
| `permission denied: ~/.marm/` | Database directory not writable | `chmod 755 ~/.marm/` or check ownership |
| `module not found: core.memory` | Missing dependencies | Reinstall from `marm-mcp-server/`: `pip install -e ".[dev]"` |
| `database is locked` | Multiple processes accessing DB | Close other connections, restart server |
| `embedding model not found` | Semantic search model didn't download | First run takes time; be patient, check internet connection |

</details>

For memory behavior, transports, supported clients, compaction, and backup questions, see the [FAQ](docs/FAQ.md).

## Star History

<a href="https://www.star-history.com/?type=date&repos=Lyellr88%2Fmarm-memory">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=Lyellr88/marm-memory&type=date&theme=dark&legend=top-left&sealed_token=JSVQqZYX5orThlbryur2eKfpdUWNbaVUYwF_fGqjUlmYXF7RhUlHXD5_2pAm-7IthxNbgDl4XDfrPclUxoZTnTjP4pm33Rjr6CsonJUOYsGH_VIjzpUxaA" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=Lyellr88/marm-memory&type=date&legend=top-left&sealed_token=JSVQqZYX5orThlbryur2eKfpdUWNbaVUYwF_fGqjUlmYXF7RhUlHXD5_2pAm-7IthxNbgDl4XDfrPclUxoZTnTjP4pm33Rjr6CsonJUOYsGH_VIjzpUxaA" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=Lyellr88/marm-memory&type=date&legend=top-left&sealed_token=JSVQqZYX5orThlbryur2eKfpdUWNbaVUYwF_fGqjUlmYXF7RhUlHXD5_2pAm-7IthxNbgDl4XDfrPclUxoZTnTjP4pm33Rjr6CsonJUOYsGH_VIjzpUxaA" />
 </picture>
</a>

## Contributing

MARM welcomes contributors at every level. Code helps, but so do docs, setup notes, client testing, bug reports, benchmarks, and real workflow feedback from people using AI tools every day.

Good places to help:

- Test MARM with more MCP clients, IDE agents, and operating systems
- Improve docs, screenshots, examples, and platform-specific setup notes
- Report bugs or confusing install steps with clear reproduction details
- Share memory workflows, agent habits, and tool ideas from real use
- Check out open [issues](https://github.com/Lyellr88/marm-memory/issues)

> 💡 Want to get your name on this list? Check out our [CONTRIBUTING.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/CONTRIBUTING.md) guide to get started!

## Join the MARM Community

**Help build the future of AI memory - no coding required!**

**Connect:** [MARM Discord](https://discord.gg/nhyJWPz2cf) | [GitHub Discussions](https://github.com/Lyellr88/marm-memory/discussions)

## License & Usage Notice

Copyright © 2026 Ryan A. Lyell. MARM is released under the [Apache 2.0 License](LICENSE) (see [NOTICE](NOTICE) for the copyright statement), and forks, experiments, and integrations are welcome. MARM also wraps third-party open-source components such as `codebase-memory-mcp` under MIT; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution. If you build on it, please make unofficial versions easy to distinguish from releases published by the [official MARM repository](https://github.com/Lyellr88/marm-memory) so users know what they are installing.

## Project Documentation

### **Usage Guides**

- **[README.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/README.md)** - This file: complete usage guide, tool reference, workflows, and architecture
- **[PROTOCOL.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/docs/PROTOCOL.md)** - MCP operating protocol
- **[FAQ.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/docs/FAQ.md)** - Answers to common questions about using MARM

### **MCP Server Installation**

- **[INSTALL-DOCKER.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/docs/INSTALL-DOCKER.md)** - Docker deployment (recommended)
- **[INSTALL-WINDOWS.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/docs/INSTALL-WINDOWS.md)** - Windows installation guide
- **[INSTALL-MACOS.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/docs/INSTALL-MACOS.md)** - macOS installation guide
- **[INSTALL-LINUX.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/docs/INSTALL-LINUX.md)** - Linux installation guide
- **[INSTALL-PLATFORMS.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/docs/INSTALL-PLATFORMS.md)** - Platform installation guide

### **Project Information**

- **[CONTRIBUTING.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/CONTRIBUTING.md)** - How to contribute to MARM
- **[CHANGELOG.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/CHANGELOG.md)** - Version history and updates
- **[ACKNOWLEDGMENTS.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/docs/ACKNOWLEDGMENTS.md)** - Contributors and acknowledgments
- **[ROADMAP.md](https://github.com/Lyellr88/marm-memory/blob/MARM-main/docs/ROADMAP.md)** - Planned features and development roadmap
- **[LICENSE](https://github.com/Lyellr88/marm-memory/blob/MARM-main/LICENSE)** - Apache 2.0 license terms
