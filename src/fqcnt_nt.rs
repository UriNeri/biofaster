// Fast FASTQ parser using needletail
// Based on biofast benchmark: https://github.com/lh3/biofast

//use needletail::{parse_fastx_file, Sequence}; // ignore unused_imports
use needletail::{parse_fastx_file}; // ignore unused_imports
use std::env;
use std::io::{self, Write};

fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: {} <fastq_file>", args[0]);
        std::process::exit(1);
    }

    let filename = &args[1];
    
    let mut n_seqs = 0u64;
    let mut n_bases = 0u64;
    
    let mut reader = parse_fastx_file(filename).unwrap_or_else(|e| {
        eprintln!("Error opening file '{}': {}", filename, e);
        std::process::exit(1);
    });
    
    while let Some(record) = reader.next() {
        let record = record.unwrap_or_else(|e| {
            eprintln!("Error parsing record: {}", e);
            std::process::exit(1);
        });
        
        n_seqs += 1;
        n_bases += record.num_bases() as u64;
    }
    
    println!("{}\t{}", n_seqs, n_bases);
    io::stdout().flush().unwrap();
}
