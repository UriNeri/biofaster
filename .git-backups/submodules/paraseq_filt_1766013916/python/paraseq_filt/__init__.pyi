"""
Type stubs for paraseq_filt package

Fast parallel FASTA/FASTQ filtering using Rust and paraseq.
"""

from typing import List, Tuple, Union, Optional
from pathlib import Path

__version__: str

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
    
    Raises:
        RuntimeError: If file operations fail or input is invalid
        FileNotFoundError: If headers file path does not exist
    
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
    ...

def load_headers_from_file(file_path: Union[str, Path]) -> List[str]:
    """
    Load sequence IDs from a file (one per line).
    
    Args:
        file_path: Path to file containing sequence IDs (one per line)
    
    Returns:
        List of sequence IDs
    
    Raises:
        RuntimeError: If file cannot be read
    
    Example:
        >>> headers = load_headers_from_file("headers.txt")
        >>> print(f"Loaded {len(headers)} headers")
    """
    ...

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
        num_threads: Number of threads to use. Default: number of CPUs
    
    Returns:
        A tuple of (num_reads, num_bases)
    
    Raises:
        RuntimeError: If file operations fail
    
    Example:
        >>> num_reads, num_bases = count_records("input.fasta.gz")
        >>> print(f"{num_reads}\\t{num_bases}")
        
        >>> # Use specific thread count
        >>> num_reads, num_bases = count_records("input.fastq", num_threads=4)
    """
    ...

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
    
    Raises:
        RuntimeError: If file operations fail
    
    Example:
        >>> # FASTA file
        >>> for seq_id, sequence, qual in parse_records("input.fasta"):
        ...     print(f">{seq_id}")
        ...     print(sequence)
        
        >>> # FASTQ file
        >>> for seq_id, sequence, qual in parse_records("input.fastq"):
        ...     if qual:
        ...         print(f"Quality: {qual}")
        
        >>> # Get all records at once
        >>> records = parse_records("input.fastq.gz")
        >>> print(f"Loaded {len(records)} sequences")
    """
    ...
