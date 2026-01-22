if __name__ == "__main__":
	import sys
	from paraseq_filt import   count_records

	if len(sys.argv) == 1:
		print("Usage: paraseq_filt.py <in.fq.gz>")
		sys.exit(0)
	if len(sys.argv) == 2:
		threads=1
	if len(sys.argv) == 3:
		threads= sys.argv[2]
		
	n, slen, qlen = 0, 0, 0
	# for record in parse_records(sys.argv[1]):
	# 	n += 1
	# 	slen += len(record.seq)
	# 	qlen += len(record.qual) if record.qual else 0
	n, slen = count_records(input_file = sys.argv[1], num_threads = int(threads))
	print('{}\t{}\t{}'.format(n, slen, slen))