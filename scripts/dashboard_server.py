from __future__ import annotations
import csv
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import glob
import re
import csv
from datetime import datetime, timezone

# Ensure we can import from scripts
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.post_gig_payout_tool import build_payout_row, upsert_payout_row
from scripts.agentmail_health_check import agentmail_request


def _money(value):
    try:
        return max(float(value or 0), 0)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid money value: {value!r}")


def is_test_payout(payload):
    identity = " ".join(
        str(payload.get(field, "")) for field in ("gig_id", "venue")
    ).lower()
    return "babaloo" in identity or "bobaloo" in identity


def get_post_gig_data(queue_path, payouts_path):
    queue_rows = []
    if os.path.exists(queue_path):
        with open(queue_path, newline='', encoding='utf-8') as f:
            queue_rows = list(csv.DictReader(f))

    payout_rows = {}
    if os.path.exists(payouts_path):
        with open(payouts_path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                # The authoritative CSV has DATE and VENUE, no gig_id
                from scripts.post_gig_payout_tool import row_key
                k = row_key(row.get("DATE", ""), row.get("VENUE", ""))
                payout_rows[k] = row

    items = []
    for q in queue_rows:
        if q.get('queue_status') not in ('needs_closeout', 'closed'):
            continue

        gig_id = q['gig_id']
        from scripts.post_gig_payout_tool import row_key
        k = row_key(q.get("date", ""), q.get("venue", ""))
        p = payout_rows.get(k, {})

        is_test = "babaloo" in str(q.get("venue", "")).lower()

        # Without advanced status tracking in the CSV, a gig is successful if it has base pay.
        has_pay = bool(p.get("PAYOUT"))
        if has_pay:
            status = 'success'
        else:
            status = 'needs_review' if q.get('queue_status') == 'needs_closeout' else 'success'

        item = {
            "id": gig_id,
            "status": status,
            "venue": q.get('venue'),
            "city": q.get('city'),
            "date": q.get('date'),
            "base_pay": p.get('PAYOUT') if p.get('PAYOUT') else None,
            "tips": p.get('TIPS') if p.get('TIPS') else None,
            "method": None,
            "received_by": None,
            "still_owed": None,
            "paid_complete": has_pay,
            "notes": "",
            "summary": "TEST DATA: " + q.get('next_step', '') if is_test else q.get('next_step', '')
        }

        items.append(item)
    return items

def handle_post_gig_payout(payload, payouts_path):
    if payload.get("payment_status") == "paid_complete":
        pass # Not blocking since payment_status doesn't persist anyway

    received = _money(payload.get("base_pay_received", "0"))
    if "still_owed" in payload:
        still_owed = _money(payload.get("still_owed", "0"))
        expected = received + still_owed
    else:
        expected = _money(payload.get("base_pay_expected", "0"))

    row = build_payout_row(
        venue=payload.get("venue", ""),
        city=payload.get("city", ""),
        date=payload.get("date", ""),
        base_pay_received=received,
        tips_received=payload.get("tips_received", "0"),
    )
    receipt = upsert_payout_row(payouts_path, row)
    return {"receipt": receipt, "row": row}

def get_health_projection():
    from scripts.lm_studio_health_check import run_health_check as lm_studio_check
    lm_result = lm_studio_check()

    status = lm_result.get("status", "blocked")
    code = lm_result.get("code")
    model = (
        lm_result.get("active_model_display_name")
        or lm_result.get("active_model")
        or "No model loaded"
    )

    if code == "LM_STUDIO_OK":
        message = f"Local model ONLINE with {model} loaded."
    elif code == "LM_STUDIO_NO_MODEL_LOADED":
        message = "Local model server ONLINE, but no model is loaded."
    else:
        message = "Local model OFFLINE. Folder creation still succeeds; digest skipped."

    return {
        "status": status,
        "title": "Local model",
        "model": model,
        "message": message,
        "last_ok": datetime.now(timezone.utc).isoformat() if status == "success" else None,
        "pending_digests": [],
    }

def get_intake_receipts(receipts_dir: Path) -> list[dict]:
    items = []
    if not receipts_dir.exists():
        return items
    for path in receipts_dir.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            status = data.get("status")
            if status in ("ignored", "duplicate"):
                continue
            req = data.get("request", {})
            src = data.get("source", {})
            items.append({
                "id": path.stem,
                "status": "needs_review" if status in ("needs_info", "needs_review", "action_needed") else "success",
                "received": data.get("created_at"),
                "sender": src.get("sender", ""),
                "venue": req.get("venue", "Unknown Venue"),
                "city": req.get("city", ""),
                "date": req.get("date"),
                "time": req.get("time"),
                "missing": req.get("missing_fields", []),
                "summary": data.get("next_step", ""),
                "ack_draft": data.get("acknowledgment_draft", ""),
                "receipt_file": str(path)
            })
        except Exception as e:
            pass
    # Sort by created_at desc
    items.sort(key=lambda x: x.get("received") or "", reverse=True)
    return items

def get_groupme_activity(db_path: Path) -> list[dict]:
    items = []
    if not db_path.exists():
        return items
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = data.get("messages", {})
        for msg_id, msg in messages.items():
            if msg.get("system") or msg.get("sender_id") == "system":
                continue
            group_name = msg.get("group_name", "")
            # Filter to operational groups
            if "neon blonde" not in group_name.lower():
                continue
            # Basic non-operational filter
            text = msg.get("text") or ""
            if len(text.split()) < 3 and "?" not in text:
                continue # ignore short chatty msgs unless it's a question
            items.append({
                "id": msg_id,
                "group": group_name,
                "sender": msg.get("name", "Unknown"),
                "timestamp": msg.get("created_at"),
                "text": text[:100] + ("..." if len(text) > 100 else ""),
            })
    except Exception as e:
        pass
    items.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)
    return items[:50]

