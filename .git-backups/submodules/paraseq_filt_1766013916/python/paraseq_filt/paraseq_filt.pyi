"""
Type stubs for paraseq_filt

Fast parallel FASTA/FASTQ filtering using Rust and paraseq.
"""

from typing import List, Tuple

__version__: str

def filter_fasta_by_headers(
    input_file: str,
    output_file: str,
    headers: List[str],
    invert: bool = False,
    num_threads: int | None = None,
) -> Tuple[int, int]:
    """
    Filter a FASTA/FASTQ file by sequence IDs with parallel processing.
    
    Args:
        input_file: Path to input FASTA/FASTQ file (supports .gz)
        output_file: Path to output FASTA/FASTQ file
        headers: List of sequence IDs to filter
        invert: If True, keep sequences NOT in the headers list. Default: False
        num_threads: Number of threads to use. Default: number of CPUs
    
    Returns:
        Tuple of (records_processed, records_written)
    
    Raises:
        RuntimeError: If file operations fail or input is invalid
    
    Example:
        >>> import paraseq_filt
        >>> processed, written = paraseq_filt.filter_fasta_by_headers(
        ...     "input.fasta",
        ...     "output.fasta",
        ...     ["seq1", "seq2", "seq3"],
        ...     num_threads=4
        ... )
        >>> print(f"Processed {processed}, wrote {written}")
    """
    ...

def load_headers_from_file(file_path: str) -> List[str]:
    """
    Load sequence IDs from a file (one per line).
    
    Args:
        file_path: Path to file containing sequence IDs (one per line)
    
    Returns:
        List of sequence IDs
    
    Raises:
        RuntimeError: If file cannot be read
    
    Example:
        >>> import paraseq_filt
        >>> headers = paraseq_filt.load_headers_from_file("headers.txt")
        >>> print(f"Loaded {len(headers)} headers")
    """
    ...

def count_records(
    input_file: str,
    num_threads: int | None = None,
) -> Tuple[int, int]:
    """
    Count reads and bases in a FASTA/FASTQ file.
    
    Args:
        input_file: Path to input FASTA/FASTQ file (supports .gz)
        num_threads: Number of threads to use. Default: number of CPUs
    
    Returns:
        Tuple of (num_reads, num_bases)
    
    Raises:
        RuntimeError: If file operations fail
    
    Example:
        >>> import paraseq_filt
        >>> num_reads, num_bases = paraseq_filt.count_records("input.fasta.gz")
        >>> print(f"{num_reads}\\t{num_bases}")
    """
    ...

def parse_records(input_file: str) -> List[Tuple[str, str, str | None]]:
    """
    Parse FASTA/FASTQ records and return (id, sequence, quality) tuples.
    
    Args:
        input_file: Path to input FASTA/FASTQ file (supports .gz)
    
    Returns:
        List of (id, sequence, quality) tuples. Quality is None for FASTA files.
    
    Raises:
        RuntimeError: If file operations fail
    
    Example:
        >>> import paraseq_filt
        >>> # FASTA file
        >>> for seq_id, sequence, qual in paraseq_filt.parse_records("input.fasta"):
        ...     print(f">{seq_id}")
        ...     print(sequence)
        >>> 
        >>> # FASTQ file
        >>> for seq_id, sequence, qual in paraseq_filt.parse_records("input.fastq"):
        ...     if qual:
        ...         print(f"Quality: {qual}")
    """
    ...
