#!/usr/bin/env python3
"""
Seed script for TechVision GmbH mock data.

Reads all email threads and documents from the mock_data directory,
parses frontmatter metadata, and POSTs each to the Contaixt API.

Usage:
    python mock_data/seed.py --api-url http://localhost:8000 --workspace-id <uuid>

Options:
    --api-url           Base URL of the Contaixt API (default: http://localhost:8000)
    --workspace-id      UUID of the target workspace (required)
    --source-connection-id  UUID for the source connection (default: auto-generated)
    --dry-run           Parse and print documents without POSTing
"""

import argparse
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

import httpx

MOCK_DATA_DIR = Path(__file__).parent


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from a markdown file."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter_str = match.group(1)
    body = match.group(2)

    metadata = {}
    for line in frontmatter_str.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip().strip('"').strip("'")

    return metadata, body


def split_email_messages(body: str) -> list[dict]:
    """Split an email thread body into individual messages.

    Each message starts with '## Message N' and contains From/To/Date headers.
    """
    # Split on ## Message N headers
    parts = re.split(r"(?=^## Message \d+)", body, flags=re.MULTILINE)
    messages = []

    for part in parts:
        part = part.strip()
        if not part or not part.startswith("## Message"):
            continue

        # Extract message number
        num_match = re.match(r"## Message (\d+)", part)
        msg_num = int(num_match.group(1)) if num_match else len(messages) + 1

        # Extract headers
        from_match = re.search(
            r"\*\*From:\*\*\s*(.+?)(?:<(.+?)>)?\s*$", part, re.MULTILINE
        )
        to_match = re.search(r"\*\*To:\*\*\s*(.+?)$", part, re.MULTILINE)
        date_match = re.search(r"\*\*Date:\*\*\s*(.+?)$", part, re.MULTILINE)

        # Get the message body (everything after the headers)
        # Find the last header line, then take everything after
        header_end = 0
        for header in [r"\*\*From:\*\*", r"\*\*To:\*\*", r"\*\*Date:\*\*", r"\*\*CC:\*\*"]:
            m = re.search(header + r".*$", part, re.MULTILINE)
            if m:
                header_end = max(header_end, m.end())

        msg_body = part[header_end:].strip() if header_end > 0 else part

        author_name = from_match.group(1).strip() if from_match else None
        author_email = from_match.group(2).strip() if from_match and from_match.group(2) else None
        date_str = date_match.group(1).strip() if date_match else None

        created_at = None
        if date_str:
            try:
                created_at = datetime.fromisoformat(date_str).isoformat()
            except ValueError:
                pass

        messages.append(
            {
                "message_num": msg_num,
                "author_name": author_name,
                "author_email": author_email,
                "to": to_match.group(1).strip() if to_match else None,
                "created_at": created_at,
                "body": msg_body,
            }
        )

    return messages


def load_emails(emails_dir: Path) -> list[dict]:
    """Load all email thread files and return individual documents for ingestion."""
    documents = []

    for filepath in sorted(emails_dir.glob("*.md")):
        content = filepath.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(content)

        thread_id = metadata.get("thread_id", filepath.stem)
        subject = metadata.get("subject", filepath.stem)

        messages = split_email_messages(body)

        for msg in messages:
            # Build content text including subject context
            content_text = f"Subject: {subject}\n"
            if msg["to"]:
                content_text += f"To: {msg['to']}\n"
            content_text += f"\n{msg['body']}"

            doc = {
                "source_type": "gmail",
                "external_id": f"{thread_id}_msg{msg['message_num']:03d}",
                "title": subject,
                "author_name": msg["author_name"],
                "author_email": msg["author_email"],
                "created_at": msg["created_at"],
                "content_text": content_text,
            }
            documents.append(doc)

    return documents


