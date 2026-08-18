import sys

input_path_1, input_path_2, output_path = sys.argv[1], sys.argv[2], sys.argv[3]
with open(input_path_1) as f:
    numbers_1 = [int(line) for line in f]
with open(input_path_2) as f:
    numbers_2 = [int(line) for line in f]
with open(output_path, "w") as f:
    for a, b in zip(numbers_1, numbers_2):
        f.write(f"{a + b}\n")
