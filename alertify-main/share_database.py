"""Copy this computer's ALERTIFY database into database/ so it can be shared via GitHub.

Run:   python share_database.py
Then:  git add database/alertify.db && git commit -m "Update shared database" && git push

On another computer, delete its instance/alertify.db (if any) and start the app:
it copies database/alertify.db in automatically on first run, with the same
accounts, reports and admin changes.

Note: the GitHub repository is public. Passwords are stored only as hashes,
but anyone can download the accounts' names, emails and reports.
"""
import os
import sqlite3

from app import LOCAL_DB, SHARED_DB


SUMMARY_TABLES = ("users", "disaster_reports", "evacuation_centers", "notifications")


def dump(path):
    """All of a database's data as SQL text, used to tell whether anything changed."""
    with sqlite3.connect(path) as conn:
        return "\n".join(conn.iterdump())


def share_database(src=LOCAL_DB, dest=SHARED_DB):
    """Copy src to dest with SQLite's backup API, but only if the data changed.

    The backup API is safe even while the app is running, unlike copying the file.
    Skipping identical data keeps git from seeing a "changed" file every time.
    Returns (changed, row counts for a few tables).
    """
    if not os.path.exists(src):
        raise SystemExit(f"No local database at {src}. Run the app once first.")
    changed = not os.path.exists(dest) or dump(src) != dump(dest)
    if changed:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with sqlite3.connect(src) as source, sqlite3.connect(dest) as target:
            source.backup(target)
    with sqlite3.connect(dest) as target:
        counts = {t: target.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in SUMMARY_TABLES}
    return changed, counts


if __name__ == "__main__":
    changed, summary = share_database()
    print(f"Shared database {'updated' if changed else 'already up to date (no data changed)'}: {SHARED_DB}")
    for table, n in summary.items():
        print(f"{n:>5}  {table}")
