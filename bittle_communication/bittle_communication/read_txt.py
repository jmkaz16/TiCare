import os

def read_from_file(file="order.txt"):
    if os.path.exists(file):
        with open(file, "r") as f:
            return f.read().strip()
    else:
        print("No existe")

print(read_from_file())
