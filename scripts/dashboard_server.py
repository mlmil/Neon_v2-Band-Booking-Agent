import csv
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# Ensure we can import from scripts
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.post_gig_payout_tool import build_payout_row, upsert_payout_row


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
                payout_rows[row['gig_id']] = row

    items = []
    for q in queue_rows:
        if q.get('queue_status') not in ('needs_closeout', 'closed'):
            continue

        gig_id = q['gig_id']
        p = payout_rows.get(gig_id, {})

        is_test = "babaloo" in str(q.get("venue", "")).lower()

        # Determine status. The UI uses specific strings (success, needs_review, blocked, pending)
        # We map payout status to dashboard status.
        pay_status = p.get('payment_status')
        if pay_status == 'paid_complete':
            status = 'success'
        elif pay_status in ('partial_payment', 'needs_review'):
            status = 'needs_review'
        elif pay_status == 'payment_pending':
            status = 'pending'
        else:
            status = 'needs_review' if q.get('queue_status') == 'needs_closeout' else 'success'

        item = {
            "id": gig_id,
            "status": status,
            "venue": q.get('venue'),
            "city": q.get('city'),
            "date": q.get('date'),
            "base_pay": p.get('base_pay_received') if p.get('base_pay_received') else None,
            "tips": p.get('tips_received') if p.get('tips_received') else None,
            "method": p.get('payment_method') if p.get('payment_method') else None,
            "received_by": p.get('received_by') if p.get('received_by') else None,
            "still_owed": p.get('still_owed') if p.get('still_owed') else None,
            "paid_complete": pay_status == 'paid_complete',
            "notes": p.get('notes', ''),
            "summary": "TEST DATA: " + q.get('next_step', '') if is_test else q.get('next_step', '')
        }

        items.append(item)
    return items

def handle_post_gig_payout(payload, payouts_path):
    if payload.get("payment_status") == "paid_complete":
        raise ValueError("Cannot mark paid_complete through safe local save endpoint.")

    received = _money(payload.get("base_pay_received", "0"))
    if "still_owed" in payload:
        still_owed = _money(payload.get("still_owed", "0"))
        expected = received + still_owed
    else:
        expected = _money(payload.get("base_pay_expected", "0"))

    row = build_payout_row(
        gig_id=payload.get("gig_id", ""),
        venue=payload.get("venue", ""),
        city=payload.get("city", ""),
        date=payload.get("date", ""),
        base_pay_expected=expected,
        base_pay_received=received,
        tips_received=payload.get("tips_received", "0"),
        payment_method=payload.get("payment_method", ""),
        payment_handle=payload.get("payment_handle", ""),
        received_by=payload.get("received_by", ""),
        payment_status=payload.get("payment_status", ""),
        notes=payload.get("notes", "")
    )
    receipt = upsert_payout_row(payouts_path, row)
    return {"receipt": receipt, "row": row}

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
