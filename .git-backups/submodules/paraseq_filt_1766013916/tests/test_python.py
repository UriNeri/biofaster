#!/usr/bin/env python3
"""
Test script for paraseq_filt Python bindings
"""

import tempfile
import os
import gzip
from pathlib import Path

def create_test_fasta(path):
    """Create a test FASTA file"""
    with open(path, 'w') as f:
        f.write(">seq1\n")
        f.write("ATCGATCGATCG\n")
        f.write(">seq2\n")
        f.write("GCTAGCTAGCTA\n")
        f.write(">seq3\n")
        f.write("TTTTAAAACCCC\n")
        f.write(">seq4\n")
        f.write("GGGGCCCCAAAA\n")
        f.write(">seq5\n")
        f.write("NNNNNNNNNNNN\n")

def read_fasta_ids(path):
    """Read FASTA IDs from a file"""
    ids = []
    with open(path, 'r') as f:
        for line in f:
            if line.startswith('>'):
                ids.append(line[1:].strip())
    return ids

def main():
    import paraseq_filt
    
    print(f"paraseq_filt version: {paraseq_filt.__version__}")
    print("=" * 60)
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Test files
        input_file = tmpdir / "test.fasta"
        output_file = tmpdir / "output.fasta"
        headers_file = tmpdir / "headers.txt"
        
        # Create test data
        create_test_fasta(input_file)
        
        # Test 1: Filter with list of headers
        print("\nTest 1: Filter with list of headers")
        headers = ["seq1", "seq3", "seq5"]
        processed, written = paraseq_filt.filter_fasta_by_headers(
            input_file,
            output_file,
            headers,
            num_threads=4
        )
        result_ids = read_fasta_ids(output_file)
        print(f"  Processed: {processed}, Written: {written}")
        print(f"  Expected IDs: {headers}")
        print(f"  Result IDs: {result_ids}")
        assert written == 3, f"Expected 3 records, got {written}"
        assert set(result_ids) == set(headers), "IDs don't match"
        print("  ✓ PASSED")
        
        # Test 2: Filter with headers from file
        print("\nTest 2: Filter with headers from file")
        with open(headers_file, 'w') as f:
            f.write("seq2\nseq4\n")
        
        output_file2 = tmpdir / "output2.fasta"
        processed, written = paraseq_filt.filter_fasta_by_headers(
            input_file,
            output_file2,
            headers_file
        )
        result_ids = read_fasta_ids(output_file2)
        print(f"  Processed: {processed}, Written: {written}")
        print(f"  Result IDs: {result_ids}")
        assert written == 2, f"Expected 2 records, got {written}"
        assert set(result_ids) == {"seq2", "seq4"}, "IDs don't match"
        print("  ✓ PASSED")
        
        # Test 3: Invert filter
        print("\nTest 3: Invert filter (exclude headers)")
        output_file3 = tmpdir / "output3.fasta"
        processed, written = paraseq_filt.filter_fasta_by_headers(
            input_file,
            output_file3,
            ["seq1", "seq3"],
            invert=True
        )
        result_ids = read_fasta_ids(output_file3)
        print(f"  Processed: {processed}, Written: {written}")
        print(f"  Result IDs: {result_ids}")
        assert written == 3, f"Expected 3 records, got {written}"
        assert set(result_ids) == {"seq2", "seq4", "seq5"}, "IDs don't match"
        print("  ✓ PASSED")
        
        # Test 4: Load headers from file
        print("\nTest 4: Load headers from file")
        loaded_headers = paraseq_filt.load_headers_from_file(headers_file)
        print(f"  Loaded headers: {loaded_headers}")
        assert loaded_headers == ["seq2", "seq4"], "Headers don't match"
        print("  ✓ PASSED")
        
        # Test 5: Empty result
        print("\nTest 5: Empty result (no matching headers)")
        output_file5 = tmpdir / "output5.fasta"
        processed, written = paraseq_filt.filter_fasta_by_headers(
            input_file,
            output_file5,
            ["nonexistent1", "nonexistent2"]
        )
        print(f"  Processed: {processed}, Written: {written}")
        assert written == 0, f"Expected 0 records, got {written}"
        print("  ✓ PASSED")
        
        # Test 6: Count records
        print("\nTest 6: Count records")
        num_reads, num_bases = paraseq_filt.count_records(input_file)
        print(f"  Reads: {num_reads}, Bases: {num_bases}")
        assert num_reads == 5, f"Expected 5 reads, got {num_reads}"
        assert num_bases == 60, f"Expected 60 bases, got {num_bases}"  # 5 sequences * 12 bases each
        print("  ✓ PASSED")
        
        # Test 7: Count with threads
        print("\nTest 7: Count records with specific thread count")
        num_reads, num_bases = paraseq_filt.count_records(input_file, num_threads=2)
        print(f"  Reads: {num_reads}, Bases: {num_bases}")
        assert num_reads == 5, f"Expected 5 reads, got {num_reads}"
        print("  ✓ PASSED")
        
        # Test 8: Parse FASTA records (no quality)
        print("\nTest 8: Parse FASTA records")
        records = paraseq_filt.parse_records(input_file)
        print(f"  Parsed {len(records)} records")
        assert len(records) == 5, f"Expected 5 records, got {len(records)}"
        seq_id, seq, qual = records[0]
        assert seq_id == "seq1", f"Expected 'seq1', got '{seq_id}'"
        assert seq == "ATCGATCGATCG", f"Expected 'ATCGATCGATCG', got '{seq}'"
        assert qual is None, f"Expected None quality for FASTA, got {qual}"
        print("  ✓ PASSED")
        
        # Test 9: Parse FASTQ records (with quality)
        print("\nTest 9: Parse FASTQ records with quality")
        fastq_file = tmpdir / "test.fastq"
        with open(fastq_file, 'w') as f:
            f.write("@read1\n")
            f.write("ACGTACGT\n")
            f.write("+\n")
            f.write("IIIIIIII\n")
            f.write("@read2\n")
            f.write("TGCATGCA\n")
            f.write("+\n")
            f.write("99999999\n")
        
        records = paraseq_filt.parse_records(fastq_file)
        print(f"  Parsed {len(records)} FASTQ records")
        assert len(records) == 2, f"Expected 2 records, got {len(records)}"
        seq_id, seq, qual = records[0]
        assert seq_id == "read1", f"Expected 'read1', got '{seq_id}'"
        assert seq == "ACGTACGT", f"Expected 'ACGTACGT', got '{seq}'"
        assert qual == "IIIIIIII", f"Expected 'IIIIIIII' quality, got '{qual}'"
        print("  ✓ PASSED")
        
        # Test 10: Parse gzipped file
        print("\nTest 10: Parse gzipped FASTA file")
        gz_file = tmpdir / "test.fasta.gz"
        with gzip.open(gz_file, 'wt') as f:
            f.write(">seq1\n")
            f.write("ACGT\n")
            f.write(">seq2\n")
            f.write("TGCA\n")
        
        records = paraseq_filt.parse_records(gz_file)
        print(f"  Parsed {len(records)} records from gzip")
        assert len(records) == 2, f"Expected 2 records, got {len(records)}"
        seq_id, seq, qual = records[0]
        assert qual is None, f"Expected None quality for FASTA, got {qual}"
        print("  ✓ PASSED")
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")

if __name__ == "__main__":
    main()
