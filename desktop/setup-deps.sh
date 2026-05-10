#!/bin/bash
# Setup script for Tauri build dependencies
# Run this before building: source desktop/setup-deps.sh

# Download and extract system dependencies
echo "Setting up Tauri build dependencies..."

DEPS_DIR="/tmp/tauri-deps-all"
mkdir -p "$DEPS_DIR"

# List of required packages
PACKAGES=(
    "libdbus-1-dev"
    "libsoup-3.0-dev"
    "libwebkit2gtk-4.1-dev=2.44.0-2"
    "libjavascriptcoregtk-4.1-dev=2.44.0-2"
    "libgtk-3-dev"
    "libgdk-pixbuf-2.0-dev"
    "libpango1.0-dev"
    "libcairo2-dev"
    "libatk1.0-dev"
    "libatk-bridge2.0-dev"
    "libssl-dev"
    "pkgconf"
    "libpkgconf3"
)

# Download packages
for pkg in "${PACKAGES[@]}"; do
    echo "Downloading $pkg..."
    apt-get download "$pkg" 2>/dev/null
done

# Extract all packages
for deb in *.deb; do
    if [ -f "$deb" ]; then
        echo "Extracting $deb..."
        dpkg-deb -x "$deb" "$DEPS_DIR" 2>/dev/null
    fi
done

# Create pkg-config wrapper
cat > /tmp/my-pkg-config << 'WRAPPER'
#!/bin/bash
if [ "$1" = "--version" ]; then
    echo "0.29.2"
    exit 0
fi

CFLAGS=""
LIBS=""
MISSING=""

for arg in "$@"; do
    if [[ "$arg" == --* ]]; then
        continue
    fi
    pkg=$(echo "$arg" | sed "s/'//g" | sed 's/ >=.*//' | sed 's/ .*//')
    if [ -z "$pkg" ]; then
        continue
    fi

    # Find the .pc file
    PC_FILE=$(find /tmp/tauri-deps-all -name "${pkg}.pc" 2>/dev/null | head -1)
    if [ -z "$PC_FILE" ]; then
        MISSING="$MISSING $pkg"
        continue
    fi

    # Parse the .pc file
    PC_DIR=$(dirname "$PC_FILE")
    if [ -f "$PC_FILE" ]; then
        PC_CFLAGS=$(grep "^Cflags:" "$PC_FILE" 2>/dev/null | sed 's/Cflags: //' | sed "s|\${prefix}|/tmp/tauri-deps-all/usr|g")
        PC_LIBS=$(grep "^Libs:" "$PC_FILE" 2>/dev/null | sed 's/Libs: //' | sed "s|\${prefix}|/tmp/tauri-deps-all/usr|g")
        CFLAGS="$CFLAGS $PC_CFLAGS"
        LIBS="$LIBS $PC_LIBS"
    fi
done

if [ -n "$MISSING" ]; then
    echo "Package(s)$MISSING not found" >&2
    exit 1
fi

case "$1" in
    --cflags)
        echo "$CFLAGS" | sed 's/^ //'
        ;;
    --libs)
        echo "$LIBS" | sed 's/^ //'
        ;;
    --modversion)
        echo "1.0.0"
        ;;
    *)
        exit 1
        ;;
esac
WRAPPER

chmod +x /tmp/my-pkg-config
mkdir -p /tmp/bin
ln -sf /tmp/my-pkg-config /tmp/bin/pkg-config

# Set environment variables
export PATH="/tmp/bin:$PATH"
export PKG_CONFIG_PATH="$DEPS_DIR/usr/lib/x86_64-linux-gnu/pkgconfig:$DEPS_DIR/usr/lib/pkgconfig"
export LD_LIBRARY_PATH="$DEPS_DIR/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export LIBRARY_PATH="$DEPS_DIR/usr/lib/x86_64-linux-gnu:$LIBRARY_PATH"
export C_INCLUDE_PATH="$DEPS_DIR/usr/include:$DEPS_DIR/usr/include/x86_64-linux-gnu"
export CPLUS_INCLUDE_PATH="$DEPS_DIR/usr/include:$DEPS_DIR/usr/include/x86_64-linux-gnu"

echo "Tauri build dependencies setup complete!"
echo "You can now run: cargo check"
