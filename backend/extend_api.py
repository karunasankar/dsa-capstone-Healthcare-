import sqlite3
from database import DB_PATH

def extend_main():
    with open('main.py', 'r') as f:
        content = f.read()

    addition = """
@app.get("/users")
def get_users(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT username, role FROM users WHERE active = 1')
    rows = cursor.fetchall()
    conn.close()
    return {"users": [dict(r) for r in rows]}

@app.get("/audit-logs")
def get_audit_logs(current_user: dict = Depends(require_roles(["ADMIN"]))):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM audit_logs ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return {"logs": [dict(r) for r in rows]}

@app.get("/dashboard/stats")
def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM records')
    total_records = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM record_shares WHERE active = 1')
    active_shares = cursor.fetchone()[0]
    conn.close()
    
    return {
        "total_records": total_records,
        "blocks": len(blockchain.chain),
        "active_shares": active_shares,
        "chain_valid": blockchain.is_chain_valid(),
        "merkle_root": blockchain.get_latest_block().merkle_root if len(blockchain.chain) > 0 else ""
    }

@app.get("/merkle/tree")
def get_merkle_tree(current_user: dict = Depends(get_current_user)):
    # Returns the full merkle tree to render
    tree = MerkleTree(current_leaves)
    return {
        "root": tree.get_root(),
        "leaves": current_leaves,
        "levels": tree.get_tree_structure(),
        "record_map": {v: k for k, v in record_hash_map.items()} # map hash to record_id
    }
"""
    if "@app.get(\"/merkle/tree\")" not in content:
        with open('main.py', 'a') as f:
            f.write(addition)
        print("Extended main.py successfully")
    else:
        print("Already extended")

if __name__ == "__main__":
    extend_main()
