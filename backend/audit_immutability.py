# Audit Immutability - Enforce append-only audit logs
from pymongo.collection import Collection
from pymongo.write_concern import WriteConcern

async def insert_strict(col: Collection, doc: dict):
    """
    Insert with majority write concern to ensure durability
    Use this for all audit trail writes (settings_history, credits_ledger)
    """
    # Enforce majority write concern
    wc = WriteConcern(w="majority")
    col_w = col.with_options(write_concern=wc)
    return await col_w.insert_one(doc)

def forbid_update_delete(*args, **kwargs):
    """
    Helper to prevent accidental updates/deletes on audit collections
    Raise this in update/delete operations on audit collections
    """
    raise RuntimeError("Audit collections are append-only - updates and deletes are forbidden")
