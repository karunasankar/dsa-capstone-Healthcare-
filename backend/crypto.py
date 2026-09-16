import hashlib
import json
import time
from typing import List, Dict, Any

def hash_data(data: str) -> str:
    """Returns SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def canonical_record_hash(record: dict) -> str:
    """Returns SHA-256 hash of a canonical representation of a record."""
    # Ensure consistent ordering and exclude metadata fields like 'record_hash'
    canonical_dict = {k: v for k, v in record.items() if k != 'record_hash'}
    canonical_string = json.dumps(canonical_dict, sort_keys=True)
    return hash_data(canonical_string)

class MerkleTree:
    def __init__(self, leaves: List[str]):
        self.leaves = leaves
        self.tree = []
        self.build_tree()

    def build_tree(self):
        if not self.leaves:
            self.tree = [[]]
            return
        
        current_level = self.leaves
        self.tree = [current_level]
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # Duplicate last element if odd number of leaves
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = left + right
                next_level.append(hash_data(combined))
            self.tree.append(next_level)
            current_level = next_level

    def get_tree_structure(self):
        return self.tree

    def update_leaf(self, index: int, new_hash: str):
        if not self.tree or index < 0 or index >= len(self.tree[0]):
            return
        self.tree[0][index] = new_hash
        current_index = index
        for level_idx in range(len(self.tree) - 1):
            current_level = self.tree[level_idx]
            next_level = self.tree[level_idx + 1]
            is_right = current_index % 2 != 0
            if is_right:
                left = current_level[current_index - 1]
                right = current_level[current_index]
            else:
                left = current_level[current_index]
                right = current_level[current_index + 1] if current_index + 1 < len(current_level) else left
            new_parent_hash = hashlib.sha256((left + right).encode()).hexdigest()
            parent_index = current_index // 2
            next_level[parent_index] = new_parent_hash
            current_index = parent_index

    def get_root(self) -> str:
        if not self.tree or not self.tree[-1]:
            return ""
        return self.tree[-1][0]

    def get_proof(self, index: int) -> List[Dict[str, str]]:
        proof = []
        if not self.leaves or index < 0 or index >= len(self.leaves):
            return proof
            
        for level in self.tree[:-1]:
            is_right_node = index % 2 != 0
            sibling_index = index - 1 if is_right_node else index + 1
            
            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
                proof.append({
                    "position": "left" if is_right_node else "right",
                    "hash": sibling_hash
                })
            else:
                proof.append({
                    "position": "right",
                    "hash": level[index]
                })
            index = index // 2
            
        return proof

    @staticmethod
    def verify_proof(leaf: str, proof: List[Dict[str, str]], root: str) -> bool:
        current_hash = leaf
        for p in proof:
            if p["position"] == "left":
                combined = p["hash"] + current_hash
            else:
                combined = current_hash + p["hash"]
            current_hash = hash_data(combined)
        return current_hash == root

class Block:
    def __init__(self, index: int, previous_hash: str, merkle_root: str, record_ids: List[str], timestamp: float = None):
        self.index = index
        self.timestamp = timestamp or time.time()
        self.merkle_root = merkle_root
        self.previous_hash = previous_hash
        self.record_ids = record_ids
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        # Commit to index, timestamp, merkle root, previous hash, and the transaction list
        block_data = f"{self.index}{self.timestamp}{self.merkle_root}{self.previous_hash}{''.join(self.record_ids)}"
        return hash_data(block_data)

    @classmethod
    def from_dict(cls, data: dict):
        b = cls(data['index'], data['previous_hash'], data['merkle_root'], data['record_ids'], data['timestamp'])
        b.hash = data['hash']
        return b

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, "0", "", ["genesis"])
        self.chain.append(genesis_block)

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, merkle_root: str, record_ids: List[str]) -> Block:
        latest_block = self.get_latest_block()
        new_block = Block(
            index=latest_block.index + 1,
            previous_hash=latest_block.hash,
            merkle_root=merkle_root,
            record_ids=record_ids
        )
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True
    def get_tree_structure(self) -> List[List[str]]:
        return self.tree
