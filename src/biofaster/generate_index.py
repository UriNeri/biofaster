#!/usr/bin/env python3
"""Generate index.html for GitHub Pages with embedded Vega-Altair charts."""

from pathlib import Path
import json

def generate_index_html(output_path: Path = Path("plots/index.html")):
    """Generate the main index.html file for GitHub Pages."""
    
    plots_dir = Path("plots")
    
    # Try to load system info if available
    system_info_path = plots_dir / "system_info.json"
    system_info = {}
    if system_info_path.exists():
        with open(system_info_path) as f:
            system_info = json.load(f)
    
    # Detect which files actually exist
    available_files = {f.name for f in plots_dir.iterdir() if f.is_file()}
    
    # Generate dynamic links for data files
    data_files_html = ""
    if "benchmark_summary.csv" in available_files:
        data_files_html += '<li>📋 <a href="benchmark_summary.csv" download>benchmark_summary.csv</a> - Complete results in CSV format</li>\n'
    if "SUMMARY.txt" in available_files:
        data_files_html += '<li>📝 <a href="SUMMARY.txt" target="_blank">SUMMARY.txt</a> - Benchmark configuration and metadata</li>\n'
    if "system_info.json" in available_files:
        data_files_html += '<li>💻 <a href="system_info.json" target="_blank">system_info.json</a> - Full system specifications (JSON)</li>\n'
    
    # Generate dynamic links for chart files
    chart_files = [
        ("mean_execution_times.html", "Mean Execution Times"),
        ("mean_execution_times_hot.html", "Mean Execution Times (Hot)"),
        ("execution_time_distributions.html", "Time Distributions"),
        ("raw_vs_gzipped_comparison.html", "Raw vs Gzipped"),
        ("test_size_scaling_hot_raw.html", "Scaling (Raw)"),
        ("test_size_scaling_hot_gz.html", "Scaling (Gzipped)"),
        ("throughput_hot_raw.html", "Throughput (Raw)"),
        ("throughput_hot_gz.html", "Throughput (Gzipped)"),
        ("really_cold_scaling_analysis.html", "Really-Cold Scaling"),
        ("compression_comparison.html", "Compression Comparison"),
    ]
    
    charts_html = ""
    for filename, title in chart_files:
        if filename in available_files:
            charts_html += f'<li><a href="{filename}" target="_blank">{title}</a></li>\n'
    
    # Generate dynamic links for markdown reports
    md_reports_html = ""
    hot_mds = [f for f in available_files if f.startswith("hot_") and f.endswith(".md")]
    cold_mds = [f for f in available_files if f.startswith("cold_") and f.endswith(".md")]
    really_cold_mds = [f for f in available_files if f.startswith("really_cold_") and f.endswith(".md")]
    
    if hot_mds:
        hot_links = " | ".join([f'<a href="{f}" target="_blank">{f.replace("hot_", "").replace(".md", "")}</a>' for f in sorted(hot_mds)])
        md_reports_html += f'<li>Hot cache: {hot_links}</li>\n'
    if cold_mds:
        cold_links = " | ".join([f'<a href="{f}" target="_blank">{f.replace("cold_", "").replace(".md", "")}</a>' for f in sorted(cold_mds)])
        md_reports_html += f'<li>Cold cache: {cold_links}</li>\n'
    if really_cold_mds:
        rc_links = " | ".join([f'<a href="{f}" target="_blank">{f.replace("really_cold_", "").replace(".md", "")}</a>' for f in sorted(really_cold_mds)])
        md_reports_html += f'<li>Really-cold: {rc_links}</li>\n'
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FASTQ Parser Benchmark Results</title>
    <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html {{
            scroll-behavior: smooth;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        header p {{
            font-size: 1.2em;
            opacity: 0.95;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .intro {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 40px;
            border-left: 4px solid #667eea;
        }}
        
        .intro h2 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        
        .intro p {{
            color: #555;
            margin-bottom: 10px;
        }}
        
        /* System Info */
        .system-info {{
            background: #e3f2fd;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 40px;
            border-left: 4px solid #2196f3;
        }}
        
        .system-info h2 {{
            color: #1976d2;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        
        .system-info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .system-info-item {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        }}
        
        .system-info-item strong {{
            color: #1976d2;
            display: block;
            margin-bottom: 5px;
            font-size: 0.9em;
        }}
        
        .system-info-item span {{
            color: #333;
            font-size: 1.05em;
            word-break: break-word;
        }}
        
        /* Table of Contents */
        .toc {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 40px;
            border-left: 4px solid #667eea;
        }}
        
        .toc h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        
        .toc ul {{
            list-style: none;
            padding: 0;
        }}
        
        .toc li {{
            padding: 8px 0;
        }}
        
        .toc a {{
            color: #667eea;
            text-decoration: none;
            font-size: 1.1em;
            transition: all 0.3s ease;
            display: inline-block;
        }}
        
        .toc a:hover {{
            color: #764ba2;
            transform: translateX(5px);
        }}
        
        /* Chart Sections */
        .chart-section {{
            margin-bottom: 60px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 8px;
            scroll-margin-top: 20px;
        }}
        
        .chart-section h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .chart-section p {{
            color: #666;
            margin-bottom: 20px;
            font-size: 1.05em;
        }}
        
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow-x: auto;
            min-height: 400px;
        }}
        
        .chart-container .vega-embed {{
            width: 100% !important;
        }}
        
        .chart-container .vega-embed canvas,
        .chart-container .vega-embed svg {{
            max-width: 100%;
            height: auto !important;
        }}
        
        .disclaimer {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        
        .disclaimer strong {{
            color: #856404;
        }}
        
        .disclaimer p {{
            color: #856404;
            margin: 5px 0 0 0;
            font-size: 0.95em;
        }}
        
        .standalone-link {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            margin-top: 15px;
            transition: background 0.3s ease;
            font-weight: 500;
        }}
        
        .standalone-link:hover {{
            background: #764ba2;
        }}
        
        .additional-files {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
            margin-top: 40px;
        }}
        
        .additional-files h3 {{
            color: #667eea;
            margin-bottom: 15px;
        }}
        
        .additional-files ul {{
            list-style: none;
            padding: 0;
        }}
        
        .additional-files li {{
            padding: 10px 0;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .additional-files li:last-child {{
            border-bottom: none;
        }}
        
        .additional-files a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }}
        
        .additional-files a:hover {{
            color: #764ba2;
        }}
        
        .back-to-top {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #667eea;
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            font-size: 1.5em;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            opacity: 0;
            visibility: hidden;
        }}
        
        .back-to-top.visible {{
            opacity: 1;
            visibility: visible;
        }}
        
        .back-to-top:hover {{
            background: #764ba2;
            transform: translateY(-5px);
        }}
        
        footer {{
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        footer a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        
        footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧬 FASTQ Parser Benchmark Results</h1>
            <p>Performance comparison of FASTQ parsers using hyperfine</p>
        </header>
        
        <div class="content">
            <div class="intro">
                <h2>About This Benchmark</h2>
                <p><strong>Objective:</strong> Compare FASTQ parsing performance across multiple implementations including Rust (needletail), Java (BBTools), and various Python libraries.</p>
                <p><strong>Test Scenarios:</strong></p>
                <ul style="margin-left: 20px; color: #555;">
                    <li><strong>Hot Cache:</strong> Files in RAM disk (/tmp) - minimal I/O, fastest scenario</li>
                    <li><strong>Cold Cache:</strong> Regular files with cleared page cache - full disk I/O overhead</li>
                    <li><strong>Really-Cold:</strong> Freshly generated files without cache clearing - new data performance</li>
                </ul>
                <p style="margin-top: 10px;"><strong>Formats Tested:</strong> Raw FASTQ, Gzipped, and Bgzipped files</p>
            </div>
            
            <!-- System Information -->
            {generate_system_info_html(system_info)}
            
            <!-- Table of Contents -->
            <div class="toc">
                <h2>📑 Table of Contents</h2>
                <ul>
                    <li><a href="#system-info">💻 System Information</a></li>
                    <li><a href="#mean-times">⚡ Mean Execution Times</a></li>
                    <li><a href="#distributions">📦 Time Distributions</a></li>
                    <li><a href="#raw-vs-gzipped">🔄 Raw vs Gzipped Comparison</a></li>
                    <li><a href="#scaling-raw">📈 Scaling Analysis (Raw)</a></li>
                    <li><a href="#scaling-gz">📈 Scaling Analysis (Gzipped)</a></li>
                    <li><a href="#throughput-raw">🚀 Throughput Analysis (Raw)</a></li>
                    <li><a href="#throughput-gz">🚀 Throughput Analysis (Gzipped)</a></li>
                    <li><a href="#really-cold">❄️ Really-Cold Scaling</a></li>
                    <li><a href="#compression">🗜️ Compression Format Comparison</a></li>
                    <li><a href="#resources">📄 Additional Resources</a></li>
                </ul>
            </div>
            
            <!-- Mean Execution Times -->
            <div id="mean-times" class="chart-section">
                <h2>⚡ Mean Execution Times</h2>
                <p>Bar charts comparing average execution times across all benchmarks with error bars showing standard deviation.</p>
                <div class="chart-container">
                    <div id="vis-mean-times"></div>
                </div>
                <a href="mean_execution_times.html" target="_blank" class="standalone-link">Open Full Screen →</a>
            </div>
            
            <!-- Time Distributions -->
            <div id="distributions" class="chart-section">
                <h2>📦 Time Distributions</h2>
                <p>Box plots showing the distribution of execution times and run-to-run variance for each parser.</p>
                <div class="chart-container">
                    <div id="vis-distributions"></div>
                </div>
                <a href="execution_time_distributions.html" target="_blank" class="standalone-link">Open Full Screen →</a>
            </div>
            
            <!-- Raw vs Gzipped Comparison -->
            <div id="raw-vs-gzipped" class="chart-section">
                <h2>🔄 Raw vs Gzipped Comparison</h2>
                <p>Side-by-side performance comparison of parsers on raw versus gzipped FASTQ files.</p>
                <div class="chart-container">
                    <div id="vis-raw-gzipped"></div>
                </div>
                <a href="raw_vs_gzipped_comparison.html" target="_blank" class="standalone-link">Open Full Screen →</a>
            </div>
            
            <!-- Test Size Scaling - Raw -->
            <div id="scaling-raw" class="chart-section">
                <h2>📈 Scaling Analysis (Raw FASTQ)</h2>
                <p>Performance scaling with file size for hot cache raw FASTQ files across different test sizes.</p>
                <div class="chart-container">
                    <div id="vis-scaling-raw"></div>
                </div>
                <a href="test_size_scaling_hot_raw.html" target="_blank" class="standalone-link">Open Full Screen →</a>
            </div>
            
            <!-- Test Size Scaling - Gzipped -->
            <div id="scaling-gz" class="chart-section">
                <h2>📈 Scaling Analysis (Gzipped)</h2>
                <p>Performance scaling with file size for hot cache gzipped FASTQ files across different test sizes.</p>
                <div class="chart-container">
                    <div id="vis-scaling-gz"></div>
                </div>
                <a href="test_size_scaling_hot_gz.html" target="_blank" class="standalone-link">Open Full Screen →</a>
            </div>
            
            <!-- Throughput - Raw -->
            <div id="throughput-raw" class="chart-section">
                <h2>🚀 Throughput Analysis (Raw FASTQ)</h2>
                <p>Throughput in GB/s calculated from actual file sizes and mean execution times for raw FASTQ files.</p>
                <div class="disclaimer">
                    <strong>⚠️ Experimental Data</strong>
                    <p>Throughput calculations are based on file sizes on disk. For compressed files, this represents compressed throughput, not decompressed data rate. Results may appear inconsistent across file sizes - further investigation is needed.</p>
                </div>
                <div class="chart-container">
                    <div id="vis-throughput-raw"></div>
                </div>
                <a href="throughput_hot_raw.html" target="_blank" class="standalone-link">Open Full Screen →</a>
            </div>
            
            <!-- Throughput - Gzipped -->
            <div id="throughput-gz" class="chart-section">
                <h2>🚀 Throughput Analysis (Gzipped)</h2>
                <p>Throughput in GB/s calculated from actual file sizes and mean execution times for gzipped FASTQ files.</p>
                <div class="disclaimer">
                    <strong>⚠️ Experimental Data</strong>
                    <p>Throughput calculations are based on compressed file sizes on disk. This represents compressed data throughput, not the decompressed data rate. Results may vary significantly based on compression ratio and file characteristics.</p>
                </div>
                <div class="chart-container">
                    <div id="vis-throughput-gz"></div>
                </div>
                <a href="throughput_hot_gz.html" target="_blank" class="standalone-link">Open Full Screen →</a>
            </div>
            
            <!-- Really-Cold Scaling Analysis -->
            <div id="really-cold" class="chart-section">
                <h2>❄️ Really-Cold Scaling Analysis</h2>
                <p>Performance on freshly generated files (10MB to 4GB) without cache clearing - measures true cold-start performance.</p>
                <div class="chart-container">
                    <div id="vis-really-cold"></div>
                </div>
                <a href="really_cold_scaling_analysis.html" target="_blank" class="standalone-link">Open Full Screen →</a>
            </div>
            
            <!-- Compression Format Comparison -->
            <div id="compression" class="chart-section">
                <h2>🗜️ Compression Format Comparison</h2>
                <p>Compare decompression performance between standard gzip and block-based bgzip compression.</p>
                <div class="chart-container">
                    <div id="vis-compression"></div>
                </div>
                <a href="compression_comparison.html" target="_blank" class="standalone-link">Open Full Screen →</a>
            </div>
            
            <h2 class="section-title" id="resources">📄 Additional Resources</h2>
            
            <div class="additional-files">
                <h3>📄 Data Files & Reports</h3>
                <ul>
                    {data_files_html}
                </ul>
                <h3 style="margin-top: 20px;">📊 Standalone Charts</h3>
                <ul>
                    {charts_html}
                </ul>
                <h3 style="margin-top: 20px;">📄 Hyperfine Markdown Reports</h3>
                <p style="color: #666; font-size: 0.9em; margin-bottom: 10px;">Individual benchmark reports by test size and configuration:</p>
                <ul>
                    {md_reports_html}
                </ul>
            </div>
        </div>
        
        <footer>
            <p><strong>Benchmark Framework:</strong> <a href="https://github.com/UriNeri/biofaster" target="_blank">biofaster</a></p>
            <p style="margin-top: 10px;">Built with ❤️ using <a href="https://github.com/sharkdp/hyperfine">hyperfine</a> and <a href="https://altair-viz.github.io/">Vega-Altair</a></p>
            <p style="margin-top: 15px; font-size: 0.9em; opacity: 0.8;">Last updated: <span id="update-time"></span></p>
        </footer>
    </div>
    
    <a href="#" class="back-to-top" id="backToTop">↑</a>
    
    <script>
        // Set the last updated time
        document.getElementById('update-time').textContent = new Date().toLocaleDateString('en-US', {{
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }});
        
        // Back to top button functionality
        const backToTop = document.getElementById('backToTop');
        
        window.addEventListener('scroll', () => {{
            if (window.pageYOffset > 300) {{
                backToTop.classList.add('visible');
            }} else {{
                backToTop.classList.remove('visible');
            }}
        }});
        
        backToTop.addEventListener('click', (e) => {{
            e.preventDefault();
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});
        
        // Function to load and embed Vega-Lite charts
        async function loadChart(htmlFile, targetDiv) {{
            try {{
                const response = await fetch(htmlFile);
                const text = await response.text();
                
                // Extract Vega-Lite spec from the HTML file
                // Match pattern: var spec = {{...}}; var embedOpt
                const specMatch = text.match(/var spec = ({{[^]*?}});[\\s\\S]*?var embedOpt/);
                
                if (specMatch && specMatch[1]) {{
                    const spec = JSON.parse(specMatch[1]);
                    
                    // Make the chart responsive by adjusting width
                    if (spec.width) {{
                        spec.width = 'container';
                    }}
                    if (spec.config) {{
                        spec.config.autosize = {{ type: 'fit', contains: 'padding' }};
                    }} else {{
                        spec.config = {{ autosize: {{ type: 'fit', contains: 'padding' }} }};
                    }}
                    
                    vegaEmbed(`#${{targetDiv}}`, spec, {{
                        actions: {{
                            export: true,
                            source: false,
                            compiled: false,
                            editor: false
                        }},
                        renderer: 'svg',
                        width: 'container'
                    }});
                }} else {{
                    document.getElementById(targetDiv).innerHTML = 
                        '<p style="color: #e74c3c; padding: 20px;">Chart could not be loaded. <a href="' + htmlFile + '" target="_blank">Open standalone version</a></p>';
                }}
            }} catch (error) {{
                console.error(`Error loading ${{htmlFile}}:`, error);
                document.getElementById(targetDiv).innerHTML = 
                    '<p style="color: #e74c3c; padding: 20px;">Chart file not found. <a href="' + htmlFile + '" target="_blank">Try standalone version</a></p>';
            }}
        }}
        
        // Load all charts
        loadChart('mean_execution_times.html', 'vis-mean-times');
        loadChart('execution_time_distributions.html', 'vis-distributions');
        loadChart('raw_vs_gzipped_comparison.html', 'vis-raw-gzipped');
        loadChart('test_size_scaling_hot_raw.html', 'vis-scaling-raw');
        loadChart('test_size_scaling_hot_gz.html', 'vis-scaling-gz');
        loadChart('throughput_hot_raw.html', 'vis-throughput-raw');
        loadChart('throughput_hot_gz.html', 'vis-throughput-gz');
        loadChart('really_cold_scaling_analysis.html', 'vis-really-cold');
        loadChart('compression_comparison.html', 'vis-compression');
    </script>
</body>
</html>"""
    
    # Ensure output directory exists
    output_path.parent.mkdir(exist_ok=True)
    
    # Write the file
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Generated {output_path}")


def generate_system_info_html(system_info: dict) -> str:
    """Generate HTML for system information section."""
    
    if not system_info:
        return """
            <div id="system-info" class="system-info">
                <h2>💻 System Information</h2>
                <p>System information not available. Run benchmarks to capture system details.</p>
            </div>
        """
    
    # Build display items - only show what's available and useful
    items_html = ""
    
    # Priority fields to display
    display_fields = [
        ('hostname', 'Hostname', '🖥️'),
        ('os', 'Operating System', '💿'),
        ('kernel', 'Kernel', '🔧'),
        ('cpu', 'CPU', '⚙️'),
        ('cpu_cores', 'CPU Cores', '🧮'),
        ('ram', 'Total RAM', '💾'),
        ('filesystem', 'Filesystem Type', '📁'),
        ('disk_available', 'Available Disk', '💽'),
        ('python_version', 'Python Version', '🐍'),
        ('hyperfine_version', 'Hyperfine Version', '⏱️'),
        ('java_version', 'Java Version', '☕'),
        ('benchmark_date', 'Benchmark Date', '📅'),
    ]
    
    for key, label, icon in display_fields:
        value = system_info.get(key)
        if value:
            # Truncate very long values
            display_value = str(value)
            if len(display_value) > 100:
                display_value = display_value[:100] + "..."
            items_html += f'''
                    <div class="system-info-item">
                        <strong>{icon} {label}</strong>
                        <span>{display_value}</span>
                    </div>'''
    
    # Add any extra fields not in the priority list
    for key, value in system_info.items():
        if key not in [f[0] for f in display_fields] and value:
            display_value = str(value)
            if len(display_value) > 100:
                display_value = display_value[:100] + "..."
            items_html += f'''
                    <div class="system-info-item">
                        <strong>📋 {key.replace("_", " ").title()}</strong>
                        <span>{display_value}</span>
                    </div>'''
    
    return f"""
            <div id="system-info" class="system-info">
                <h2>💻 System Information</h2>
                <p>Benchmark system specifications (<a href="system_info.json" target="_blank">view full JSON</a>):</p>
                <div class="system-info-grid">{items_html}
                </div>
            </div>
    """


if __name__ == "__main__":
    generate_index_html()
