"""
Fast parallel FASTA/FASTQ filtering using Rust and paraseq.

This module provides Python bindings to a high-performance Rust implementation
for filtering FASTA/FASTQ files based on sequence IDs.
"""

from typing import List, Optional, Tuple, Union
from pathlib import Path

# Import the Rust extension module
from .paraseq_filt import filter_fasta_by_headers as _filter_fasta_by_headers
from .paraseq_filt import load_headers_from_file as _load_headers_from_file
from .paraseq_filt import count_records as _count_records
from .paraseq_filt import parse_records as _parse_records

__version__ = "0.1.0"
__all__ = ["filter_fasta_by_headers", "load_headers_from_file", "count_records", "parse_records"]


def filter_fasta_by_headers(
    input_file: Union[str, Path],
    output_file: Union[str, Path],
    headers: Union[List[str], str, Path],
    invert: bool = False,
    num_threads: Optional[int] = None,
) -> Tuple[int, int]:
    """
    Filter a FASTA/FASTQ file by sequence IDs with parallel processing.
    
    This function provides a high-performance, parallel implementation for filtering
    FASTA/FASTQ files. It can handle both regular and gzipped input files automatically.
    
    Args:
        input_file: Path to input FASTA/FASTQ file (supports .gz)
        output_file: Path to output FASTA/FASTQ file
        headers: Either a list of sequence IDs to filter, or a path to a file
                containing sequence IDs (one per line)
        invert: If True, keep sequences NOT in the headers list. Default: False
        num_threads: Number of threads to use. Default: number of CPUs
    
    Returns:
        A tuple of (records_processed, records_written)
    
    Example:
        >>> # Filter specific sequences
        >>> processed, written = filter_fasta_by_headers(
        ...     "input.fasta",
        ...     "output.fasta",
        ...     ["seq1", "seq2", "seq3"]
        ... )
        >>> print(f"Processed {processed}, wrote {written}")
        
        >>> # Filter using a file of headers
        >>> processed, written = filter_fasta_by_headers(
        ...     "input.fasta.gz",
        ...     "output.fasta",
        ...     "headers_to_keep.txt",
        ...     num_threads=8
        ... )
        
        >>> # Invert to exclude sequences
        >>> processed, written = filter_fasta_by_headers(
        ...     "input.fasta",
        ...     "filtered.fasta",
        ...     ["seq_to_exclude1", "seq_to_exclude2"],
        ...     invert=True
        ... )
    """
    # Convert paths to strings
    input_file = str(input_file)
    output_file = str(output_file)
    
    # Handle headers - either a list or a file path
    if isinstance(headers, (str, Path)):
        headers_path = Path(headers)
        if headers_path.exists():
            headers = _load_headers_from_file(str(headers))
        else:
            raise FileNotFoundError(f"Headers file not found: {headers}")
    
    # Call the Rust implementation
    return _filter_fasta_by_headers(
        input_file,
        output_file,
        headers,
        invert=invert,
        num_threads=num_threads,
    )


def load_headers_from_file(file_path: Union[str, Path]) -> List[str]:
    """
    Load sequence IDs from a file (one per line).
    
    Args:
        file_path: Path to file containing sequence IDs (one per line)
    
    Returns:
        List of sequence IDs
    
    Example:
        >>> headers = load_headers_from_file("headers.txt")
        >>> print(f"Loaded {len(headers)} headers")
    """
    return _load_headers_from_file(str(file_path))


def count_records(
    input_file: Union[str, Path],
    num_threads: Optional[int] = None,
) -> Tuple[int, int]:
    """
    Count reads and bases in a FASTA/FASTQ file.
    
    This function provides a high-performance parallel implementation for counting
    sequences and bases. It can handle both regular and gzipped input files automatically.
    
    Args:
        input_file: Path to input FASTA/FASTQ file (supports .gz)
        num_threads: Number of threads to use (default: number of CPUs)
    
    Returns:
        Tuple of (num_reads, num_bases)
    
    Example:
        >>> num_reads, num_bases = count_records("input.fasta.gz")
        >>> print(f"{num_reads}\\t{num_bases}")
        >>> 
        >>> # Use specific thread count
        >>> num_reads, num_bases = count_records("input.fastq", num_threads=4)
    """
    return _count_records(str(input_file), num_threads=num_threads)


def parse_records(input_file: Union[str, Path]) -> List[Tuple[str, str, Optional[str]]]:
    """
    Parse FASTA/FASTQ records and return (id, sequence, quality) tuples.
    
    This function reads all records from a FASTA/FASTQ file and returns them as
    a list of (id, sequence, quality) tuples. For FASTA files, quality will be None.
    For FASTQ files, quality contains the quality scores. It can handle both regular
    and gzipped input files.
    
    Args:
        input_file: Path to input FASTA/FASTQ file (supports .gz)
    
    Returns:
        List of (id, sequence, quality) tuples. Quality is None for FASTA files.
    
    Example:
        >>> # FASTA file
        >>> for seq_id, sequence, qual in parse_records("input.fasta"):
        ...     print(f">{seq_id}")
        ...     print(sequence)
        >>> 
        >>> # FASTQ file
        >>> for seq_id, sequence, qual in parse_records("input.fastq"):
        ...     print(f"@{seq_id}")
        ...     print(sequence)
        ...     if qual:
        ...         print("+")
        ...         print(qual)
        >>> 
        >>> # Get all records at once
        >>> records = parse_records("input.fastq.gz")
        >>> print(f"Loaded {len(records)} sequences")
    """
    return _parse_records(str(input_file))
