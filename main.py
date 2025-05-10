import threading
import random
import struct
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
import math

# ==== Parametry TRNG ====
NUM_BITS = 13_000_000
OUTPUT_FILE = "trng_output.bin"
THREADS = 4
CHUNK_SIZE = NUM_BITS // THREADS
BITS_PER_BYTE = 8

# ==== Chaos (logistyczna mapa) ====
def logistic_map(x, r):
    return r * x * (1 - x)

def normalize(x):
    return (1000 * x) - int(1000 * x)

def generate_bit(x, r, gamma=2):
    for _ in range(gamma):
        x = logistic_map(x, r)
        x = normalize(x)
    # Zwiększenie losowości przez dodanie dodatkowego przekształcenia
    random_factor = random.uniform(0, 1)
    x = (x + random_factor) % 1
    return int(x * 256) & 1, x

# ==== Wątek TRNG ====
def thread_trng(output, index, bits_to_generate):
    x = random.uniform(0.1, 0.9)
    r = 3.99
    bits = []
    for _ in range(bits_to_generate):
        bit, x = generate_bit(x, r)
        bits.append(bit)
    output[index] = bits

# ==== Zapis bitów do pliku bin ====
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

# ==== Entropia Shannona ====
def calculate_entropy(byte_array):
    counts = Counter(byte_array)
    total = len(byte_array)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy

# ==== Histogram 8-bitowych liczb ====
def plot_histogram(byte_array, sample_size=100_000):
    sample = byte_array[:sample_size]
    sample = [byte & 0xFF for byte in sample]  # Ensure values are in the range 0–255
    plt.figure(figsize=(10, 5))
    plt.hist(sample, bins=256, range=(0, 255), color='steelblue', edgecolor='black')
    plt.title("Histogram 8-bitowych liczb losowych (pierwsze 100k bajtów)")
    plt.xlabel("Wartość bajtu (0–255)")
    plt.ylabel("Liczba wystąpień")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# ==== Główna funkcja ====
def main():
    print("Generowanie TRNG...")
    threads = []
    output = [None] * THREADS

    for i in range(THREADS):
        t = threading.Thread(target=thread_trng, args=(output, i, CHUNK_SIZE))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    all_bits = []
    for chunk in output:
        all_bits.extend(chunk)

    # Zapis do pliku
    save_bits_to_file(all_bits[:NUM_BITS], OUTPUT_FILE)
    print(f"Zapisano {NUM_BITS} bitów do pliku {OUTPUT_FILE}")

    # Konwersja do bajtów
    byte_array = []
    for i in range(0, len(all_bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(all_bits):
                byte = (byte << 1) | all_bits[i + j]
        byte_array.append(byte)

    # Oblicz entropię
    entropy = calculate_entropy(byte_array)
    print(f"Entropia Shannona: {entropy:.6f} bitów na bajt (max = 8.0)")

    # Wykres histogramu
    plot_histogram(byte_array)

if __name__ == "__main__":
    main()