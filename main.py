import threading
import random
import math
from collections import Counter
from hashlib import sha3_256
import matplotlib.pyplot as plt

ALPHA, BETA, GAMMA = 8, 3, 2
THREADS = 4
BYTES_TO_GENERATE = 100_000_000
shared_x, shared_r = 0.36089632, 4.0
lock = threading.Lock()

def logistic(x, r): return x * r * (1.0 - x)
def normalize(x): return (x * 1000.0) - int(x * 1000.0)

def chaos_stage(x, r_prime, gamma=GAMMA):
    for _ in range(gamma):
        x = logistic(x, r_prime)
        x = normalize(x)
    return x

def trng_network(thread_id, byte_count, raw_bytes_out, processed_bytes_out):
    global shared_x, shared_r
    thread_raw, thread_processed = [], []
    
    for _ in range(byte_count):
        with lock:
            local_x, local_r = shared_x, shared_r
        
        thread_raw.append(int(local_x * 256.0) & 0xFF)
        x_processed, r_current = local_x, local_r
        
        y = []
        for _ in range(4):
            x_processed = chaos_stage(x_processed, r_current)
            y.append(3.86 + x_processed * 0.14)

        for _ in range(1, BETA):
            r_primes = [(y[0] + y[2])/2.0] * 2 + [(y[1] + y[3])/2.0] * 2 if x_processed >= 0.5 else [sum(y)/4.0] * 4
            y = []
            for r_p in r_primes:
                x_processed = chaos_stage(x_processed, r_p)
                y.append(3.86 + x_processed * 0.14)

        with lock:
            shared_x, shared_r = x_processed, sum(y)/4.0
        thread_processed.append(int(x_processed * 256.0) & 0xFF)

    raw_bytes_out[thread_id] = thread_raw
    processed_bytes_out[thread_id] = thread_processed

def save_bits_to_file(bits, filename):
    byte_array = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
        byte_array.append(byte)
    with open(filename, "wb") as f:
        f.write(byte_array)

def hash_bits(bits):
    byte_array = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
        byte_array.append(byte)

    hashes = bytearray()
    for i in range(0, len(byte_array), 32):
        hasher = sha3_256()
        hasher.update(byte_array[i:i+32])
        hashes.extend(hasher.digest())
    return hashes

def calculate_entropy(byte_array):
    counts = Counter(byte_array)
    return -sum(p * math.log2(p) for p in (count/len(byte_array) for count in counts.values()))

def plot_data_analysis(data, title, is_sha=False, sample_size=100_000):
    byte_array = list(data) if not isinstance(data[0], int) or data[0] > 1 else [
        sum((data[i+j] << j) for j in range(8) if i+j < len(data))
        for i in range(0, len(data), 8)
    ]
    entropy = calculate_entropy(byte_array)
    plt.figure(figsize=(10, 6))
    counts, _, _ = plt.hist(byte_array[:sample_size], bins=256, range=(0, 255), 
                           density=True, color='black', rwidth=1)
    plt.ylim(0, 0.006 if is_sha else max(counts) * 1.1)
    plt.title(f"{'Empiryczny rozkład po SHA3-256' if is_sha else title}\nEntropia: {entropy:.6f} bitów/bajt")
    plt.xlabel("Wartość (x)"), plt.ylabel("Częstość występowania (p)")
    plt.xlim(0, 255)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    plt.tight_layout()
    plt.show()
    return entropy

def hash_from_bytes(byte_array):
    hashes = bytearray()
    for i in range(0, len(byte_array), 32):
        hasher = sha3_256()
        hasher.update(bytearray(byte_array[i:i+32]))
        hashes.extend(hasher.digest())
    return hashes

def main():
    bytes_per_thread = BYTES_TO_GENERATE // THREADS
    raw_output = [None] * THREADS
    bits_output = [None] * THREADS
    
    threads = [threading.Thread(target=trng_network, 
               args=(i, bytes_per_thread, raw_output, bits_output)) for i in range(THREADS)]
    for t in threads: t.start()
    for t in threads: t.join()

    raw_bytes = sum((rb for rb in raw_output if rb), [])
    post_bytes = sum((pb for pb in bits_output if pb), [])
    
    for filename, data in [("source.bin", raw_bytes), ("post.bin", post_bytes)]:
        with open(filename, "wb") as f:
            f.write(bytearray(data))
            
    hashed_bytes = hash_from_bytes(post_bytes)
    with open("sha.bin", "wb") as f:
        f.write(hashed_bytes)

    print("\nAnaliza entropii:")
    print("-" * 40)
    print(f"Entropia surowych danych: {plot_data_analysis(raw_bytes, 'Surowe dane TRNG'):.6f} bitów/bajt")
    print(f"Entropia po post-processingu: {plot_data_analysis(post_bytes, 'Dane po post-processingu'):.6f} bitów/bajt")
    print(f"Entropia po SHA3-256: {plot_data_analysis(list(hashed_bytes), 'Dane po SHA3-256', is_sha=True):.6f} bitów/bajt")
    print("-" * 40)

if __name__ == "__main__":
    main()
