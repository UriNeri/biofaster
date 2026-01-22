#!/usr/bin/env python

import sys
from contextlib import contextmanager
from enum import Enum, auto
from pathlib import Path

from Bio import SeqIO

if sys.version_info >= (3, 14):
    from compression import bz2, gzip, lzma, zstd
else:
    import bz2
    import gzip
    import lzma


class Compression(Enum):
    bzip2 = auto()
    gzip = auto()
    xz = auto()
    zstd = auto()
    uncompressed = auto()


def is_compressed(filepath: Path) -> Compression:
    with open(filepath, "rb") as fin:
        signature = fin.peek(8)[:8]
        if tuple(signature[:2]) == (0x1F, 0x8B):
            return Compression.gzip
        elif tuple(signature[:3]) == (0x42, 0x5A, 0x68):
            return Compression.bzip2
        elif tuple(signature[:7]) == (
            0xFD,
            0x37,
            0x7A,
            0x58,
            0x5A,
            0x00,
            0x00,
        ):
            return Compression.xz
        elif tuple(signature[:4]) == (0x28, 0xB5, 0x2F, 0xFD):
            return Compression.zstd
        else:
            return Compression.uncompressed


@contextmanager
def open_file(filepath):
    filepath_compression = is_compressed(filepath)
    if filepath_compression is Compression.gzip:
        fin = gzip.open(filepath, "rt")
    elif filepath_compression is Compression.bzip2:
        fin = bz2.open(filepath, "rt")
    elif filepath_compression is Compression.xz:
        fin = lzma.open(filepath, "rt")
    elif filepath_compression is Compression.zstd and sys.version_info >= (
        3,
        14,
    ):
        fin = zstd.open(filepath, "rt")
    else:
        fin = open(filepath, "r")
    try:
        yield fin
    finally:
        fin.close()

if len(sys.argv) == 1:
    print("Usage: biopython.py <input>")
    sys.exit(0)

fastx_file = sys.argv[1]

with open_file(fastx_file) as fi:
    first_char = fi.read(1)
    if first_char == ">":
        fmt = "fasta"
    elif first_char == "@":
        fmt = "fastq"
    else:
        raise ValueError("Unrecognized FASTX format")
    fi.seek(0)

    n, slen, qlen = 0, 0, 0
    for record in SeqIO.parse(fi, fmt):
        n += 1
        slen += len(record.seq)
        qlen += (
            len(record.letter_annotations["phred_quality"])
            if fmt == "fastq"
            else 0
        )

print("{}\t{}\t{}".format(n, slen, qlen))
