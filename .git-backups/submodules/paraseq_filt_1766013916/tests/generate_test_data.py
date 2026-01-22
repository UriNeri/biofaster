#!/usr/bin/env python3
"""Generate test FASTA/FASTQ files in various compression formats"""

import gzip
import subprocess
from pathlib import Path


def generate_fasta(output_path: Path, num_seqs: int = 5, seq_length: int = 80):
    """Generate a test FASTA file"""
    bases = "ACGT"
    with open(output_path, 'w') as f:
        for i in range(1, num_seqs + 1):
            f.write(f">seq{i} test sequence {i}\n")
            # Generate sequence with pattern based on sequence number
            seq = ''.join([bases[(i + j) % 4] for j in range(seq_length)])
            f.write(seq + "\n")
    print(f"Generated: {output_path}")


def generate_fastq(output_path: Path, num_seqs: int = 5, seq_length: int = 80):
    """Generate a test FASTQ file"""
    bases = "ACGT"
    with open(output_path, 'w') as f:
        for i in range(1, num_seqs + 1):
            f.write(f"@seq{i} test sequence {i}\n")
            # Generate sequence with pattern based on sequence number
            seq = ''.join([bases[(i + j) % 4] for j in range(seq_length)])
            f.write(seq + "\n")
            f.write("+\n")
            # Generate quality scores (Phred+33 format)
            # Use varying qualities: good (I=40), medium (9=24), low (!=0)
            qual_scores = ['I', '9', '!']
            qual = ''.join([qual_scores[j % 3] for j in range(seq_length)])
            f.write(qual + "\n")
    print(f"Generated: {output_path}")


def compress_gzip(input_path: Path):
    """Compress file with gzip"""
    output_path = input_path.with_suffix(input_path.suffix + '.gz')
    with open(input_path, 'rb') as f_in:
        with gzip.open(output_path, 'wb', compresslevel=6) as f_out:
            f_out.writelines(f_in)
    print(f"Compressed: {output_path}")
    return output_path


def compress_bgzip(input_path: Path):
    """Compress file with bgzip (if available)"""
    output_path = input_path.with_suffix(input_path.suffix + '.bgz')
    try:
        subprocess.run(
            ['bgzip', '-c', str(input_path)],
            stdout=open(output_path, 'wb'),
            check=True,
            stderr=subprocess.DEVNULL
        )
        print(f"Compressed (bgzip): {output_path}")
        return output_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"Skipped bgzip (not available): {output_path}")
        return None


def main():
    """Generate all test files"""
    # Create test data directory
    test_data_dir = Path(__file__).parent / "data"
    test_data_dir.mkdir(exist_ok=True)
    
    print("Generating test data files...")
    print("=" * 60)
    
    # Generate FASTA
    fasta_path = test_data_dir / "test.fasta"
    generate_fasta(fasta_path, num_seqs=5, seq_length=80)
    compress_gzip(fasta_path)
    compress_bgzip(fasta_path)
    
    print()
    
    # Generate FASTQ
    fastq_path = test_data_dir / "test.fastq"
    generate_fastq(fastq_path, num_seqs=5, seq_length=80)
    compress_gzip(fastq_path)
    compress_bgzip(fastq_path)
    
    print()
    
    # Generate smaller files for quick tests
    small_fasta = test_data_dir / "small.fasta"
    generate_fasta(small_fasta, num_seqs=3, seq_length=40)
    compress_gzip(small_fasta)
    
    small_fastq = test_data_dir / "small.fastq"
    generate_fastq(small_fastq, num_seqs=3, seq_length=40)
    compress_gzip(small_fastq)
    
    print()
    print("=" * 60)
    print("Test data generation complete!")
    print(f"Files created in: {test_data_dir}")
    print()
    print("Generated files:")
    for f in sorted(test_data_dir.glob("*")):
        size = f.stat().st_size
        print(f"  {f.name:20s} ({size:>6d} bytes)")


if __name__ == "__main__":
    main()
