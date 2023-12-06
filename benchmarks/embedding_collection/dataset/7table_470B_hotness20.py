import os
import numpy as np
import struct
import sys

part_id = sys.argv[1]
output_dir = sys.argv[2]

alpha = 1.1
output_filename = os.path.join(
    output_dir, "7table_470B_hotness20_synthetic_alpha{}.bin.part{}".format(alpha, part_id)
)

dataset_info = [
    (1, 80, 10000000),
    (1, 20, 400000000),
    (1, 20, 1000000000),
    (1, 40, 5000000000),
    (1, 1, 1000000000),
    (1, 1, 10000000),
    (1, 1, 10000000),
]
num_dense_features = 13
num_label = 1

n = 65536

num_cate_features = sum([num_table * hotness for (num_table, hotness, _) in dataset_info])
max_vocabulary_size = sum([v for _, _, v in dataset_info])
item_num_per_sample = 1 + num_dense_features + num_cate_features
sample_format = r"1I" + str(num_dense_features) + "f" + str(num_cate_features) + "Q"
sample_size_in_bytes = 1 * 4 + num_dense_features * 4 + num_cate_features * 8

print("num_dense_features", num_dense_features)
print("num_cate_features", num_cate_features)
print("item_num_per_sample", item_num_per_sample)
print("sample_format", sample_format)


def Zipf(a: np.float64, min: np.uint64, max: np.uint64, size=None):
    """
    Generate Zipf-like random variables,
    but in inclusive [min...max] interval
    """
    v = np.arange(min + 1, max + 1)  # values to sample
    p = 1.0 / np.power(v, a)  # probabilities
    p /= np.sum(p)  # normalized
    k = np.arange(min, max)
    np.random.shuffle(k)

    return np.random.choice(k, size=size, replace=True, p=p)


random_cate_list = []
table_id = 0
for num_table, hotness, vocabulary_size in dataset_info:
    for t in range(num_table):
        s = Zipf(alpha, 0, vocabulary_size, n * hotness)
        s = s.reshape(n, hotness)
        random_cate_list.append(s)
        print("table_id", table_id, "unique ratio:", np.unique(s).size / s.size)
        table_id += 1
random_cate = np.concatenate(random_cate_list, axis=1).astype(np.int64)

random_label = np.random.randint(2, size=(n, 1)).astype(np.int32)
random_dense = np.random.uniform(size=(n, num_dense_features)).astype(np.float32)

with open(output_filename, "wb") as file:
    for i in range(n):
        label = random_label[i].tolist()
        dense = random_dense[i].tolist()
        cate = random_cate[i].tolist()
        data = label + dense + cate
        data_buffer = struct.pack(sample_format, *data)
        file.write(data_buffer)