def get_venue_folders(venues_dir: Path) -> list[dict]:
    items = []
    if not venues_dir.exists():
        return items
    # Format: Venues/Venue Name/Venue Name - YYYY-MM-DD/
    for venue_dir in venues_dir.iterdir():
        if not venue_dir.is_dir() or venue_dir.name.startswith("_"):
            continue
        for gig_dir in venue_dir.iterdir():
            if not gig_dir.is_dir():
                continue
            # Check for receipt and digest
            has_receipt = (gig_dir / "LOCAL_GIG_RECEIPT.md").exists()
            has_digest = (gig_dir / "LOCAL_MODEL_DIGEST.md").exists()

            # Is it in the future?
            match = re.search(r"(\d{4}-\d{2}-\d{2})", gig_dir.name)
            if not match:
                continue
            date_str = match.group(1)

            # Simple status logic
            status = "success"
            note = "Synced & reviewed."
            if not has_digest:
                status = "needs_review"
                note = "Digest missing."

            items.append({
                "id": gig_dir.name,
                "status": status,
                "venue": venue_dir.name,
                "date": date_str,
                "path": str(gig_dir),
                "receipt": has_receipt,
                "digest": has_digest,
                "reviewed": has_digest, # proxy for reviewed
                "note": note
            })
    items.sort(key=lambda x: x["date"], reverse=True)
    return items

def get_scout_leads(csv_path: Path) -> list[dict]:
    items = []
    if not csv_path.exists():
        return items
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                status = row.get("status", "needs_review").lower()
                if status in ("ignored", "rejected"):
                    continue
                items.append({
                    "id": row.get("id", ""),
                    "status": status,
                    "venue": row.get("venue_name", "Unknown"),
                    "city": row.get("city", ""),
                    "signal": row.get("notes", ""),
                    "found": row.get("date_added", ""),
                    "fit": row.get("fit_score", "Medium")
                })
    except Exception as e:
        pass
    return items

def run_accuracy_checks():
    try:
        from scripts.bandsheet_verification_report import run_live_check as bandsheet_check
        from scripts.website_verification_report import run_live_check as website_check

        b_res = bandsheet_check()
        w_res = website_check()

        now = datetime.now(timezone.utc).isoformat()

        return [
            {
                "id": "CHK-BANDSHEET",
                "kind": "bandsheet",
                "title": "Band Sheet verification",
                "script": "scripts/bandsheet_verification_report.py",
                "status": b_res.get("status", "blocked"),
                "last_run": now,
                "result": f"{len(b_res.get('mismatches', []))} mismatches found." if b_res.get("mismatches") else "All synced.",
                "detail": "Compares public Google Calendar against published private Band Sheet JSON.",
            },
            {
                "id": "CHK-WEBSITE",
                "kind": "website",
                "title": "Website verification",
                "script": "scripts/website_verification_report.py",
                "status": w_res.get("status", "blocked"),
                "last_run": now,
                "result": f"{len(w_res.get('mismatches', []))} mismatches found." if w_res.get("mismatches") else "All synced.",
                "detail": "Compares public WordPress show posts against the Band Sheet.",
            }
        ], b_res, w_res
    except Exception as e:
        return [], {}, {}

