import threading
import random
import matplotlib.pyplot as plt
from collections import Counter
import math
from hashlib import sha3_256

NUM_BITS = 100_000_000
THREADS = 4
CHUNK_SIZE = NUM_BITS // THREADS

def logistic_map(x, r):
    return r * x * (1 - x)

def normalize(x):
    return (1000 * x) - int(1000 * x)

def generate_bit(x, r, gamma=2):
    for _ in range(gamma):
        x = logistic_map(x, r)
        x = normalize(x)
    raw_bit = int(x * 256) & 1
    x = (x + random.uniform(0, 1)) % 1
    processed_bit = int(x * 256) & 1
    return raw_bit, processed_bit, x

def thread_trng(raw_output, processed_output, index, bits_to_generate):
    x = random.uniform(0.1, 0.9)
    raw_bits = []
    processed_bits = []
    for _ in range(bits_to_generate):
        raw_bit, processed_bit, x = generate_bit(x, 3.99)
        raw_bits.append(raw_bit)
        processed_bits.append(processed_bit)
    raw_output[index] = raw_bits
    processed_output[index] = processed_bits

def save_bits_to_file(bit_array, filename):
    byte_array = bytearray()
    for i in range(0, len(bit_array), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bit_array):
                byte = (byte << 1) | bit_array[i + j]
        byte_array.append(byte)
    with open(filename, "wb") as f:
        f.write(byte_array)

def calculate_entropy(byte_array):
    counts = Counter(byte_array)
    entropy = 0.0
    for count in counts.values():
        p = count / len(byte_array)
        entropy -= p * math.log2(p)
    return entropy

def hash_bits(bit_array):
    byte_array = bytearray()
    for i in range(0, len(bit_array), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bit_array):
                byte = (byte << 1) | bit_array[i + j]
        byte_array.append(byte)
    
    hashes = bytearray()
    for i in range(0, len(byte_array), 32):
        hasher = sha3_256()
        hasher.update(byte_array[i:i+32])
        hashes.extend(hasher.digest())
    return hashes

def plot_data_analysis(data, title, is_sha=False, sample_size=100_000):
    if isinstance(data[0], int) and data[0] in (0, 1):
        byte_array = []
        for i in range(0, len(data), 8):
            byte = 0
            for j in range(8):
                if i + j < len(data):
                    byte = (byte << 1) | data[i + j]
            byte_array.append(byte)
    else:
        byte_array = list(data)

    entropy = calculate_entropy(byte_array)
    sample = byte_array[:sample_size]
    
    plt.figure(figsize=(10, 6))
    counts, _, _ = plt.hist(sample, bins=256, range=(0, 255), 
                           density=True, color='black', rwidth=1)
    
    plt.ylim(0, 0.006 if is_sha else max(counts) * 1.1)
    plt.title(f"Empiryczny rozkład zmiennych losowych po SHA3-256\nEntropia Shannona: {entropy:.6f} bitów/bajt" if is_sha 
              else f"{title}\nEntropia Shannona: {entropy:.6f} bitów/bajt")
    plt.xlabel("Wartość (x)")
    plt.ylabel("Częstość występowania (p)")
    plt.xlim(0, 255)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    plt.tight_layout()
    plt.show()
    return entropy

def main():
    threads = []
    raw_output = [None] * THREADS
    processed_output = [None] * THREADS

    for i in range(THREADS):
        t = threading.Thread(target=thread_trng, args=(raw_output, processed_output, i, CHUNK_SIZE))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    raw_bits = []
    processed_bits = []
    for chunk in raw_output:
        raw_bits.extend(chunk)
    for chunk in processed_output:
        processed_bits.extend(chunk)

    save_bits_to_file(raw_bits[:NUM_BITS], "source.bin")
    save_bits_to_file(processed_bits[:NUM_BITS], "post.bin")
    
    hashed_data = hash_bits(processed_bits[:NUM_BITS])
    with open("sha.bin", "wb") as f:
        f.write(hashed_data)

    raw_bytes = []
    for i in range(0, len(raw_bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(raw_bits):
                byte = (byte << 1) | raw_bits[i + j]
        raw_bytes.append(byte)
    
    print("\nWyniki analizy entropii:")
    print("-" * 40)
    
    entropy_raw = plot_data_analysis(raw_bytes, "Histogram surowych danych")
    print(f"Entropia surowych danych: {entropy_raw:.6f} bitów/bajt")
    
    entropy_processed = plot_data_analysis(processed_bits[:NUM_BITS], "Histogram danych po post-processingu")
    print(f"Entropia po post-processingu: {entropy_processed:.6f} bitów/bajt")
    
    entropy_hashed = plot_data_analysis(list(hashed_data), "Histogram danych po SHA3-256", is_sha=True)
    print(f"Entropia po SHA3-256: {entropy_hashed:.6f} bitów/bajt")
    print("-" * 40)

if __name__ == "__main__":
    main()