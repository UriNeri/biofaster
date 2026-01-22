if __name__ == "__main__":
	from polars_bio import  read_fastq
	import sys
	import polars as pl
	if len(sys.argv) == 1:
		print("Usage: polars_bio <in.fq.gz>")
		sys.exit(0)
	n, slen, qlen = 0, 0, 0
	out_df = read_fastq(sys.argv[1])
	n += out_df.height()
	slen += out_df.select(pl.col("sequence").str.length_nchar().sum())
	qlen += out_df.select(pl.col("quality").str.length_nchar().sum())
	print('{}\t{}\t{}'.format(n, slen, qlen))