def run_agentmail_check():
    try:
        from scripts.agentmail_health_check import run_health_check
        res = run_health_check()
        return [{
            "id": "AS-AGENTMAIL",
            "key": "agentmail",
            "title": "AgentMail",
            "status": res.get("status", "blocked"),
            "script": "scripts/agentmail_health_check.py",
            "last_check": datetime.now(timezone.utc).isoformat(),
            "message": f"Health check result: {res.get('code', 'UNKNOWN')}.",
            "blocks": "Send email" if res.get("status") != "success" else None
        }]
    except Exception as e:
        return []

def get_agentmail_threads(api_key: str | None = None) -> list[dict] | dict:
    if not api_key:
        api_key = os.environ.get("AGENTMAIL_API_KEY")
    if not api_key:
        return {"error": "Missing key"}
    try:
        status, body = agentmail_request(api_key, "/v0/inboxes/neon_blonde@agentmail.to/threads")
        if status != 200 or not isinstance(body, dict):
            return {"error": f"API error {status}"}

        threads = body.get("threads", [])
        result = []
        for t in threads[:20]:
            labels = t.get("labels", [])
            senders = t.get("senders", [])

            # Simple status derivation
            t_status = "Closed"
            direction = "inbound"
            latest_sender = senders[0] if senders else "Unknown"

            if "neon_blonde@agentmail.to" in latest_sender or "neonblondevc@gmail.com" in latest_sender:
                direction = "outbound"
                t_status = "Waiting"
            else:
                direction = "inbound"
                if "unread" in labels:
                    t_status = "Needs reply"
                else:
                    t_status = "Closed"

            if "draft" in labels:
                t_status = "Draft"

            result.append({
                "thread_id": t.get("thread_id"),
                "subject": t.get("subject", "No Subject"),
                "participants": t.get("senders", []) + t.get("recipients", []),
                "latest_sender": latest_sender,
                "latest_timestamp": t.get("timestamp"),
                "message_count": t.get("message_count", 1),
                "preview": (t.get("preview") or "")[:200],
                "direction": direction,
                "status": t_status
            })
        return result
    except Exception as e:
        return {"error": str(e)}

def get_agentmail_thread_detail(api_key: str | None, thread_id: str) -> dict:
    if not api_key:
        api_key = os.environ.get("AGENTMAIL_API_KEY")
    if not api_key:
        return {"error": "Missing key"}

    try:
        status, body = agentmail_request(api_key, f"/v0/inboxes/neon_blonde@agentmail.to/threads/{thread_id}")
        if status != 200 or not isinstance(body, dict):
            return {"error": "Fetch failed"}

        msgs = body.get("messages", [])
        extracted_msgs = []
        for m in msgs:
            text = m.get("extracted_text") or m.get("text") or m.get("preview") or ""
            extracted_msgs.append({
                "message_id": m.get("message_id"),
                "sender": m.get("from", "Unknown"),
                "timestamp": m.get("timestamp"),
                "text": text
            })

        # sort chronological (oldest first)
        extracted_msgs.sort(key=lambda x: x.get("timestamp") or "")

        return {
            "thread_id": thread_id,
            "subject": body.get("subject"),
            "messages": extracted_msgs
        }
    except Exception as e:
        return {"error": str(e)}

