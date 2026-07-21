#!/Users/cthulhu/.hermes/hermes-agent/venv/bin/python
"""Narrow Google People API client for approved Neon Blonde contacts."""
from __future__ import annotations

import argparse
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
CLIENT_FILE = Path(os.environ.get(
    "NEON_GOOGLE_PEOPLE_CLIENT", ROOT / ".secrets/google_people_client.json"
)).expanduser()
TOKEN_FILE = Path(os.environ.get(
    "NEON_GOOGLE_PEOPLE_TOKEN", ROOT / ".secrets/google_people_token.json"
)).expanduser()
PROPOSAL_DIR = ROOT / "data/contacts/pending"
SCOPES = ["https://www.googleapis.com/auth/contacts"]


def credentials(interactive: bool = False) -> Credentials:
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not interactive:
            raise RuntimeError("Google Contacts is not authorized; run the auth command")
        if not CLIENT_FILE.exists():
            raise FileNotFoundError(f"OAuth client file not found: {CLIENT_FILE}")
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True)
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(TOKEN_FILE, 0o600)
    return creds


def service():
    return build("people", "v1", credentials=credentials(), cache_discovery=False)


def search(query: str) -> list[dict]:
    result = service().people().searchContacts(
        query=query,
        readMask="names,emailAddresses,phoneNumbers,organizations,biographies",
        pageSize=20,
    ).execute()
    contacts = []
    for item in result.get("results", []):
        person = item.get("person", {})
        contacts.append({
            "resource_name": person.get("resourceName"),
            "names": [n.get("displayName") for n in person.get("names", [])],
            "emails": [e.get("value") for e in person.get("emailAddresses", [])],
            "phones": [p.get("value") for p in person.get("phoneNumbers", [])],
        })
    return contacts


def propose(args) -> dict:
    if not args.email and not args.phone:
        raise ValueError("A contact requires an email or phone number")
    proposal_id = uuid.uuid4().hex[:10]
    proposal = {
        "proposal_id": proposal_id,
        "status": "PENDING_APPROVAL",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "name": args.name.strip(),
        "email": args.email.strip().lower(),
        "phone": args.phone.strip(),
        "role": args.role.strip(),
        "notes": args.notes.strip(),
        "approval_text": f"APPROVE CONTACT {proposal_id}",
    }
    PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)
    path = PROPOSAL_DIR / f"{proposal_id}.json"
    path.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return proposal


def commit(proposal_id: str, approval: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{10}", proposal_id):
        raise ValueError("Invalid proposal ID")
    path = PROPOSAL_DIR / f"{proposal_id}.json"
    proposal = json.loads(path.read_text(encoding="utf-8"))
    if proposal.get("status") != "PENDING_APPROVAL":
        raise RuntimeError(f"Proposal is not pending: {proposal.get('status')}")
    if approval.strip() != proposal.get("approval_text"):
        raise PermissionError("Exact approval text does not match this proposal")

    duplicate_query = proposal.get("email") or proposal.get("phone") or proposal["name"]
    duplicates = search(duplicate_query)
    if duplicates:
        return {"created": False, "status": "DUPLICATE_REVIEW", "matches": duplicates}

    body = {"names": [{"displayName": proposal["name"]}]}
    if proposal.get("email"):
        body["emailAddresses"] = [{"value": proposal["email"], "type": "work"}]
    if proposal.get("phone"):
        body["phoneNumbers"] = [{"value": proposal["phone"], "type": "work"}]
    details = "\n".join(x for x in [proposal.get("role"), proposal.get("notes")] if x)
    if details:
        body["biographies"] = [{"value": details, "contentType": "TEXT_PLAIN"}]
    created = service().people().createContact(body=body).execute()
    proposal.update({
        "status": "CREATED",
        "created_resource_name": created.get("resourceName"),
        "committed_at": datetime.now(timezone.utc).isoformat(),
    })
    path.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return {"created": True, "resource_name": created.get("resourceName")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("auth")
    search_parser = sub.add_parser("search")
    search_parser.add_argument("query")
    proposal_parser = sub.add_parser("propose")
    proposal_parser.add_argument("--name", required=True)
    proposal_parser.add_argument("--email", default="")
    proposal_parser.add_argument("--phone", default="")
    proposal_parser.add_argument("--role", default="")
    proposal_parser.add_argument("--notes", default="")
    commit_parser = sub.add_parser("commit")
    commit_parser.add_argument("proposal_id")
    commit_parser.add_argument("--approval", required=True)
    args = parser.parse_args()

    if args.command == "auth":
        credentials(interactive=True)
        output = {"authorized": True, "scope": SCOPES}
    elif args.command == "search":
        output = search(args.query)
    elif args.command == "propose":
        output = propose(args)
    else:
        output = commit(args.proposal_id, args.approval)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
