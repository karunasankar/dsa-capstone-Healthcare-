import os
import sys
import time
import json
import uuid
import random
import string
import hashlib
import statistics
import csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto import MerkleTree, canonical_record_hash

def get_random_record():
    return {
        "record_id": str(uuid.UUID(int=random.getrandbits(128))),
        "patient_id": f"PAT-{random.randint(1, 1000)}",
        "record_type": random.choice(["Blood Test", "X-Ray"]),
        "diagnosis": "Condition " + "".join(random.choices(string.ascii_letters, k=5)),
        "date": "2026-09-10",
        "provider": f"DOC-{random.randint(1, 50)}",
        "value": str(random.random() * 100)
    }

def run_audit():
    print("=== 1. MERKLE PROOF STATS ===")
    sizes = [1000, 10000, 100000, 500000, 1000000]
    for size in sizes:
        hashes = [hashlib.sha256(str(i).encode()).hexdigest() for i in range(size)]
        tree = MerkleTree(hashes)
        
        # Test proof verify 100 times
        times = []
        for _ in range(100):
            target_idx = random.randint(0, size-1)
            # Gen proof
            path = []
            curr = target_idx
            for level in tree.tree[:-1]:
                sibling = curr + 1 if curr % 2 == 0 else curr - 1
                if sibling < len(level):
                    path.append((level[sibling], curr % 2 == 0))
                curr //= 2
            
            # Verify
            start = time.perf_counter()
            curr_hash = hashes[target_idx]
            for p, is_left in path:
                if is_left:
                    curr_hash = hashlib.sha256((curr_hash + p).encode()).hexdigest()
                else:
                    curr_hash = hashlib.sha256((p + curr_hash).encode()).hexdigest()
            end = time.perf_counter()
            times.append((end - start) * 1000) # ms
            
        print(f"Size: {size:7d} | Mean: {statistics.mean(times):.5f} ms | Std: {statistics.stdev(times):.5f} ms | Min: {min(times):.5f} ms | Max: {max(times):.5f} ms")


    print("\n=== 2. INCREMENTAL UPDATE CORRECTNESS ===")
    test_hashes = [hashlib.sha256(str(i).encode()).hexdigest() for i in range(100000)]
    tree_inc = MerkleTree(test_hashes.copy())
    
    # Update 10 leaves
    for idx in range(10):
        new_h = hashlib.sha256(f"tamper_{idx}".encode()).hexdigest()
        tree_inc.update_leaf(idx, new_h)
        test_hashes[idx] = new_h
        
    tree_full = MerkleTree(test_hashes)
    print(f"Incremental Root: {tree_inc.get_root()}")
    print(f"Full Rebuild Root: {tree_full.get_root()}")
    print(f"Match: {tree_inc.get_root() == tree_full.get_root()}")

    print("\n=== 3. TAMPERING EXPERIMENT ===")
    # Simulate tampering scenarios locally
    cases = 1000
    detected = 0
    
    # We'll simulate tampering the hash in the leaves array and checking if root matches
    # Since we know AES-GCM tags would catch ciphertext tampering, we test the Merkle layer here:
    original_hashes = [hashlib.sha256(str(i).encode()).hexdigest() for i in range(1000)]
    t_tree = MerkleTree(original_hashes.copy())
    original_root = t_tree.get_root()
    
    for _ in range(cases):
        tampered_hashes = original_hashes.copy()
        idx = random.randint(0, 999)
        tampered_hashes[idx] = hashlib.sha256(b"tampered").hexdigest()
        
        tampered_tree = MerkleTree(tampered_hashes)
        if tampered_tree.get_root() != original_root:
            detected += 1
            
    print(f"Total cases: {cases}")
    print(f"Detected: {detected}")
    print(f"Undetected: {cases - detected}")
    print(f"Detection Rate: {(detected/cases)*100:.2f}%")

if __name__ == '__main__':
    run_audit()