def get_calendar_gigs(b_res: dict, w_res: dict) -> list[dict]:
    # We can use the calendar data fetched in the bandsheet check,
    # but the check function doesn't return the raw gigs list easily.
    # We will fetch basic.ics here to build the gigs array.
    try:
        from scripts.bandsheet_verification_report import fetch_text, parse_calendar_ics, PUBLIC_CALENDAR_ICS_URL, filter_gigs_on_or_after
        from datetime import date
        ics = fetch_text(PUBLIC_CALENDAR_ICS_URL)
        gigs = filter_gigs_on_or_after(parse_calendar_ics(ics), date.today())

        b_mismatches = b_res.get("mismatches", [])
        w_mismatches = w_res.get("mismatches", [])

        items = []
        for gig in gigs:
            g_id = f"GIG-{gig.get('date')}-{re.sub(r'[^a-z0-9]', '', gig.get('venue', '').lower())}"
            # find if blocked by mismatch
            b_match = any(m.get("calendar", {}).get("date") == gig["date"] for m in b_mismatches if "calendar" in m)
            w_match = any(m.get("website", {}).get("date") == gig["date"] for m in w_mismatches if "website" in m)

            items.append({
                "id": g_id,
                "status": "blocked" if b_match else ("needs_review" if w_match else "success"),
                "venue": gig.get("venue"),
                "city": gig.get("city"),
                "date": gig.get("date"),
                "time": gig.get("time"),
                "calendar_event": True,
                "bandsheet_match": not b_match,
                "website_match": not w_match,
                "folder_id": "",
                "promo_status": "published" if not w_match else "not_started",
                "confirmed": not b_match,
                "logistics": ["Mismatch found."] if (b_match or w_match) else [],
                "summary": "Check details."
            })
        return items
    except Exception as e:
        return []

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve static files from dashboard/
        kwargs['directory'] = str(REPO_ROOT / "dashboard")
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/post-gig':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            queue_path = REPO_ROOT / "data" / "post_gig" / "queue.csv"
            payouts_path = REPO_ROOT / "data" / "post_gig" / "payouts.csv"

            data = get_post_gig_data(queue_path, payouts_path)
            self.wfile.write(json.dumps(data).encode('utf-8'))
        elif parsed_path.path == '/api/health':
            projection = get_health_projection()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(projection).encode('utf-8'))
        elif parsed_path.path.startswith('/api/agentmail/threads/'):
            thread_id = parsed_path.path.split('/')[-1]
            data = get_agentmail_thread_detail(None, thread_id)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        elif parsed_path.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            # Build the big NEON_DATA structure
            intake_path = REPO_ROOT / "data" / "intake" / "receipts"
            groupme_path = REPO_ROOT / "data" / "groupme" / "groupme_db.json"
            venues_path = REPO_ROOT / "Venues"
            scout_path = REPO_ROOT / "Scout Agent" / "scout-leads.csv"

            checks, b_res, w_res = run_accuracy_checks()

            resp = {
                "meta": {
                    "now": datetime.now(timezone.utc).isoformat(),
                    "band": "Neon Blonde",
                    "operator": "Mike",
                    "project_path": str(REPO_ROOT),
                    "venues_path": str(venues_path),
                    "calendar_url": "https://calendar.google.com/calendar/u/0/r",
                    "bandsheet_url": "https://mlmil.github.io/NeonBlonde-Bandsheet/docs/bandsheet-data.json",
                    "last_full_sync": datetime.now(timezone.utc).isoformat()
                },
                "intake_receipts": get_intake_receipts(intake_path),
                "gigs": get_calendar_gigs(b_res, w_res),
                "venue_folders": get_venue_folders(venues_path),
                "checks": checks,
                "post_gig_items": get_post_gig_data(REPO_ROOT / "data" / "post_gig" / "queue.csv", REPO_ROOT / "data" / "post_gig" / "payouts.csv"),
                "agent_status": run_agentmail_check(),
                "agentmail_threads": get_agentmail_threads(),
                "local_model_digest": get_health_projection(),
                "scout_leads": get_scout_leads(scout_path),
                "groupme_activity": get_groupme_activity(groupme_path)
            }
            self.wfile.write(json.dumps(resp).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/post-gig/payout':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                payload = json.loads(body)

                if is_test_payout(payload):
                    # For Club Babaloo, we use a temporary/test ledger during manual verification
                    payouts_path = REPO_ROOT / "data" / "post_gig" / "test_payouts.csv"
                else:
                    payouts_path = REPO_ROOT / "data" / "post_gig" / "payouts.csv"

                resp_data = handle_post_gig_payout(payload, payouts_path)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(resp_data).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=8787):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    print(f"Server running at http://127.0.0.1:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    run_server()
