import csv
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.post_gig_queue_sync import QueueGig, fetch_calendar_queue_gigs

FIELDNAMES = ["VENUE", "CITY", "DATE", "PAYOUT", "TIP_JAR", "VENMO"]

ADMIN_LEDGER = Path("/Volumes/VADER/Manifold/Neon_Blonde/Administrative/PAYOUT TRACKING SPREADSHEET/neon-blonde_Payouts 2026.csv")
NUMBERS_SOURCE = Path("/Volumes/VADER/Manifold/Neon_Blonde/Administrative/PAYOUT TRACKING SPREADSHEET/📄-neon-blonde_Payouts 2026.numbers")

def normalize_money(value: object) -> str:
    if value is None:
        return ""
    val_str = str(value).strip()
    if not val_str or val_str.lower() in ("missing value", "none"):
        return ""
    val_str = val_str.replace("$", "").replace(",", "")
    try:
        f = float(val_str)
        return f"${f:.2f}"
    except ValueError:
        return ""

def normalize_venue(value: str) -> str:
    v = value.lower().strip()
    v = re.sub(r"^gig at\s+", "", v)
    v = v.replace("'", "").replace("&", "and")
    v = re.sub(r"[^\w\s]", "", v)
    v = re.sub(r"\s+", " ", v).strip()

    # Aliases logic
    aliases = {
        "the cruisery": "cruisery",
        "parque 1055": "parquee 1055",
        "sewer": "the sewer",
        "tonys pizza": "tonys pizza",
        "m special": "ms special",
        "harrys night club and beach bar": "harrys",
        "harrys nightclub": "harrys",
        "fox wine co topa topa": "fox wine",
        "fox wine company": "fox wine",
        "fig mountain sb": "fig mountain",
        "fig mt los olivos": "fig mountain",
        "santa barbara yacht club": "yacht club",
        "fess parkers": "fess parker",
    }
    return aliases.get(v, v)

def normalize_date(value: object) -> str:
    val_str = str(value).strip()
    if not val_str:
        return ""
    try:
        if "T" in val_str:
            return datetime.fromisoformat(val_str).date().isoformat()
        if "/" in val_str:
            parts = val_str.split("/")
            if len(parts) == 3:
                m, d, y = map(int, parts)
                return f"{y:04d}-{m:02d}-{d:02d}"
        if "-" in val_str:
            parts = val_str.split("-")
            if len(parts) == 3:
                return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    except Exception:
        pass
    return val_str

def row_key(row: dict[str, str]) -> tuple[str, str]:
    return (row.get("DATE", ""), normalize_venue(row.get("VENUE", "")))

def normalize_row(row: dict[str, object]) -> dict[str, str]:
    tip_jar_source = row.get("Tip Jar", row.get("TIP_JAR", row.get("Tips", row.get("TIPS", ""))))
    return {
        "VENUE": str(row.get("Venue", row.get("VENUE", ""))).strip(),
        "CITY": str(row.get("City", row.get("CITY", ""))).strip(),
        "DATE": normalize_date(row.get("Date", row.get("DATE", ""))),
        "PAYOUT": normalize_money(row.get("Payout", row.get("PAYOUT", ""))),
        "TIP_JAR": normalize_money(tip_jar_source),
        "VENMO": normalize_money(row.get("Venmo", row.get("VENMO", ""))),
    }

