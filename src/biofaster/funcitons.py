import json
import altair as alt
import polars as pl
from pathlib import Path

# Configure Altair
alt.data_transformers.disable_max_rows()
alt.renderers.enable('default')

def load_hyperfine_results(json_path):
    """Load hyperfine JSON results and return parsed data."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def find_latest_results_dir():
    """Find the most recent benchmark results directory."""
    results_dir = Path('benchmark_results')
    if not results_dir.exists():
        return None
    
    subdirs = [d for d in results_dir.iterdir() if d.is_dir()]
    if not subdirs:
        return None
    
    # Sort by name (which includes timestamp)
    latest = sorted(subdirs)[-1]
    return latest

def get_color_palette():
    """Get consistent color palette for parsers.
    
    Returns:
        List of color hex codes
    """
    return [
        '#2ecc71',  # Green
        '#3498db',  # Blue
        '#9b59b6',  # Purple
        '#e74c3c',  # Red
        '#f39c12',  # Orange
        '#1abc9c',  # Turquoise
        '#e67e22',  # Carrot
        '#95a5a6',  # Gray
        '#34495e',  # Dark blue-gray
        '#16a085',  # Teal
        '#8e44ad',  # Wisteria (purple)
        '#27ae60',  # Nephritis (green)
        '#d35400',  # Pumpkin (orange)
        '#c0392b',  # Pomegranate (red)
        '#2980b9',  # Belize Hole (blue)
        '#f1c40f',  # Sunflower (yellow)
    ]


def get_file_size_bytes(json_path):
    """Get the actual file size in bytes for a benchmark.
    
    Args:
        json_path: Path to the benchmark JSON file
        
    Returns:
        int: File size in bytes, or None if not found
    """
    try:
        data_dir = Path('test-data')
        json_path_str = str(json_path)
        json_path_obj = Path(json_path)
        
        # Check for really-cold benchmarks (generated files with known sizes)
        if 'really_cold_10mb' in json_path_str:
            return 10 * 1024**2  # 10 MB
        elif 'really_cold_100mb' in json_path_str:
            return 100 * 1024**2  # 100 MB
        elif 'really_cold_1gb' in json_path_str:
            return 1 * 1024**3  # 1 GB
        elif 'really_cold_4gb' in json_path_str:
            return 4 * 1024**3  # 4 GB
        
        # Extract test size from directory structure
        test_size = None
        if len(json_path_obj.parts) >= 2:
            parent_dir = json_path_obj.parent.name
            if parent_dir.endswith('m') and any(c.isdigit() for c in parent_dir):
                test_size = parent_dir
        
        # Determine file suffix based on compression type
        if 'raw' in json_path_str or json_path_str.endswith('hot_raw.json') or json_path_str.endswith('cold_raw.json'):
            file_suffix = ".fastq"
        elif 'bgz' in json_path_str:
            file_suffix = ".fastq_bgzipped.gz"
        elif 'gz' in json_path_str:
            file_suffix = ".fastq.gz"
        else:
            return None
        
        # Get actual file size
        if test_size and data_dir.exists():
            file_path = data_dir / f"{test_size}{file_suffix}"
            if file_path.exists():
                return file_path.stat().st_size
        
        return None
    except Exception:
        return None


def get_file_size_from_results(json_path):
    """Extract file size information based on benchmark name and known file paths.
    
    Returns a string with file size and compression type.
    Uses the benchmark name to infer which file was used.
    """
    try:
        # Default data directory
        data_dir = Path('test-data')
        
        # Map benchmark names to files
        json_path_str = str(json_path)
        json_path_obj = Path(json_path)
        
        # Check for really-cold benchmarks (generated files with known sizes)
        if 'really_cold_10mb' in json_path_str:
            return "~10 MB, raw"
        elif 'really_cold_100mb' in json_path_str:
            return "~100 MB, raw"
        elif 'really_cold_1gb' in json_path_str:
            return "~1 GB, raw"
        elif 'really_cold_4gb' in json_path_str:
            return "~4 GB, raw"
        
        # Try to extract test size from directory structure
        # New structure: benchmark_results/benchmark_TIMESTAMP/SIZE/hot_raw.json
        # where SIZE is like "0.1m", "1m", "10m", etc.
        test_size = None
        if len(json_path_obj.parts) >= 2:
            # Check if parent directory looks like a size (e.g., "1m", "10m")
            parent_dir = json_path_obj.parent.name
            if parent_dir.endswith('m') and any(c.isdigit() for c in parent_dir):
                test_size = parent_dir
        
        # Determine compression type
        compression_type = None
        if 'raw' in json_path_str or json_path_str.endswith('hot_raw.json') or json_path_str.endswith('cold_raw.json'):
            file_suffix = ".fastq"
            compression_type = "raw"
        elif 'bgz' in json_path_str:
            file_suffix = ".fastq_bgzipped.gz"
            compression_type = "bgzip"
        elif 'gz' in json_path_str:
            file_suffix = ".fastq.gz"
            compression_type = "gzip"
        else:
            return None
        
        # If we found a test size, look for that specific file
        if test_size and data_dir.exists():
            file_path = data_dir / f"{test_size}{file_suffix}"
            if file_path.exists():
                size_bytes = file_path.stat().st_size
                # Format size nicely
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024**2:
                    size_str = f"{size_bytes/1024:.1f} KB"
                elif size_bytes < 1024**3:
                    size_str = f"{size_bytes/(1024**2):.1f} MB"
                else:
                    size_str = f"{size_bytes/(1024**3):.2f} GB"
                
                return f"{size_str}, {compression_type}"
        
        return None
    except Exception as e:
        return None

def _parse_benchmark_key(name):
    """Parse benchmark key into components.
    
    Keys look like: "0.1m_hot_raw", "1m_cold_gz", "10m_hot_bgz", etc.
    Also handles: "0.1m_really_cold_raw", "1m_really_cold_gz"
    
    Returns:
        tuple: (size, cache_type, compression) or None if can't parse
    """
    name_lower = name.lower()
    
    # Handle really_cold format: "0.1m_really_cold_raw"
    if 'really_cold' in name_lower:
        # Split on really_cold to get size and compression
        # e.g., "0.1m_really_cold_raw" -> ["0.1m", "raw"]
        parts = name_lower.split('_really_cold_')
        if len(parts) == 2:
            size = parts[0]
            compression = parts[1]
            if compression in ('raw', 'gz', 'bgz'):
                return (size, 'really_cold', compression)
        return None
    
    parts = name_lower.split('_')
    
    # Try to extract: size_cache_compression (e.g., "1m_hot_raw")
    if len(parts) >= 3:
        size = parts[0]
        cache_type = parts[1] if parts[1] in ('hot', 'cold') else None
        compression = parts[2] if parts[2] in ('raw', 'gz', 'bgz') else None
        if cache_type and compression:
            return (size, cache_type, compression)
    
    # Legacy format: "hot_raw", "cold_gz" (no size)
    if len(parts) == 2:
        if parts[0] in ('hot', 'cold') and parts[1] in ('raw', 'gz', 'bgz'):
            return ('default', parts[0], parts[1])
    
    return None


def plot_mean_times(data_dict, title="Execution Time Comparison", file_sizes=None, 
                    cache_type='hot', grid_layout=True):
    """Create bar plot of mean execution times using Altair.
    
    Args:
        data_dict: Dictionary of benchmark name to DataFrame
        title: Overall chart title
        file_sizes: Optional dictionary mapping benchmark names to file sizes
        cache_type: 'hot' or 'cold' - which cache type to display
        grid_layout: If True, arrange in grid (rows=size, cols=compression)
                    If False, use original horizontal layout
    
    Charts include interactive legend - click to filter parsers.
    """
    colors = get_color_palette()
    
    if not grid_layout:
        # Original behavior - horizontal layout
        return _plot_mean_times_horizontal(data_dict, title, file_sizes, colors)
    
    # Parse all benchmark keys and organize by compression and size
    organized_data = {}  # {(compression, size): (name, df)}
    
    for name, df in data_dict.items():
        if len(df) == 0:
            print(f"Skipping {name} - no successful results")
            continue
        
        parsed = _parse_benchmark_key(name)
        if parsed is None:
            # Silently skip unparseable keys
            continue
        
        size, cache, compression = parsed
        
        # Filter by cache type
        if cache != cache_type:
            continue
        
        organized_data[(compression, size)] = (name, df)
    
    if not organized_data:
        print(f"Warning: No data to plot for cache_type={cache_type}")
        return None
    
    # Get unique compressions and sizes, sorted
    compressions = sorted(set(comp for comp, _ in organized_data.keys()),
                         key=lambda x: {'raw': 0, 'gz': 1, 'bgz': 2}.get(x, 3))
    
    # Sort sizes numerically
    def size_sort_key(s):
        if s == 'default':
            return 0
        try:
            return float(s.replace('m', '').replace('M', ''))
        except:
            return 999
    
    sizes = sorted(set(size for _, size in organized_data.keys()), key=size_sort_key)
    
    compression_labels = {'raw': 'Raw FASTQ', 'gz': 'Gzipped', 'bgz': 'Bgzipped'}
    
    # Combine all data into a single DataFrame for consistent visualization
    # This ensures all parsers appear in all panels
    combined_rows = []
    for (comp, size), (name, df) in organized_data.items():
        for row in df.iter_rows(named=True):
            combined_rows.append({
                'command': row['command'],
                'mean': row['mean'],
                'stddev': row['stddev'] if row['stddev'] is not None else 0.0,
                'min': row['min'],
                'max': row['max'],
                'compression': comp,
                'size': size,
                'benchmark_name': name
            })
    
    if not combined_rows:
        print("Warning: No data to plot")
        return None
    
    combined_df = pl.DataFrame(combined_rows)
    
    # Get all unique parsers for consistent coloring
    all_parsers = sorted(combined_df['command'].unique().to_list())
    
    # Create interactive selection for legend - toggle behavior
    selection = alt.selection_point(name='mean_times_sel', fields=['command'], bind='legend', toggle=True)
    
    # Build grid of charts - rows=sizes, cols=compressions (pivoted for better width usage)
    rows = []
    for size in sizes:
        row_charts = []
        for compression in compressions:
            key = (compression, size)
            if key in organized_data:
                name, _ = organized_data[key]
                
                # Filter combined data for this specific cell
                cell_df = combined_df.filter(
                    (pl.col('compression') == compression) & (pl.col('size') == size)
                )
                
                # Create bar chart with selection
                base = alt.Chart(cell_df).encode(
                    x=alt.X('command:N', 
                           title='Parser',
                           sort=alt.EncodingSortField(field='mean', order='ascending'),
                           axis=alt.Axis(labelAngle=-45, labelLimit=100)),
                    color=alt.Color('command:N', 
                                  scale=alt.Scale(domain=all_parsers, range=colors),
                                  legend=alt.Legend(title='Parser (click to toggle)')),
                    opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
                ).add_params(selection)
                
                bars = base.mark_bar().encode(
                    y=alt.Y('mean:Q', title='Time (s)'),
                    tooltip=[
                        alt.Tooltip('command:N', title='Parser'),
                        alt.Tooltip('mean:Q', title='Mean', format='.3f'),
                        alt.Tooltip('stddev:Q', title='Std Dev', format='.3f'),
                        alt.Tooltip('min:Q', title='Min', format='.3f'),
                        alt.Tooltip('max:Q', title='Max', format='.3f')
                    ]
                )
                
                error_bars = base.mark_errorbar(extent='stdev').encode(
                    y=alt.Y('mean:Q'),
                    yError='stddev:Q'
                )
                
                # Title shows compression type; row header shows size
                chart_title = compression_labels.get(compression, compression)
                if file_sizes and name in file_sizes:
                    chart_title += f" ({file_sizes[name]})"
                
                chart = (bars + error_bars).properties(
                    title=chart_title,
                    width=350,
                    height=250
                )
                row_charts.append(chart)
            else:
                # Empty placeholder
                empty_df = pl.DataFrame({'command': ['N/A'], 'mean': [0.0]})
                chart = alt.Chart(empty_df).mark_text(text='No Data').properties(
                    title=compression_labels.get(compression, compression),
                    width=350,
                    height=250
                )
                row_charts.append(chart)
        
        if row_charts:
            # Add row label (size) as first element
            size_display = size.upper() if size != 'default' else 'Default'
            row_label = alt.Chart().mark_text(
                text=f"{size_display} reads",
                fontSize=12,
                fontWeight='bold',
                angle=270
            ).properties(width=25, height=250)
            
            row = alt.hconcat(row_label, *row_charts, spacing=5)
            rows.append(row)
    
    if not rows:
        print("Warning: No charts to display")
        return None
    
    # Stack rows vertically with independent Y scales per panel
    final_chart = alt.vconcat(*rows, spacing=10).resolve_scale(
        y='independent'
    ).properties(
        title=alt.TitleParams(
            text=f"{title} ({cache_type.title()} Cache)",
            fontSize=16, 
            fontWeight='bold'
        )
    ).configure_axis(
        gridOpacity=0.3
    ).configure_legend(
        orient='right',
        titleFontSize=12,
        labelFontSize=10
    )
    
    # Save to plots directory
    plots_dir = Path('plots')
    plots_dir.mkdir(exist_ok=True)
    final_chart.save(str(plots_dir / f'mean_execution_times_{cache_type}.html'), format='html')
    
    return final_chart


def _plot_mean_times_horizontal(data_dict, title, file_sizes, colors):
    """Original horizontal layout for plot_mean_times (internal helper)."""
    charts = []
    
    for name, df in data_dict.items():
        # Skip empty DataFrames (all commands failed)
        if len(df) == 0:
            print(f"Skipping {name} - no successful results")
            continue
            
        # Add benchmark name to dataframe
        plot_df = df.with_columns(pl.lit(name.replace("_", " ").title()).alias('benchmark'))
        
        # Create bar chart with error bars
        base = alt.Chart(plot_df).encode(
            x=alt.X('command:N', 
                   title='Parser',
                   sort=alt.EncodingSortField(field='command', order='ascending'),
                   axis=alt.Axis(labelAngle=-45)),
            color=alt.Color('command:N', 
                          scale=alt.Scale(range=colors),
                          legend=None)
        )
        
        bars = base.mark_bar(opacity=0.8).encode(
            y=alt.Y('mean:Q', title='Time (seconds)'),
            tooltip=[
                alt.Tooltip('command:N', title='Parser'),
                alt.Tooltip('mean:Q', title='Mean', format='.3f'),
                alt.Tooltip('stddev:Q', title='Std Dev', format='.3f'),
                alt.Tooltip('min:Q', title='Min', format='.3f'),
                alt.Tooltip('max:Q', title='Max', format='.3f')
            ]
        )
        
        # Error bars
        error_bars = base.mark_errorbar(extent='stdev').encode(
            y=alt.Y('mean:Q'),
            yError='stddev:Q'
        )
        
        # Combine bars and error bars with title (include file size if available)
        chart_title = name.replace("_", " ").title()
        if file_sizes and name in file_sizes:
            chart_title += f" ({file_sizes[name]})"
        
        chart = (bars + error_bars).properties(
            title=chart_title,
            width=400,
            height=400
        )
        
        charts.append(chart)
    
    if not charts:
        print("Warning: No data to plot in plot_mean_times")
        return None
    
    # Combine all charts horizontally
    final_chart = alt.hconcat(*charts).properties(
        title=alt.TitleParams(text=title, fontSize=16, fontWeight='bold')
    ).configure_axis(
        gridOpacity=0.3
    )
    
    # Save to plots directory
    plots_dir = Path('plots')
    plots_dir.mkdir(exist_ok=True)
    final_chart.save(str(plots_dir / 'mean_execution_times.html'), format='html')
    
    return final_chart

def compare_raw_vs_gzipped(all_data):
    """Compare performance on raw vs gzipped files using Altair."""
    # Filter for hot cache results (handle both old and new naming)
    hot_results = {k: v for k, v in all_data.items() if 'hot' in k}
    
    # Find raw and gz results (could have size prefixes like "1m_hot_raw")
    raw_keys = [k for k in hot_results.keys() if 'raw' in k and len(hot_results[k]) > 0]
    gz_keys = [k for k in hot_results.keys() if 'gz' in k and 'bgz' not in k and len(hot_results[k]) > 0]
    
    if not raw_keys or not gz_keys:
        print("Need both hot_raw and hot_gz results for comparison")
        print(f"Found raw: {raw_keys}, gz: {gz_keys}")
        return None
    
    # Use first available (or combine multiple sizes if available)
    raw_dfs = []
    for key in raw_keys:
        df = hot_results[key].with_columns(
            pl.lit('Raw FASTQ').alias('file_type'),
            pl.lit(key.split('_')[0] if '_' in key else 'default').alias('size')
        )
        raw_dfs.append(df)
    
    gz_dfs = []
    for key in gz_keys:
        df = hot_results[key].with_columns(
            pl.lit('Gzipped FASTQ').alias('file_type'),
            pl.lit(key.split('_')[0] if '_' in key else 'default').alias('size')
        )
        gz_dfs.append(df)
    
    combined_df = pl.concat(raw_dfs + gz_dfs)
    
    # Create grouped bar chart
    chart = alt.Chart(combined_df).mark_bar(opacity=0.8).encode(
        x=alt.X('command:N', title='Parser', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('mean:Q', title='Time (seconds)'),
        color=alt.Color('file_type:N', 
                       scale=alt.Scale(domain=['Raw FASTQ', 'Gzipped FASTQ'],
                                     range=['#3498db', '#9b59b6']),
                       legend=alt.Legend(title='File Type')),
        xOffset='file_type:N',
        tooltip=[
            alt.Tooltip('command:N', title='Parser'),
            alt.Tooltip('file_type:N', title='Type'),
            alt.Tooltip('mean:Q', title='Mean', format='.3f'),
            alt.Tooltip('stddev:Q', title='Std Dev', format='.3f')
        ]
    ).properties(
        title='Raw vs Gzipped FASTQ Performance',
        width=600,
        height=400
    )
    
    # Add error bars
    error_bars = alt.Chart(combined_df).mark_errorbar(extent='stdev').encode(
        x=alt.X('command:N'),
        y=alt.Y('mean:Q'),
        yError='stddev:Q',
        xOffset='file_type:N'
    )
    
    final_chart = (chart + error_bars).configure_axis(gridOpacity=0.3)
    
    # Save to plots directory
    plots_dir = Path('plots')
    plots_dir.mkdir(exist_ok=True)
    final_chart.save(str(plots_dir / 'raw_vs_gzipped_comparison.html'), format='html')
    
    # Print speedup analysis
    print("\n=== Performance Analysis ===")
    parsers = sorted(set(combined_df['command'].to_list()))
    
    # Get unique sizes
    sizes = sorted(set(combined_df['size'].to_list()))
    
    for size in sizes:
        if size != 'default':
            print(f"\n--- Size: {size} ---")
        
        size_data = combined_df.filter(pl.col('size') == size)
        
        for parser in parsers:
            raw_data = size_data.filter(
                (pl.col('command') == parser) & (pl.col('file_type') == 'Raw FASTQ')
            )
            gz_data = size_data.filter(
                (pl.col('command') == parser) & (pl.col('file_type') == 'Gzipped FASTQ')
            )
            
            if len(raw_data) > 0 and len(gz_data) > 0:
                raw_time = raw_data['mean'][0]
                gz_time = gz_data['mean'][0]
                speedup = gz_time / raw_time
                print(f"\n{parser}:")
                print(f"  Raw:     {raw_time:.2f}s")
                print(f"  Gzipped: {gz_time:.2f}s")
                print(f"  Ratio:   {speedup:.2f}x {'slower' if speedup > 1 else 'faster'}")
    
    return final_chart


def parse_benchmark_data(json_path):
    """Parse hyperfine results into a DataFrame.
    
    Handles missing results from failed commands (when --ignore-failure is used).
    Commands that failed will not appear in the returned DataFrame.
    Also handles empty or corrupted JSON files gracefully.
    """
    try:
        data = load_hyperfine_results(json_path)
    except json.JSONDecodeError as e:
        print(f"⚠️  Skipping {json_path}: Invalid or empty JSON file ({e})")
        # Return empty DataFrame with correct schema
        return pl.DataFrame(schema={
            'command': pl.Utf8,
            'mean': pl.Float64,
            'stddev': pl.Float64,
            'median': pl.Float64,
            'min': pl.Float64,
            'max': pl.Float64,
            'times': pl.List(pl.Float64)
        })
    
    # Extract file size if available
    file_size = get_file_size_from_results(json_path)
    
    records = []
    for result in data['results']:
        # Check if command failed by examining exit codes
        # With --ignore-failure, hyperfine includes exit_codes field
        exit_codes = result.get('exit_codes', [])
        if exit_codes and any(code != 0 for code in exit_codes):
            failed_runs = sum(1 for code in exit_codes if code != 0)
            print(f"⚠️  Command '{result.get('command', 'unknown')}' failed {failed_runs}/{len(exit_codes)} runs - excluding from results")
            continue
        
        # Also check if command succeeded (has timing data)
        # Failed commands with --ignore-failure won't have 'mean' field or will have None
        if 'mean' not in result or result['mean'] is None:
            print(f"⚠️  Command '{result.get('command', 'unknown')}' has no timing data - excluding from results")
            continue
            
        record = {
            'command': result['command'],
            'mean': result['mean'],
            'stddev': result.get('stddev', 0.0),
            'median': result.get('median', result['mean']),
            'min': result.get('min', result['mean']),
            'max': result.get('max', result['mean']),
            'times': result.get('times', [result['mean']])
        }
        records.append(record)
    
    if not records:
        print(f"Warning: No successful results found in {json_path}")
        # Return empty DataFrame with correct schema
        return pl.DataFrame(schema={
            'command': pl.Utf8,
            'mean': pl.Float64,
            'stddev': pl.Float64,
            'median': pl.Float64,
            'min': pl.Float64,
            'max': pl.Float64,
            'times': pl.List(pl.Float64)
        })
    
    return pl.DataFrame(records)

def plot_scatter_runs(data_dict, file_sizes=None):
    """Create scatter plots of individual run times using Altair.
    
    Args:
        data_dict: Dictionary of benchmark name to DataFrame
        file_sizes: Optional dictionary mapping benchmark names to file sizes
    
    Charts include interactive legend - click to filter parsers.
    """
    colors = get_color_palette()
    
    # Parse and organize data by size and compression (hot cache only)
    organized_data = {}
    all_parsers = set()
    
    for name, df in data_dict.items():
        if len(df) == 0:
            continue
        
        parsed = _parse_benchmark_key(name)
        if parsed is None:
            continue
        
        size, cache, compression = parsed
        if cache != 'hot':  # Only show hot cache
            continue
        
        organized_data[(compression, size)] = (name, df)
        for row in df.iter_rows(named=True):
            all_parsers.add(row['command'])
    
    if not organized_data:
        # Fallback to old behavior
        return _plot_scatter_runs_simple(data_dict, file_sizes, colors)
    
    all_parsers = sorted(all_parsers)
    
    compressions = sorted(set(comp for comp, _ in organized_data.keys()),
                         key=lambda x: {'raw': 0, 'gz': 1, 'bgz': 2}.get(x, 3))
    
    def size_sort_key(s):
        if s == 'default':
            return 0
        try:
            return float(s.replace('m', '').replace('M', ''))
        except:
            return 999
    
    sizes = sorted(set(size for _, size in organized_data.keys()), key=size_sort_key)
    compression_labels = {'raw': 'Raw', 'gz': 'Gzip', 'bgz': 'Bgzip'}
    
    # Interactive selection
    selection = alt.selection_point(name='scatter_sel', fields=['command'], bind='legend')
    
    # Build grid - rows=sizes, cols=compressions
    rows = []
    for size in sizes:
        row_charts = []
        for compression in compressions:
            key = (compression, size)
            if key in organized_data:
                name, df = organized_data[key]
                
                # Expand times
                expanded_rows = []
                for row in df.iter_rows(named=True):
                    for run_idx, time_val in enumerate(row['times']):
                        expanded_rows.append({
                            'command': row['command'],
                            'run': run_idx,
                            'time': time_val,
                            'mean': row['mean']
                        })
                
                run_df = pl.DataFrame(expanded_rows)
                
                points = alt.Chart(run_df).mark_circle(size=60, opacity=0.6).encode(
                    x=alt.X('run:Q', title='Run'),
                    y=alt.Y('time:Q', title='Time (s)'),
                    color=alt.Color('command:N', 
                                  scale=alt.Scale(domain=all_parsers, range=colors[:len(all_parsers)]),
                                  legend=alt.Legend(title='Parser (click to filter)')),
                    opacity=alt.condition(selection, alt.value(0.7), alt.value(0.1)),
                    tooltip=[
                        alt.Tooltip('command:N', title='Parser'),
                        alt.Tooltip('run:Q', title='Run'),
                        alt.Tooltip('time:Q', title='Time', format='.3f')
                    ]
                ).add_params(selection)
                
                mean_lines = alt.Chart(run_df).mark_rule(strokeDash=[3, 3], opacity=0.5).encode(
                    y='mean:Q',
                    color=alt.Color('command:N', scale=alt.Scale(domain=all_parsers, range=colors[:len(all_parsers)]), legend=None),
                    opacity=alt.condition(selection, alt.value(0.7), alt.value(0.1))
                ).add_params(selection)
                
                chart = (points + mean_lines).properties(
                    title=compression_labels.get(compression, compression),
                    width=180,
                    height=160
                )
                row_charts.append(chart)
            else:
                empty_df = pl.DataFrame({'run': [0], 'time': [0.0]})
                chart = alt.Chart(empty_df).mark_text(text='No Data').properties(
                    title=compression_labels.get(compression, compression),
                    width=180,
                    height=160
                )
                row_charts.append(chart)
        
        if row_charts:
            size_display = size.upper() if size != 'default' else 'Default'
            row_label = alt.Chart().mark_text(
                text=f"{size_display}",
                fontSize=11,
                fontWeight='bold',
                angle=270
            ).properties(width=20, height=160)
            
            row = alt.hconcat(row_label, *row_charts, spacing=5)
            rows.append(row)
    
    if not rows:
        return _plot_scatter_runs_simple(data_dict, file_sizes, colors)
    
    final_chart = alt.vconcat(*rows, spacing=10).properties(
        title=alt.TitleParams(text='Individual Run Times (Hot Cache)', 
                             fontSize=16, fontWeight='bold')
    ).configure_axis(
        gridOpacity=0.3
    ).configure_legend(
        orient='right',
        titleFontSize=12,
        labelFontSize=10
    )
    
    # Save to plots directory
    plots_dir = Path('plots')
    plots_dir.mkdir(exist_ok=True)
    final_chart.save(str(plots_dir / 'individual_run_times_scatter.html'), format='html')
    
    return final_chart


def _plot_scatter_runs_simple(data_dict, file_sizes, colors):
    """Simple vertical layout for scatter plots (fallback)."""
    charts = []
    
    for name, df in data_dict.items():
        if len(df) == 0:
            continue
            
        expanded_rows = []
        for row in df.iter_rows(named=True):
            for run_idx, time_val in enumerate(row['times']):
                expanded_rows.append({
                    'command': row['command'],
                    'run': run_idx,
                    'time': time_val,
                    'mean': row['mean']
                })
        
        run_df = pl.DataFrame(expanded_rows)
        
        points = alt.Chart(run_df).mark_circle(size=80, opacity=0.6).encode(
            x=alt.X('run:Q', title='Run Number'),
            y=alt.Y('time:Q', title='Time (seconds)'),
            color=alt.Color('command:N', scale=alt.Scale(range=colors), legend=alt.Legend(title='Parser')),
            tooltip=[
                alt.Tooltip('command:N', title='Parser'),
                alt.Tooltip('time:Q', title='Time', format='.3f')
            ]
        )
        
        mean_lines = alt.Chart(run_df).mark_rule(strokeDash=[5, 5], opacity=0.7).encode(
            y='mean:Q',
            color=alt.Color('command:N', scale=alt.Scale(range=colors), legend=None)
        )
        
        chart_title = name.replace("_", " ").title()
        if file_sizes and name in file_sizes:
            chart_title += f" ({file_sizes[name]})"
        
        chart = (points + mean_lines).properties(title=chart_title, width=600, height=350)
        charts.append(chart)
    
    if not charts:
        return None
    
    final_chart = alt.vconcat(*charts).configure_axis(gridOpacity=0.3)
    
    plots_dir = Path('plots')
    plots_dir.mkdir(exist_ok=True)
    final_chart.save(str(plots_dir / 'individual_run_times_scatter.html'), format='html')
    
    return final_chart


def plot_distributions(data_dict, file_sizes=None):
    """Create box plots showing distribution of execution times using Altair.
    
    Args:
        data_dict: Dictionary of benchmark name to DataFrame
        file_sizes: Optional dictionary mapping benchmark names to file sizes
    
    Charts include interactive legend - click to filter parsers.
    """
    colors = get_color_palette()
    
    # Parse and organize data by size and compression
    organized_data = {}
    all_parsers = set()
    
    for name, df in data_dict.items():
        if len(df) == 0:
            continue
        
        parsed = _parse_benchmark_key(name)
        if parsed is None:
            continue
        
        size, cache, compression = parsed
        if cache != 'hot':  # Only show hot cache
            continue
        
        organized_data[(compression, size)] = (name, df)
        for row in df.iter_rows(named=True):
            all_parsers.add(row['command'])
    
    if not organized_data:
        # Fallback to old behavior if no structured data
        return _plot_distributions_horizontal(data_dict, file_sizes, colors)
    
    all_parsers = sorted(all_parsers)
    
    # Get unique compressions and sizes
    compressions = sorted(set(comp for comp, _ in organized_data.keys()),
                         key=lambda x: {'raw': 0, 'gz': 1, 'bgz': 2}.get(x, 3))
    
    def size_sort_key(s):
        if s == 'default':
            return 0
        try:
            return float(s.replace('m', '').replace('M', ''))
        except:
            return 999
    
    sizes = sorted(set(size for _, size in organized_data.keys()), key=size_sort_key)
    compression_labels = {'raw': 'Raw', 'gz': 'Gzip', 'bgz': 'Bgzip'}
    
    # Interactive selection
    selection = alt.selection_point(name='dist_sel', fields=['command'], bind='legend')
    
    # Build grid - rows=sizes, cols=compressions
    rows = []
    for size in sizes:
        row_charts = []
        for compression in compressions:
            key = (compression, size)
            if key in organized_data:
                name, df = organized_data[key]
                
                # Expand times for box plot
                expanded_rows = []
                for row in df.iter_rows(named=True):
                    for time_val in row['times']:
                        expanded_rows.append({
                            'command': row['command'],
                            'time': time_val
                        })
                
                dist_df = pl.DataFrame(expanded_rows)
                
                chart = alt.Chart(dist_df).mark_boxplot(extent='min-max', size=30).encode(
                    x=alt.X('command:N', 
                           title=None,
                           sort=alt.EncodingSortField(field='command', order='ascending'),
                           axis=alt.Axis(labelAngle=-45, labelFontSize=9)),
                    y=alt.Y('time:Q', title='Time (s)'),
                    color=alt.Color('command:N', 
                                  scale=alt.Scale(domain=all_parsers, range=colors[:len(all_parsers)]),
                                  legend=alt.Legend(title='Parser (click to filter)')),
                    opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
                ).add_params(selection).properties(
                    title=compression_labels.get(compression, compression),
                    width=180,
                    height=180
                )
                row_charts.append(chart)
            else:
                empty_df = pl.DataFrame({'command': ['N/A'], 'time': [0.0]})
                chart = alt.Chart(empty_df).mark_text(text='No Data').properties(
                    title=compression_labels.get(compression, compression),
                    width=180,
                    height=180
                )
                row_charts.append(chart)
        
        if row_charts:
            size_display = size.upper() if size != 'default' else 'Default'
            row_label = alt.Chart().mark_text(
                text=f"{size_display}",
                fontSize=11,
                fontWeight='bold',
                angle=270
            ).properties(width=20, height=180)
            
            row = alt.hconcat(row_label, *row_charts, spacing=5)
            rows.append(row)
    
    if not rows:
        return _plot_distributions_horizontal(data_dict, file_sizes, colors)
    
    final_chart = alt.vconcat(*rows, spacing=10).properties(
        title=alt.TitleParams(text='Execution Time Distributions (Hot Cache)', 
                             fontSize=16, fontWeight='bold')
    ).configure_axis(
        gridOpacity=0.3
    ).configure_legend(
        orient='right',
        titleFontSize=12,
        labelFontSize=10
    )
    
    # Save to plots directory
    plots_dir = Path('plots')
    plots_dir.mkdir(exist_ok=True)
    final_chart.save(str(plots_dir / 'execution_time_distributions.html'), format='html')
    
    return final_chart


def _plot_distributions_horizontal(data_dict, file_sizes, colors):
    """Original horizontal layout for distributions (fallback)."""
    charts = []
    
    for name, df in data_dict.items():
        if len(df) == 0:
            continue
            
        expanded_rows = []
        for row in df.iter_rows(named=True):
            for time_val in row['times']:
                expanded_rows.append({
                    'command': row['command'],
                    'time': time_val
                })
        
        dist_df = pl.DataFrame(expanded_rows)
        
        chart = alt.Chart(dist_df).mark_boxplot(extent='min-max', size=40).encode(
            x=alt.X('command:N', title='Parser', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('time:Q', title='Time (seconds)'),
            color=alt.Color('command:N', scale=alt.Scale(range=colors), legend=None)
        ).properties(
            title=name.replace("_", " ").title() + (f" ({file_sizes[name]})" if file_sizes and name in file_sizes else ""),
            width=350,
            height=350
        )
        
        charts.append(chart)
    
    if not charts:
        return None
    
    final_chart = alt.hconcat(*charts).configure_axis(gridOpacity=0.3)
    
    plots_dir = Path('plots')
    plots_dir.mkdir(exist_ok=True)
    final_chart.save(str(plots_dir / 'execution_time_distributions.html'), format='html')
    
    return final_chart



def plot_really_cold_scaling(all_data):
    """Plot performance scaling across different file sizes for really-cold tests using Altair."""
    # Filter for really-cold results
    really_cold_results = {k: v for k, v in all_data.items() if 'really_cold' in k}
    
    if not really_cold_results:
        print("No really-cold cache results found.")
        return None
    
    # Extract size information and organize data
    size_order = ['10mb', '100mb', '1gb', '4gb']
    size_display = {'10mb': '10 MB', '100mb': '100 MB', '1gb': '1 GB', '4gb': '4 GB'}
    
    # Collect all data
    scaling_rows = []
    for size_key in size_order:
        result_key = f'really_cold_{size_key}'
        if result_key in really_cold_results:
            df = really_cold_results[result_key]
            # Skip empty DataFrames
            if len(df) == 0:
                print(f"Skipping {result_key} - no successful results")
                continue
            for row in df.iter_rows(named=True):
                scaling_rows.append({
                    'size': size_display[size_key],
                    'command': row['command'],
                    'mean': row['mean'],
                    'stddev': row['stddev'] if row['stddev'] is not None else 0.0
                })
    
    if not scaling_rows:
        print("No really-cold data to plot")
        return None
    
    scaling_df = pl.DataFrame(scaling_rows)
    
    # Create line plot with points and interactive selection
    colors = get_color_palette()
    all_parsers = sorted(set(scaling_df['command'].to_list()))
    
    # Interactive selection for legend
    selection = alt.selection_point(name='really_cold_sel', fields=['command'], bind='legend')
    
    base = alt.Chart(scaling_df).encode(
        x=alt.X('size:N', 
               title='File Size',
               sort=['10 MB', '100 MB', '1 GB', '4 GB']),
        color=alt.Color('command:N', 
                       scale=alt.Scale(domain=all_parsers, range=colors[:len(all_parsers)]),
                       legend=alt.Legend(title='Parser (click to filter)')),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).add_params(selection)
    
    lines = base.mark_line(point=True, strokeWidth=2).encode(
        y=alt.Y('mean:Q', title='Time (seconds)'),
        tooltip=[
            alt.Tooltip('command:N', title='Parser'),
            alt.Tooltip('size:N', title='File Size'),
            alt.Tooltip('mean:Q', title='Mean', format='.3f'),
            alt.Tooltip('stddev:Q', title='Std Dev', format='.3f')
        ]
    )
    
    # Add error bars
    error_bars = base.mark_errorbar(extent='stdev').encode(
        y=alt.Y('mean:Q'),
        yError='stddev:Q'
    )
    
    chart = (lines + error_bars).properties(
        title='Really-Cold Cache: Performance Scaling with File Size\n(Includes file generation time)',
        width=600,
        height=400
    ).configure_axis(
        gridOpacity=0.3
    ).configure_legend(
        orient='right',
        titleFontSize=12,
        labelFontSize=10
    )
    
    # Save to plots directory
    plots_dir = Path('plots')
    plots_dir.mkdir(exist_ok=True)
    chart.save(str(plots_dir / 'really_cold_scaling_analysis.html'), format='html')
    
    # Print speedup analysis
    print("\n=== Really-Cold Performance Analysis ===")
    sizes = ['10 MB', '100 MB', '1 GB', '4 GB']
    parsers = sorted(set(scaling_df['command'].to_list()))
    
    for size in sizes:
        size_data = scaling_df.filter(pl.col('size') == size)
        if len(size_data) > 0:
            print(f"\n{size}:")
            for parser in parsers:
                parser_data = size_data.filter(pl.col('command') == parser)
                if len(parser_data) > 0:
                    mean = parser_data['mean'][0]
                    std = parser_data['stddev'][0]
                    print(f"  {parser:20s}: {mean:.2f}s ± {std:.2f}s")
            
            # Calculate speedups
            if len(size_data) >= 2:
                means = [(row['command'], row['mean']) for row in size_data.iter_rows(named=True)]
                slowest_parser, slowest_time = max(means, key=lambda x: x[1])
                fastest_parser, fastest_time = min(means, key=lambda x: x[1])
                
                if slowest_time > 0:
                    speedup = slowest_time / fastest_time
                    print(f"  Speedup: {speedup:.2f}x ({fastest_parser} vs {slowest_parser})")
    
    return chart


def plot_test_size_scaling(all_data, cache_type='hot', file_format='raw'):
    """Plot performance scaling across different test sizes for each parser using Altair.
    
    Args:
        all_data: Dictionary of benchmark name to DataFrame
        cache_type: 'hot' or 'cold' cache benchmarks
        file_format: 'raw', 'gz', or 'bgz' file format
    
    Returns:
        Altair chart or None if no data available
    """
    # Find all results matching the cache type and format
    # Keys look like: "0.1m_hot_raw", "1m_hot_gz", etc.
    # Need to match exact cache_type to avoid 'cold' matching 'really_cold'
    matching_keys = [k for k in all_data.keys() 
                     if f'_{cache_type}_' in k and k.endswith(f'_{file_format}')
                     and 'really_cold' not in k
                     and len(all_data[k]) > 0]
    
    if not matching_keys:
        print(f"No {cache_type} cache {file_format} results found for scaling analysis.")
        return None
    
    # Extract size and parse to numeric value for sorting
    def extract_size_info(key):
        """Extract size from key like '0.1m_hot_raw' -> (0.1, '0.1m', '0.1M')"""
        size_str = key.split('_')[0]  # e.g., "0.1m"
        try:
            # Remove 'm' and convert to float
            size_value = float(size_str.replace('m', '').replace('M', ''))
            display_str = f"{size_str}".upper()  # "0.1M"
            return size_value, size_str, display_str
        except:
            return None, size_str, size_str
    
    # Collect all data with size information
    scaling_rows = []
    size_map = {}  # Map numeric value to display string
    
    for key in matching_keys:
        df = all_data[key]
        size_value, size_key, size_display = extract_size_info(key)
        
        if size_value is None:
            continue
            
        size_map[size_value] = size_display
        
        for row in df.iter_rows(named=True):
            scaling_rows.append({
                'size_value': size_value,
                'size_display': size_display,
                'command': row['command'],
                'mean': row['mean'],
                'stddev': row['stddev'] if row['stddev'] is not None else 0.0
            })
    
    if not scaling_rows:
        print(f"No data to plot for {cache_type} {file_format} scaling")
        return None
    
    scaling_df = pl.DataFrame(scaling_rows)
    
    # Sort sizes for display
    sorted_sizes = sorted(size_map.keys())
    size_order = [size_map[s] for s in sorted_sizes]
    
    # Create line plot with points and interactive selection
    colors = get_color_palette()
    all_parsers = sorted(set(scaling_df['command'].to_list()))
    
    # Interactive selection for legend
    selection = alt.selection_point(name='size_scaling_sel', fields=['command'], bind='legend')
    
    base = alt.Chart(scaling_df).encode(
        x=alt.X('size_display:N', 
               title='Test Size (Million Reads)',
               sort=size_order),
        color=alt.Color('command:N', 
                       scale=alt.Scale(domain=all_parsers, range=colors[:len(all_parsers)]),
                       legend=alt.Legend(title='Parser (click to filter)')),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).add_params(selection)
    
    lines = base.mark_line(point=True, strokeWidth=2).encode(
        y=alt.Y('mean:Q', title='Time (seconds)'),
        tooltip=[
            alt.Tooltip('command:N', title='Parser'),
            alt.Tooltip('size_display:N', title='Test Size'),
            alt.Tooltip('mean:Q', title='Mean', format='.3f'),
            alt.Tooltip('stddev:Q', title='Std Dev', format='.3f')
        ]
    )
    
    # Add error bars
    error_bars = base.mark_errorbar(extent='stdev').encode(
        y=alt.Y('mean:Q'),
        yError='stddev:Q'
    )
    
    format_display = {'raw': 'Raw FASTQ', 'gz': 'Gzipped', 'bgz': 'Bgzipped'}
    chart = (lines + error_bars).properties(
        title=f'Performance Scaling: {cache_type.title()} Cache, {format_display.get(file_format, file_format)}',
        width=600,
        height=400
    ).configure_axis(
        gridOpacity=0.3
    ).configure_legend(
        orient='right',
        titleFontSize=12,
        labelFontSize=10
    )
    
    # Save to plots directory
    plots_dir = Path('plots')
    plots_dir.mkdir(exist_ok=True)
    chart.save(str(plots_dir / f'test_size_scaling_{cache_type}_{file_format}.html'), format='html')
    
    # Print scaling analysis
    print(f"\n=== {cache_type.title()} Cache {format_display.get(file_format, file_format)} Scaling Analysis ===")
    parsers = sorted(set(scaling_df['command'].to_list()))
    
    for parser in parsers:
        parser_data = scaling_df.filter(pl.col('command') == parser).sort('size_value')
        if len(parser_data) > 0:
            print(f"\n{parser}:")
            for row in parser_data.iter_rows(named=True):
                print(f"  {row['size_display']:6s}: {row['mean']:7.3f}s ± {row['stddev']:6.3f}s")
            
            # Calculate scaling ratio (largest / smallest)
            if len(parser_data) >= 2:
                smallest_time = parser_data['mean'][0]
                largest_time = parser_data['mean'][-1]
                smallest_size = parser_data['size_value'][0]
                largest_size = parser_data['size_value'][-1]
                
                if smallest_time > 0 and smallest_size > 0:
                    time_ratio = largest_time / smallest_time
                    size_ratio = largest_size / smallest_size
                    scaling_efficiency = (time_ratio / size_ratio) if size_ratio > 0 else 0
                    print(f"  Scaling: {time_ratio:.2f}x time for {size_ratio:.1f}x data")
                    print(f"  Efficiency: {scaling_efficiency:.2f} (1.0 = linear)")
    
    return chart


def plot_throughput(all_data, available_results, cache_type='hot', file_format='raw'):
    """Plot throughput (GB/s) for each parser based on actual file sizes and mean times.
    
    Args:
        all_data: Dictionary of benchmark name to DataFrame with timing results
        available_results: Dictionary of benchmark name to JSON file path
        cache_type: 'hot' or 'cold' cache benchmarks
        file_format: 'raw', 'gz', or 'bgz' file format
    
    Returns:
        Altair chart or None if no data available
    """
    # Find all results matching the cache type and format
    # Need to match exact cache_type to avoid 'cold' matching 'really_cold'
    matching_keys = [k for k in all_data.keys() 
                     if f'_{cache_type}_' in k and k.endswith(f'_{file_format}')
                     and 'really_cold' not in k
                     and len(all_data[k]) > 0]
    
    if not matching_keys:
        print(f"No {cache_type} cache {file_format} results found for throughput analysis.")
        return None
    
    # Helper to extract size info from key
    def extract_size_info(key):
        """Extract size from key like '0.1m_hot_raw' -> (0.1, '0.1m', '0.1M')"""
        size_str = key.split('_')[0]
        try:
            size_value = float(size_str.replace('m', '').replace('M', ''))
            display_str = f"{size_str}".upper()
            return size_value, size_str, display_str
        except:
            return None, size_str, size_str
    
    # Collect throughput data
    throughput_rows = []
    size_map = {}
    
    for key in matching_keys:
        df = all_data[key]
        
        # Get actual file size in bytes
        if key not in available_results:
            continue
        file_size_bytes = get_file_size_bytes(available_results[key])
        if file_size_bytes is None or file_size_bytes == 0:
            print(f"Warning: Could not get file size for {key}")
            continue
        
        size_value, size_key, size_display = extract_size_info(key)
        if size_value is None:
            continue
        
        size_map[size_value] = size_display
        file_size_gb = file_size_bytes / (1024**3)
        
        for row in df.iter_rows(named=True):
            mean_time = row['mean']
            stddev_time = row['stddev'] if row['stddev'] is not None else 0.0
            
            if mean_time > 0:
                # Calculate throughput in GB/s
                throughput_gbs = file_size_gb / mean_time
                
                # Propagate error: if T = S/t, then dT/T = dt/t
                # So dT = T * (dt/t) = (S/t) * (dt/t) = S * dt / t^2
                throughput_stddev = file_size_gb * stddev_time / (mean_time ** 2)
                
                throughput_rows.append({
                    'size_value': size_value,
                    'size_display': size_display,
                    'command': row['command'],
                    'throughput_gbs': throughput_gbs,
                    'throughput_stddev': throughput_stddev,
                    'file_size_mb': file_size_bytes / (1024**2),
                    'mean_time': mean_time
                })
    
    if not throughput_rows:
        print(f"No throughput data available for {cache_type} {file_format}")
        return None
    
    throughput_df = pl.DataFrame(throughput_rows)
    
    # Sort sizes for display
    sorted_sizes = sorted(size_map.keys())
    size_order = [size_map[s] for s in sorted_sizes]
    
    colors = get_color_palette()
    all_parsers = sorted(set(throughput_df['command'].to_list()))
    
    # Interactive selection for legend
    selection = alt.selection_point(name='throughput_sel', fields=['command'], bind='legend')
    
    base = alt.Chart(throughput_df).encode(
        x=alt.X('size_display:N', 
               title='Test Size (Million Reads)',
               sort=size_order),
        color=alt.Color('command:N', 
                       scale=alt.Scale(domain=all_parsers, range=colors[:len(all_parsers)]),
                       legend=alt.Legend(title='Parser (click to filter)')),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).add_params(selection)
    
    lines = base.mark_line(point=True, strokeWidth=2).encode(
        y=alt.Y('throughput_gbs:Q', title='Throughput (GB/s)'),
        tooltip=[
            alt.Tooltip('command:N', title='Parser'),
            alt.Tooltip('size_display:N', title='Test Size'),
            alt.Tooltip('throughput_gbs:Q', title='Throughput (GB/s)', format='.3f'),
            alt.Tooltip('throughput_stddev:Q', title='Std Dev', format='.4f'),
            alt.Tooltip('file_size_mb:Q', title='File Size (MB)', format='.1f'),
            alt.Tooltip('mean_time:Q', title='Mean Time (s)', format='.3f')
        ]
    )
    
    # Add error bars
    error_bars = base.mark_errorbar(extent='stdev').encode(
        y=alt.Y('throughput_gbs:Q'),
        yError='throughput_stddev:Q'
    )
    
    format_display = {'raw': 'Raw FASTQ', 'gz': 'Gzipped', 'bgz': 'Bgzipped'}
    chart = (lines + error_bars).properties(
        title=f'Throughput: {cache_type.title()} Cache, {format_display.get(file_format, file_format)}',
        width=600,
        height=400
    ).configure_axis(
        gridOpacity=0.3
    ).configure_legend(
        orient='right',
        titleFontSize=12,
        labelFontSize=10
    )
    
    # Save to plots directory
    plots_dir = Path('plots')
    plots_dir.mkdir(exist_ok=True)
    chart.save(str(plots_dir / f'throughput_{cache_type}_{file_format}.html'), format='html')
    
    # Print throughput analysis
    print(f"\n=== {cache_type.title()} Cache {format_display.get(file_format, file_format)} Throughput Analysis ===")
    parsers = sorted(set(throughput_df['command'].to_list()))
    
    for parser in parsers:
        parser_data = throughput_df.filter(pl.col('command') == parser).sort('size_value')
        if len(parser_data) > 0:
            print(f"\n{parser}:")
            for row in parser_data.iter_rows(named=True):
                print(f"  {row['size_display']:6s}: {row['throughput_gbs']:7.3f} GB/s ± {row['throughput_stddev']:6.4f} ({row['file_size_mb']:.1f} MB)")
            
            # Calculate average throughput
            avg_throughput = parser_data['throughput_gbs'].mean()
            print(f"  Average: {avg_throughput:.3f} GB/s")
    
    return chart
