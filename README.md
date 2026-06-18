# DrugScope

A command-line tool that queries the public [openFDA drug adverse event API](https://open.fda.gov/apis/drug/event/), aggregates the results, and prints a safety summary to the terminal — optionally exporting a report to JSON and/or CSV.

No API key is required.

---

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) (recommended) **or** pip

---

## Installation

**With uv (recommended):**

```bash
git clone <repo-url>
cd drugscope
uv sync
```

**With pip:**

```bash
git clone <repo-url>
cd drugscope
pip install -e .
```

---

## Usage

```
python main.py <drugname> [--limit N] [--output FILENAME] [--format json] [--format csv]
```
to run tests

```
uv run pytest drugscope/tests/test_aggregations.py -v
```

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `drugname` | Yes | — | Drug name to query (case-insensitive) |
| `--limit` | No | `100` | Maximum number of adverse event records to fetch |
| `--output` | No | — | Base filename for the exported report (no extension) |
| `--format` | No | `json csv` | Output format(s). Pass once per format. Only used when `--output` is set. |

---

## Examples

**Print a summary to the terminal:**
```bash
python main.py aspirin
```

**Fetch up to 200 records:**
```bash
python main.py ibuprofen --limit 200
```

**Export to both JSON and CSV:**
```bash
python main.py warfarin --output warfarin_report
# produces: warfarin_report.json and warfarin_report.csv
```

**Export to JSON only:**
```bash
python main.py warfarin --output warfarin_report --format json
```

**Export to CSV only:**
```bash
python main.py warfarin --output warfarin_report --format csv
```

**With uv run:**
```bash
uv run python main.py aspirin --output aspirin_report
```

---

## Output

### Terminal summary (always printed)

```
=== SAFETY SUMMARY FOR: ASPIRIN (100 Reports Evaluated) ===

[Severity]
Serious Reports: 72%(72)
Non-Serious:     28%(28)

[Top Adverse Reactions]
...

[Patient Demographics]
Sex:     45% Female | 55% Male
Average Age: 61.30
...

[Top Patient Outcomes]
...

[Top Concomitant Medications]
...
```

### Exported report fields (JSON/CSV)

- **Metadata** — drug name, total reports evaluated
- **Severity metrics** — serious vs. non-serious counts and percentages
- **Gender demographics** — male/female breakdown
- **Age demographics** — average age and cohort distribution (Pediatrics, Adults, Geriatrics)
- **Top 5 adverse reactions** — reaction term and report count
- **Top 3 clinical outcomes** — outcome label, count, and percentage
- **Top 3 concomitant medications** — co-administered drugs and frequency