def parse_numbers_rows(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    parsed = []
    for row in rows:
        norm = normalize_row(row)
        if norm["VENUE"] and norm["DATE"]:
            parsed.append(norm)
    return parsed

def parse_date(date_str: str) -> str:
    from dateutil import parser
    try:
        dt = parser.parse(date_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str

def export_numbers_rows(source: Path = NUMBERS_SOURCE) -> list[dict[str, object]]:
    script = f"""
    tell application "Numbers"
        set doc to open POSIX file "{source}"
        set theSheet to sheet "Neon Blonde Venues" of doc
        set theTable to table "Table 1" of theSheet

        set rowCount to count of rows of theTable

        set theData to ""

        repeat with i from 2 to rowCount
            set v to value of cell 1 of row i of theTable
            if v is not missing value then
                set c to value of cell 2 of row i of theTable
                set d to value of cell 3 of row i of theTable
                set p to value of cell 5 of row i of theTable
                set t to value of cell 6 of row i of theTable

                if c is missing value then set c to ""
                if d is missing value then set d to ""
                if p is missing value then set p to ""
                if t is missing value then set t to ""

                set theData to theData & v & "|||" & c & "|||" & d & "|||" & p & "|||" & t & "|||ROW|||"
            end if
        end repeat

        close doc without saving
        return theData
    end tell
    """

    script_path = REPO_ROOT / "scripts" / "temp_numbers_export.scpt"
    with open(script_path, "w") as f:
        f.write(script)

    try:
        subprocess.run(["open", "-a", "Numbers", str(source)], check=True)
        import time
        time.sleep(2)
        result = subprocess.run(["osascript", str(script_path)], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"osascript error: {result.stderr}")
            return []
    finally:
        if script_path.exists():
            script_path.unlink()

    out = result.stdout.strip()
    rows = []
    for line in out.split("|||ROW|||"):
        if not line:
            continue
        parts = line.split("|||")
        if len(parts) >= 5:
            d_parsed = parse_date(parts[2].strip())
            rows.append({
                "VENUE": parts[0].strip(),
                "CITY": parts[1].strip(),
                "DATE": d_parsed,
                "PAYOUT": parts[3].strip(),
                "TIP_JAR": parts[4].strip(),
                "VENMO": "",
            })
    return rows

def calendar_gig_to_row(gig: QueueGig) -> dict[str, str]:
    return {
        "VENUE": gig.venue,
        "CITY": gig.city,
        "DATE": datetime.fromisoformat(gig.start_at).date().isoformat(),
        "PAYOUT": "",
        "TIP_JAR": "",
        "VENMO": "",
    }

def merge_rows(
    existing_rows: list[dict[str, str]],
    calendar_gigs: list[QueueGig],
) -> tuple[list[dict[str, str]], dict[str, int]]:

    existing_by_key = {}
    for r in existing_rows:
        if r.get("VENUE", "") == "TOTAL":
            continue
        v_norm = normalize_venue(r.get("VENUE", ""))
        # Filter out old 2023 dates or known rehearsals
        if "rehearsal" in v_norm or "rehearsal" in r.get("VENUE", "").lower():
            continue
        if r.get("DATE", "").startswith("2023-"):
            continue
        existing_by_key[row_key(r)] = normalize_row(r)

    created = 0
    matched = 0

    for gig in calendar_gigs:
        row = calendar_gig_to_row(gig)
        v_norm = normalize_venue(row.get("VENUE", ""))
        # Filter out rehearsals
        if "rehearsal" in v_norm or "rehearsal" in row.get("VENUE", "").lower():
            continue
        if row.get("DATE", "").startswith("2023-"):
            continue

        # Hardcode drop for duplicate Fig Mountain gig on 2-07 (actual gig was 2-06)
        if v_norm == "fig mountain" and row.get("DATE") == "2026-02-07":
            continue

        k = row_key(row)
        if k in existing_by_key:
            matched += 1
            ex = existing_by_key[k]
            # preserve existing financial info and update others if needed, but keeping venue string as is might be better.
            # "Calendar changes update venue, city, and date fields when the existing row can be matched unambiguously."
            ex["VENUE"] = row["VENUE"]
            ex["CITY"] = ex.get("CITY") or row["CITY"]
            ex["DATE"] = row["DATE"]
        else:
            created += 1
            existing_by_key[k] = row

    final_rows = list(existing_by_key.values())
    final_rows.sort(key=lambda r: (r.get("DATE", ""), r.get("VENUE", "")))

    total_payout = 0.0
    total_tip_jar = 0.0
    total_venmo = 0.0
    for r in final_rows:
        try:
            total_payout += float(r.get("PAYOUT", "").replace("$", "").replace(",", ""))
        except ValueError:
            pass
        try:
            total_tip_jar += float(r.get("TIP_JAR", "").replace("$", "").replace(",", ""))
        except ValueError:
            pass
        try:
            total_venmo += float(r.get("VENMO", "").replace("$", "").replace(",", ""))
        except ValueError:
            pass

    total_row = {
        "VENUE": "TOTAL",
        "CITY": "ALL TIME",
        "DATE": "",
        "PAYOUT": f"${total_payout:.2f}" if total_payout > 0 else "",
        "TIP_JAR": f"${total_tip_jar:.2f}" if total_tip_jar > 0 else "",
        "VENMO": f"${total_venmo:.2f}" if total_venmo > 0 else "",
    }
    final_rows.insert(0, total_row)

    return final_rows, {"created": created, "matched": matched, "total": len(final_rows) - 1}

def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def write_csv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
        temp_name = f.name
    os.replace(temp_name, path)

def sync_payout_csv(ledger_path: Path = ADMIN_LEDGER, numbers_source: Path = NUMBERS_SOURCE) -> dict[str, object]:
    if not ledger_path.parent.exists():
        return {"status": "blocked", "reason": f"Missing directory: {ledger_path.parent}"}

    if not ledger_path.exists():
        # First time migration
        raw = export_numbers_rows(numbers_source)
        existing = parse_numbers_rows(raw)
    else:
        existing = read_csv_rows(ledger_path)

    try:
        gigs = fetch_calendar_queue_gigs()
    except Exception as e:
        return {"status": "blocked", "reason": f"Failed to fetch calendar: {e}"}

    merged, counts = merge_rows(existing, gigs)
    write_csv_atomic(ledger_path, merged)
    return counts

def main() -> int:
    result = sync_payout_csv()
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
