import pandas as pd
import matplotlib.pyplot as plt
import os

os.makedirs('plots', exist_ok=True)

def plot_verification():
    if not os.path.exists('results/verification_results.csv'): return
    df = pd.read_csv('results/verification_results.csv')
    plt.figure(figsize=(10, 6))
    plt.plot(df['dataset_size'], df['sha_only_time'], label='SHA-256 Only Verification', marker='o')
    plt.plot(df['dataset_size'], df['proof_verify_time'], label='Merkle Proof Verification', marker='s')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Number of Records')
    plt.ylabel('Time (seconds)')
    plt.title('Verification Time vs Dataset Size')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/verification_time.png')
    plt.close()

def plot_merkle_build():
    if not os.path.exists('results/merkle_results.csv'): return
    df = pd.read_csv('results/merkle_results.csv')
    plt.figure(figsize=(10, 6))
    plt.plot(df['dataset_size'], df['build_time'], marker='o', color='green')
    plt.xlabel('Number of Records')
    plt.ylabel('Time (seconds)')
    plt.title('Merkle Tree Construction Time')
    plt.grid(True)
    plt.savefig('plots/merkle_build_time.png')
    plt.close()

def plot_storage():
    if not os.path.exists('results/storage_results.csv'): return
    df = pd.read_csv('results/storage_results.csv')
    plt.figure(figsize=(10, 6))
    plt.plot(df['dataset_size'], df['plaintext_bytes'] / (1024*1024), label='Plaintext DB', marker='o')
    plt.plot(df['dataset_size'], df['total_proposed_bytes'] / (1024*1024), label='Proposed Arch Total', marker='s')
    plt.xlabel('Number of Records')
    plt.ylabel('Storage Size (MB)')
    plt.title('Storage Overhead Analysis')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/storage_analysis.png')
    plt.close()

def plot_memory():
    if not os.path.exists('results/merkle_results.csv'): return
    df = pd.read_csv('results/merkle_results.csv')
    plt.figure(figsize=(10, 6))
    plt.plot(df['dataset_size'], df['peak_mem_mb'], marker='o', color='purple')
    plt.xlabel('Number of Records')
    plt.ylabel('Peak Memory (MB)')
    plt.title('Memory Usage for Merkle Construction')
    plt.grid(True)
    plt.savefig('plots/memory_usage.png')
    plt.close()

def plot_updates():
    if not os.path.exists('results/update_results.csv'): return
    df = pd.read_csv('results/update_results.csv')
    plt.figure(figsize=(10, 6))
    plt.plot(df['dataset_size'], df['rebuild_10_time'], label='Full Tree Rebuild (O(n))', marker='o')
    plt.plot(df['dataset_size'], df['incremental_10_time'], label='Incremental Update (O(log n))', marker='s')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Number of Records in Tree')
    plt.ylabel('Time (seconds)')
    plt.title('Dynamic Update: Rebuild vs Incremental (10 Records)')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/dynamic_updates.png')
    plt.close()

if __name__ == "__main__":
    plot_verification()
    plot_merkle_build()
    plot_storage()
    plot_memory()
    plot_updates()
    print("Plots generated in plots/")
