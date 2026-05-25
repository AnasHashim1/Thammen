"""scripts/ — Sprint 2.21.4+ — operator scripts package.

Sprint 2.21.4 added this `__init__.py` so `connectors/developer_inventory_t3.py`
can import `DEFAULT_DB_PATH` from `migrate_developer_inventory.py` (Rule #40
single source of truth for the SQLite path). CLI usage of the scripts is
unaffected — they remain executable standalone via `python scripts/<name>.py`.
"""
