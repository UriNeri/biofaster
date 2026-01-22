#!/usr/bin/env python3
"""
Type checking test for paraseq_filt

Run with: mypy test_types.py
"""

import paraseq_filt
from pathlib import Path

def test_basic_types() -> None:
    """Test basic type checking"""
    
    # Valid calls
    result1: tuple[int, int] = paraseq_filt.filter_fasta_by_headers(
        "input.fasta",
        "output.fasta",
        ["seq1", "seq2"]
    )
    
    # With all parameters
    result2: tuple[int, int] = paraseq_filt.filter_fasta_by_headers(
        input_file="input.fasta",
        output_file="output.fasta",
        headers=["seq1", "seq2"],
        invert=True,
        num_threads=8
    )
    
    # With Path objects
    result3: tuple[int, int] = paraseq_filt.filter_fasta_by_headers(
        Path("input.fasta"),
        Path("output.fasta"),
        ["seq1", "seq2"]
    )
    
    # With headers from file
    result4: tuple[int, int] = paraseq_filt.filter_fasta_by_headers(
        "input.fasta",
        "output.fasta",
        "headers.txt"
    )
    
    # load_headers_from_file
    headers: list[str] = paraseq_filt.load_headers_from_file("headers.txt")
    headers2: list[str] = paraseq_filt.load_headers_from_file(Path("headers.txt"))
    
    # Unpack tuple
    processed, written = paraseq_filt.filter_fasta_by_headers(
        "input.fasta",
        "output.fasta",
        ["seq1"]
    )
    
    print(f"Processed {processed}, wrote {written}")
    print(f"Loaded {len(headers)} headers")


def test_invalid_types() -> None:
    """These should fail type checking"""
    
    # Invalid: wrong return type annotation
    # result: str = paraseq_filt.filter_fasta_by_headers(  # type: ignore
    #     "input.fasta",
    #     "output.fasta",
    #     ["seq1"]
    # )
    
    # Invalid: headers must be list[str] or str/Path
    # result = paraseq_filt.filter_fasta_by_headers(  # type: ignore
    #     "input.fasta",
    #     "output.fasta",
    #     123  # Wrong type!
    # )
    
    # Invalid: num_threads must be int or None
    # result = paraseq_filt.filter_fasta_by_headers(  # type: ignore
    #     "input.fasta",
    #     "output.fasta",
    #     ["seq1"],
    #     num_threads="4"  # Should be int!
    # )
    
    pass


if __name__ == "__main__":
    print("Type checking test file")
    print("Run: mypy test_types.py")
    print("")
    print("Or check in your IDE - should show proper autocomplete and types!")
