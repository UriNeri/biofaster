use anyhow::{Context, Result};
use clap::Parser;
use paraseq::prelude::*;
use std::collections::HashSet;
use std::fs::File;
use std::io::{BufRead, BufReader, BufWriter, Write};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

#[derive(Parser, Debug)]
#[command(name = "paraseq_filt")]
#[command(about = "Fast parallel FASTA/FASTQ filtering tool", long_about = None)]
struct Args {
    /// Input FASTA/FASTQ file (supports .gz via paraseq/niffler)
    #[arg(short, long)]
    input: PathBuf,

    /// Output FASTA/FASTQ file
    #[arg(short, long)]
    output: Option<PathBuf>,

    /// Headers to filter (comma-separated IDs or path to file with one ID per line)
    #[arg(short = 'H', long)]
    headers: Option<String>,

    /// Invert match - keep records NOT in the header list
    #[arg(short = 'v', long)]
    invert: bool,

    /// Number of threads (default: number of CPUs)
    #[arg(short, long)]
    threads: Option<usize>,

    /// Count mode - just count reads and bases without filtering
    #[arg(short, long)]
    count: bool,
}

#[derive(Clone)]
struct FastaFilter {
    headers: Arc<HashSet<String>>,
    writer: Arc<Mutex<BufWriter<Box<dyn Write + Send>>>>,
    invert: bool,
    processed: Arc<Mutex<u64>>,
    written: Arc<Mutex<u64>>,
}

impl<R: Record> ParallelProcessor<R> for FastaFilter {
    fn process_record(&mut self, record: R) -> Result<(), paraseq::ProcessError> {
        let id = record.id_str().to_string();
        let seq_bytes = record.seq();
        let seq = std::str::from_utf8(&seq_bytes)
            .map_err(|e| paraseq::ProcessError::Process(Box::new(e)))?;

        // Update processed count
        {
            let mut count = self.processed.lock().unwrap();
            *count += 1;
            if *count % 100_000 == 0 {
                eprintln!("Processed {} records", *count);
            }
        }

        let should_write = if self.invert {
            !self.headers.contains(&id)
        } else {
            self.headers.contains(&id)
        };

        if should_write {
            let mut writer = self.writer.lock().unwrap();
            writeln!(writer, ">{}\n{}", id, seq)
                .map_err(|e| paraseq::ProcessError::IoError(e))?;
            
            let mut count = self.written.lock().unwrap();
            *count += 1;
        }

        Ok(())
    }
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Configure threads
    let num_threads = args.threads.unwrap_or_else(num_cpus::get);
    eprintln!("Using {} threads", num_threads);

    // Count mode - just count reads and bases
    if args.count {
        return count_mode(&args.input, num_threads);
    }

    // Filter mode - require headers and output
    let headers_input = args.headers
        .as_ref()
        .ok_or_else(|| anyhow::anyhow!("--headers is required for filtering mode"))?;
    
    let output_path = args.output
        .as_ref()
        .ok_or_else(|| anyhow::anyhow!("--output is required for filtering mode"))?;

    // Load headers into HashSet for O(1) lookup
    let headers = load_headers(headers_input)?;
    eprintln!("Loaded {} headers", headers.len());

    // Open output file or stdout
    let output_file: Box<dyn Write + Send> = if output_path.to_str() == Some("-") || output_path.to_str() == Some("/dev/stdout") {
        Box::new(std::io::stdout())
    } else {
        Box::new(File::create(output_path)
            .with_context(|| format!("Failed to create output file: {:?}", output_path))?)
    };
    let writer = BufWriter::new(output_file);

    // Create processor
    let mut processor = FastaFilter {
        headers: Arc::new(headers),
        writer: Arc::new(Mutex::new(writer)),
        invert: args.invert,
        processed: Arc::new(Mutex::new(0)),
        written: Arc::new(Mutex::new(0)),
    };

    // Process FASTA file
    let reader = paraseq::fastx::Reader::from_path(&args.input)
        .map_err(|e| anyhow::anyhow!("Failed to open input file: {}", e))?;
    
    reader
        .process_parallel(&mut processor, num_threads)
        .map_err(|e| anyhow::anyhow!("Failed to process file: {:?}", e))?;

    let total_processed = *processor.processed.lock().unwrap();
    let total_written = *processor.written.lock().unwrap();

    eprintln!(
        "Processed {} records, written {} records",
        total_processed, total_written
    );

    Ok(())
}

#[derive(Clone)]
struct FastaCounter {
    n_seqs: Arc<Mutex<u64>>,
    n_bases: Arc<Mutex<u64>>,
}

impl<R: Record> ParallelProcessor<R> for FastaCounter {
    fn process_record(&mut self, record: R) -> Result<(), paraseq::ProcessError> {
        let seq_bytes = record.seq();
        let seq_len = seq_bytes.len() as u64;

        {
            let mut n_seqs = self.n_seqs.lock().unwrap();
            *n_seqs += 1;
        }

        {
            let mut n_bases = self.n_bases.lock().unwrap();
            *n_bases += seq_len;
        }

        Ok(())
    }
}

fn count_mode(input_path: &PathBuf, num_threads: usize) -> Result<()> {
    let mut counter = FastaCounter {
        n_seqs: Arc::new(Mutex::new(0)),
        n_bases: Arc::new(Mutex::new(0)),
    };

    let reader = paraseq::fastx::Reader::from_path(input_path)
        .map_err(|e| anyhow::anyhow!("Failed to open input file: {}", e))?;
    
    reader
        .process_parallel(&mut counter, num_threads)
        .map_err(|e| anyhow::anyhow!("Failed to process file: {:?}", e))?;

    let n_seqs = *counter.n_seqs.lock().unwrap();
    let n_bases = *counter.n_bases.lock().unwrap();

    println!("{}\t{}", n_seqs, n_bases);

    Ok(())
}

fn load_headers(headers_input: &str) -> Result<HashSet<String>> {
    let mut headers = HashSet::new();

    // Check if it's a file path
    let path = std::path::Path::new(headers_input);
    if path.exists() {
        // Read from file
        let file = File::open(path)
            .with_context(|| format!("Failed to open headers file: {}", headers_input))?;
        let reader = BufReader::new(file);

        for line in reader.lines() {
            let line = line?;
            let header = line.trim();
            if !header.is_empty() {
                headers.insert(header.to_string());
            }
        }
    } else {
        // Treat as comma-separated list
        for header in headers_input.split(',') {
            let header = header.trim();
            if !header.is_empty() {
                headers.insert(header.to_string());
            }
        }
    }

    Ok(headers)
}
