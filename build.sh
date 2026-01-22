#!/bin/bash
set -e

# get and set pixi
if ! command -v pixi &> /dev/null; then
curl -fsSL https://pixi.sh/install.sh | sh
pixi shell 
fi


echo "Generating test data with BBTools..."
echo "Creating multiple sized FASTQ files: 0.1M, 0.5M, 1M, 10M, and 50M reads"

# Download latest BBTools
echo "Downloading BBTools..."
BBTOOLS_DIR="BBTools"
BBTOOLS_VERSION="39.59"
BBTOOLS_URL="https://github.com/bbushnell/BBTools/archive/refs/tags/${BBTOOLS_VERSION}.tar.gz"
if [ ! -d "$BBTOOLS_DIR" ]; then
    wget -nc -O "BBTools-${BBTOOLS_VERSION}.tar.gz" "$BBTOOLS_URL"
    tar -xzf "BBTools-${BBTOOLS_VERSION}.tar.gz"
    mv "BBTools-${BBTOOLS_VERSION}" "$BBTOOLS_DIR"  
    echo "BBTools installed to $BBTOOLS_DIR/"
else
    echo "BBTools already exists in $BBTOOLS_DIR/"
fi

# Download Adoptium JRE 25 (Eclipse Temurin)
# Latest JRE with full SIMD support (i think)
echo "Downloading Adoptium JRE 25..."
JRE_DIR="jre"

JRE_URL="https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.1%2B8/OpenJDK25U-jre_x64_linux_hotspot_25.0.1_8.tar.gz"
JRE_ARCHIVE="OpenJDK25U-jre_x64_linux_hotspot_25.0.1_8.tar.gz"

if [ ! -d "$JRE_DIR" ]; then
    wget -nc "$JRE_URL"
    tar -xzf "$JRE_ARCHIVE"
    # The archive extracts to jdk-25.0.1+8-jre, rename it
    mv jdk-25.0.1+8-jre "$JRE_DIR"
    echo "JRE installed to $JRE_DIR/"
else
    echo "JRE already exists in $JRE_DIR/"
fi
rm -f "$JRE_ARCHIVE" 2>/dev/null || true

# Compile needletail Rust binary
echo "Compiling needletail..."
if command -v cargo &> /dev/null; then
    cargo build --release
    echo "needletail compiled successfully"
    cargo install hyperfine
else
    echo "Warning: cargo not found."
    echo "Install Rust from: https://rustup.rs/"
fi

# Build paraseq_filt CLI
echo "Compiling paraseq_filt..."
if [ -d "paraseq_filt" ]; then
    pushd "paraseq_filt" > /dev/null
    if command -v cargo &>/dev/null; then
        cargo build --release
        # ensure dest dir exists in biofaster repo
        mkdir -p "target/release"
        cp -f target/release/paraseq_filt "target/release/" || true 
    else
        echo "Warning: cargo not found; skipping paraseq_filt build"
    fi
    popd > /dev/null
fi


# Build paraseq_filt python binding
echo "Compiling pyraseq..."
pixi run uv pip install paraseq_filt/
# make sure polars-bio is intialized
pixi run uv pip install polars-bio

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo "JRE: $(pwd)/$JRE_DIR"
echo "BBTools: $(pwd)/$BBTOOLS_DIR"
echo ""