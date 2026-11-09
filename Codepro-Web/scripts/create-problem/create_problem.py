import os, sys

def create(code):
    print(f"Creating polygon scaffold for problem: {code}")

if __name__ == '__main__':
    if len(sys.argv) > 1: create(sys.argv[1])