def load_documents(docs_dir: Path) -> list[dict]:
    """Load all document files and return documents for ingestion."""
    documents = []

    for filepath in sorted(docs_dir.glob("*.md")):
        content = filepath.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(content)

        doc = {
            "source_type": metadata.get("source_type", "notion"),
            "external_id": metadata.get("doc_id", filepath.stem),
            "title": metadata.get("title", filepath.stem),
            "author_name": metadata.get("author", None),
            "content_text": body.strip(),
        }
        documents.append(doc)

    return documents


def ingest_document(
    client: httpx.Client,
    api_url: str,
    workspace_id: str,
    source_connection_id: str,
    doc: dict,
) -> dict:
    """POST a single document to the ingest endpoint."""
    payload = {
        "workspace_id": workspace_id,
        "source_connection_id": source_connection_id,
        "source_type": doc["source_type"],
        "external_id": doc["external_id"],
        "content_text": doc["content_text"],
    }

    # Add optional fields
    for field in ["title", "author_name", "author_email", "url", "created_at", "updated_at"]:
        if doc.get(field):
            payload[field] = doc[field]

    resp = client.post(f"{api_url}/v1/ingest/document", json=payload)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Seed TechVision mock data into Contaixt")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Contaixt API base URL")
    parser.add_argument("--workspace-id", required=True, help="Target workspace UUID")
    parser.add_argument(
        "--source-connection-id",
        default=None,
        help="Source connection UUID (default: auto-generated)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse files without POSTing")
    args = parser.parse_args()

    source_connection_id = args.source_connection_id or str(uuid.uuid4())

    emails_dir = MOCK_DATA_DIR / "emails"
    docs_dir = MOCK_DATA_DIR / "documents"

    # Load all data
    print("Loading email threads...")
    email_docs = load_emails(emails_dir) if emails_dir.exists() else []
    print(f"  Found {len(email_docs)} individual email messages")

    print("Loading documents...")
    doc_docs = load_documents(docs_dir) if docs_dir.exists() else []
    print(f"  Found {len(doc_docs)} documents")

    all_docs = email_docs + doc_docs
    print(f"\nTotal documents to ingest: {len(all_docs)}")
    print(f"Workspace ID: {args.workspace_id}")
    print(f"Source Connection ID: {source_connection_id}")

    if args.dry_run:
        print("\n--- DRY RUN ---")
        for i, doc in enumerate(all_docs, 1):
            print(
                f"  [{i:3d}] {doc['source_type']:6s} | {doc['external_id']:30s} | "
                f"{doc.get('title', 'N/A')[:50]}"
            )
        print(f"\nDry run complete. {len(all_docs)} documents would be ingested.")
        return

    # Ingest all documents
    print("\nStarting ingestion...")
    stats = {"created": 0, "updated": 0, "unchanged": 0, "errors": 0}

    with httpx.Client(timeout=30.0) as client:
        for i, doc in enumerate(all_docs, 1):
            try:
                result = ingest_document(
                    client, args.api_url, args.workspace_id, source_connection_id, doc
                )
                status = result.get("status", "unknown")
                stats[status] = stats.get(status, 0) + 1
                print(
                    f"  [{i:3d}/{len(all_docs)}] {status:10s} | {doc['external_id']:30s} | "
                    f"{doc.get('title', 'N/A')[:50]}"
                )
            except httpx.HTTPStatusError as e:
                stats["errors"] += 1
                print(
                    f"  [{i:3d}/{len(all_docs)}] ERROR      | {doc['external_id']:30s} | "
                    f"{e.response.status_code}: {e.response.text[:100]}"
                )
            except httpx.RequestError as e:
                stats["errors"] += 1
                print(
                    f"  [{i:3d}/{len(all_docs)}] ERROR      | {doc['external_id']:30s} | "
                    f"Connection error: {e}"
                )

    print(f"\nIngestion complete!")
    print(f"  Created:   {stats['created']}")
    print(f"  Updated:   {stats['updated']}")
    print(f"  Unchanged: {stats['unchanged']}")
    print(f"  Errors:    {stats['errors']}")

    if stats["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
