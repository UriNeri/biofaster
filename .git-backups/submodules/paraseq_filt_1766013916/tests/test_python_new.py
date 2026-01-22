#!/usr/bin/env python3
"""Test new Python bindings for count_records and parse_records"""

import paraseq_filt
import tempfile
import gzip
from pathlib import Path


def test_count_records():
    """Test counting reads and bases"""
    # Create test FASTA
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        test_file = f.name
        f.write(">seq1\n")
        f.write("ACGTACGT\n")
        f.write(">seq2\n")
        f.write("TGCATGCA\n")
        f.write(">seq3\n")
        f.write("GGGGGGGGGG\n")  # 10 bases
    
    try:
        n_seqs, n_bases = paraseq_filt.count_records(test_file)
        print(f"Count test: {n_seqs} seqs, {n_bases} bases")
        assert n_seqs == 3, f"Expected 3 seqs, got {n_seqs}"
        assert n_bases == 26, f"Expected 26 bases, got {n_bases}"
        print("✓ Count test passed")
    finally:
        Path(test_file).unlink()


def test_count_records_gzip():
    """Test counting gzipped file"""
    with tempfile.NamedTemporaryFile(suffix='.fasta.gz', delete=False) as f:
        test_file = f.name
    
    with gzip.open(test_file, 'wt') as f:
        f.write(">seq1\n")
        f.write("ACGT\n")
        f.write(">seq2\n")
        f.write("TGCA\n")
    
    try:
        n_seqs, n_bases = paraseq_filt.count_records(test_file, num_threads=2)
        print(f"Gzip count test: {n_seqs} seqs, {n_bases} bases")
        assert n_seqs == 2, f"Expected 2 seqs, got {n_seqs}"
        assert n_bases == 8, f"Expected 8 bases, got {n_bases}"
        print("✓ Gzip count test passed")
    finally:
        Path(test_file).unlink()


def test_parse_records():
    """Test parsing FASTA records"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        test_file = f.name
        f.write(">seq1\n")
        f.write("ACGT\n")
        f.write(">seq2\n")
        f.write("TGCA\n")
    
    try:
        records = paraseq_filt.parse_records(test_file)
        print(f"Parse test: {len(records)} records")
        
        assert len(records) == 2, f"Expected 2 records, got {len(records)}"
        
        seq_id, seq, qual = records[0]
        assert seq_id == "seq1", f"Expected 'seq1', got '{seq_id}'"
        assert seq == "ACGT", f"Expected 'ACGT', got '{seq}'"
        assert qual is None, f"Expected None quality for FASTA, got {qual}"
        
        seq_id, seq, qual = records[1]
        assert seq_id == "seq2", f"Expected 'seq2', got '{seq_id}'"
        assert seq == "TGCA", f"Expected 'TGCA', got '{seq}'"
        assert qual is None, f"Expected None quality for FASTA, got {qual}"
        
        print("✓ Parse test passed")
    finally:
        Path(test_file).unlink()


def test_parse_fastq():
    """Test parsing FASTQ format with quality scores"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fastq', delete=False) as f:
        test_file = f.name
        f.write("@read1\n")
        f.write("ACGTACGT\n")
        f.write("+\n")
        f.write("IIIIIIII\n")
        f.write("@read2\n")
        f.write("TGCATGCA\n")
        f.write("+\n")
        f.write("99999999\n")
    
    try:
        records = paraseq_filt.parse_records(test_file)
        print(f"FASTQ parse test: {len(records)} records")
        
        assert len(records) == 2, f"Expected 2 records, got {len(records)}"
        
        seq_id, seq, qual = records[0]
        assert seq_id == "read1", f"Expected 'read1', got '{seq_id}'"
        assert seq == "ACGTACGT", f"Expected 'ACGTACGT', got '{seq}'"
        assert qual == "IIIIIIII", f"Expected 'IIIIIIII' quality, got '{qual}'"
        
        seq_id, seq, qual = records[1]
        assert seq_id == "read2", f"Expected 'read2', got '{seq_id}'"
        assert seq == "TGCATGCA", f"Expected 'TGCATGCA', got '{seq}'"
        assert qual == "99999999", f"Expected '99999999' quality, got '{qual}'"
        
        print("✓ FASTQ parse test passed")
    finally:
        Path(test_file).unlink()


if __name__ == "__main__":
    test_count_records()
    test_count_records_gzip()
    test_parse_records()
    test_parse_fastq()
    print("\n✓ All new Python tests passed!")
