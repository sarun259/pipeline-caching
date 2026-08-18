import sys

output_path = sys.argv[1]
with open(output_path, "w") as f:
    for n in range(20):
        f.write(f"{n}\n")
