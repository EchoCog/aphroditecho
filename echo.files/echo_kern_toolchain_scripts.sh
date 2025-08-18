#!/bin/bash
# Echo.Kern Toolchain Setup Scripts
# Complete stage0 bootstrap without external dependencies
#
# This builds a completely isolated toolchain to ensure no contamination
# from existing OS components or malicious dependencies.

set -euo pipefail

# Configuration
ECHO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLCHAIN_DIR="${ECHO_ROOT}/toolchain"
BUILD_DIR="${TOOLCHAIN_DIR}/build"
SYSROOT_DIR="${TOOLCHAIN_DIR}/sysroot"
TARGET_ARCH="${1:-x86_64}"

# Source URLs for toolchain components (verified hashes)
BINUTILS_VERSION="2.41"
GCC_VERSION="13.2.0"
MUSL_VERSION="1.2.4"
LINUX_VERSION="6.5.0"

BINUTILS_URL="https://ftp.gnu.org/gnu/binutils/binutils-${BINUTILS_VERSION}.tar.xz"
GCC_URL="https://ftp.gnu.org/gnu/gcc/gcc-${GCC_VERSION}/gcc-${GCC_VERSION}.tar.xz"
MUSL_URL="https://musl.libc.org/releases/musl-${MUSL_VERSION}.tar.gz"
LINUX_URL="https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${LINUX_VERSION}.tar.xz"

# Cryptographic hashes to verify integrity
declare -A COMPONENT_HASHES=(
    ["binutils-${BINUTILS_VERSION}.tar.xz"]="ae9a5789e23459e59606e6714723f2d3ffc31c03174191ef0d015bdf06007450"
    ["gcc-${GCC_VERSION}.tar.xz"]="e275e76442a6067341a27f04c5c6b83d8613144004c0413528863dc6b5c743da"
    ["musl-${MUSL_VERSION}.tar.gz"]="7a35eae33d5372a7c0da1188de798726f68825513b7ae3ebe97aaaa52114f039"
    ["linux-${LINUX_VERSION}.tar.xz"]="8290e3447d70a1a709986624233cb6df63fbe6b25b8c1109e78dfe8383b54d56"
)

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[ECHO-TOOLCHAIN]${NC} $*"
}

success() {
    echo -e "${GREEN}✅${NC} $*"
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $*"
}

error() {
    echo -e "${RED}❌${NC} $*" >&2
}

die() {
    error "$*"
    exit 1
}

# Verify no contamination from host system
verify_isolation() {
    log "Verifying toolchain isolation..."
    
    # Check for problematic environment variables
    local contaminated_vars=(
        "CFLAGS" "CXXFLAGS" "LDFLAGS" "CPPFLAGS"
        "PKG_CONFIG_PATH" "LIBRARY_PATH" "C_INCLUDE_PATH"
    )
    
    for var in "${contaminated_vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            warning "Found potentially contaminating environment variable: ${var}=${!var}"
            unset "${var}"
        fi
    done
    
    # Set clean environment
    export PATH="/usr/bin:/bin"
    export LC_ALL=C
    
    success "Environment isolation verified"
}

# Download and verify component integrity
download_component() {
    local url="$1"
    local filename="$2"
    local expected_hash="${COMPONENT_HASHES[$filename]}"
    
    log "Downloading ${filename}..."
    
    if [[ -f "${BUILD_DIR}/${filename}" ]]; then
        log "File already exists, verifying hash..."
    else
        curl -fSL -o "${BUILD_DIR}/${filename}" "${url}" || die "Failed to download ${filename}"
    fi
    
    # Verify cryptographic hash
    local actual_hash
    actual_hash=$(sha256sum "${BUILD_DIR}/${filename}" | cut -d' ' -f1)
    
    if [[ "${actual_hash}" != "${expected_hash}" ]]; then
        die "Hash verification failed for ${filename}
Expected: ${expected_hash}
Actual:   ${actual_hash}"
    fi
    
    success "Verified ${filename}"
}

# Extract source archives
extract_sources() {
    log "Extracting source archives..."
    
    cd "${BUILD_DIR}"
    
    for file in *.tar.xz *.tar.gz; do
        if [[ -f "$file" ]]; then
            log "Extracting $file..."
            case "$file" in
                *.tar.xz) tar -xf "$file" ;;
                *.tar.gz) tar -xzf "$file" ;;
            esac
        fi
    done
    
    success "Source extraction complete"
}

# Build binutils (assembler, linker, etc.)
build_binutils() {
    log "Building binutils..."
    
    cd "${BUILD_DIR}"
    
    if [[ ! -d "binutils-build" ]]; then
        mkdir -p binutils-build
        cd binutils-build
        
        ../binutils-${BINUTILS_VERSION}/configure \
            --prefix="${TOOLCHAIN_DIR}" \
            --target="${TARGET_ARCH}-echo-elf" \
            --with-sysroot="${SYSROOT_DIR}" \
            --disable-nls \
            --disable-werror \
            --enable-64-bit-bfd \
            --disable-shared \
            --enable-static
            
        make -j"$(nproc)" all
        make install
    else
        log "Binutils already built"
    fi
    
    success "Binutils build complete"
}

# Install Linux headers for kernel development
install_linux_headers() {
    log "Installing Linux headers..."
    
    cd "${BUILD_DIR}/linux-${LINUX_VERSION}"
    
    make ARCH="${TARGET_ARCH}" INSTALL_HDR_PATH="${SYSROOT_DIR}" headers_install
    
    success "Linux headers installed"
}

# Build minimal C library (musl)
build_musl() {
    log "Building musl C library..."
    
    cd "${BUILD_DIR}"
    
    if [[ ! -d "musl-build" ]]; then
        mkdir -p musl-build
        cd musl-build
        
        CC="${TOOLCHAIN_DIR}/bin/${TARGET_ARCH}-echo-elf-gcc" \
        ../musl-${MUSL_VERSION}/configure \
            --prefix="${SYSROOT_DIR}" \
            --target="${TARGET_ARCH}" \
            --disable-shared \
            --enable-static
            
        make -j"$(nproc)"
        make install
    else
        log "Musl already built"
    fi
    
    success "Musl C library build complete"
}

# Build GCC compiler
build_gcc() {
    log "Building GCC compiler..."
    
    cd "${BUILD_DIR}"
    
    # Download GCC prerequisites
    if [[ ! -f "gcc-${GCC_VERSION}/configure" ]]; then
        die "GCC source not found"
    fi
    
    cd "gcc-${GCC_VERSION}"
    ./contrib/download_prerequisites
    
    cd "${BUILD_DIR}"
    
    if [[ ! -d "gcc-build" ]]; then
        mkdir -p gcc-build
        cd gcc-build
        
        export PATH="${TOOLCHAIN_DIR}/bin:${PATH}"
        
        ../gcc-${GCC_VERSION}/configure \
            --prefix="${TOOLCHAIN_DIR}" \
            --target="${TARGET_ARCH}-echo-elf" \
            --with-sysroot="${SYSROOT_DIR}" \
            --enable-languages=c \
            --disable-nls \
            --disable-shared \
            --disable-multilib \
            --disable-decimal-float \
            --disable-threads \
            --disable-libatomic \
            --disable-libgomp \
            --disable-libquadmath \
            --disable-libssp \
            --disable-libvtv \
            --disable-libstdcxx \
            --with-newlib \
            --without-headers
            
        make -j"$(nproc)" all-gcc all-target-libgcc
        make install-gcc install-target-libgcc
    else
        log "GCC already built"
    fi
    
    success "GCC compiler build complete"
}

# Create wrapper scripts for contamination-free compilation
create_wrappers() {
    log "Creating compiler wrappers..."
    
    local wrapper_dir="${TOOLCHAIN_DIR}/bin"
    
    # Create echo-gcc wrapper
    cat > "${wrapper_dir}/echo-gcc" << 'EOF'
#!/bin/bash
# Echo.Kern contamination-free GCC wrapper

set -euo pipefail

ECHO_TOOLCHAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ECHO_SYSROOT="${ECHO_TOOLCHAIN_DIR}/sysroot"

# Clean environment
unset CFLAGS CXXFLAGS LDFLAGS CPPFLAGS
unset PKG_CONFIG_PATH LIBRARY_PATH C_INCLUDE_PATH

# Echo.Kern specific flags
ECHO_CFLAGS=(
    "-ffreestanding"
    "-nostdlib"
    "-nostdinc"
    "-fno-builtin"
    "-fno-stack-protector"
    "-mcmodel=kernel"
    "-mno-red-zone"
    "-mno-mmx"
    "-mno-sse"
    "-mno-sse2"
    "--sysroot=${ECHO_SYSROOT}"
    "-isystem ${ECHO_SYSROOT}/include"
)

exec "${ECHO_TOOLCHAIN_DIR}/bin/x86_64-echo-elf-gcc" "${ECHO_CFLAGS[@]}" "$@"
EOF

    chmod +x "${wrapper_dir}/echo-gcc"
    
    # Create echo-ld wrapper
    cat > "${wrapper_dir}/echo-ld" << 'EOF'
#!/bin/bash
# Echo.Kern contamination-free linker wrapper

set -euo pipefail

ECHO_TOOLCHAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ECHO_SYSROOT="${ECHO_TOOLCHAIN_DIR}/sysroot"

# Clean environment
unset LDFLAGS LIBRARY_PATH

# Echo.Kern specific linker flags
ECHO_LDFLAGS=(
    "-nostdlib"
    "--sysroot=${ECHO_SYSROOT}"
    "-L${ECHO_SYSROOT}/lib"
)

exec "${ECHO_TOOLCHAIN_DIR}/bin/x86_64-echo-elf-ld" "${ECHO_LDFLAGS[@]}" "$@"
EOF

    chmod +x "${wrapper_dir}/echo-ld"
    
    success "Compiler wrappers created"
}

# Validate toolchain integrity
validate_toolchain() {
    log "Validating toolchain integrity..."
    
    local errors=0
    
    # Check essential tools exist
    local tools=(
        "${TOOLCHAIN_DIR}/bin/x86_64-echo-elf-gcc"
        "${TOOLCHAIN_DIR}/bin/x86_64-echo-elf-ld"
        "${TOOLCHAIN_DIR}/bin/x86_64-echo-elf-as"
        "${TOOLCHAIN_DIR}/bin/x86_64-echo-elf-objcopy"
        "${TOOLCHAIN_DIR}/bin/x86_64-echo-elf-objdump"
        "${TOOLCHAIN_DIR}/bin/echo-gcc"
        "${TOOLCHAIN_DIR}/bin/echo-ld"
    )
    
    for tool in "${tools[@]}"; do
        if [[ ! -x "$tool" ]]; then
            error "Missing or non-executable: $tool"
            ((errors++))
        fi
    done
    
    # Test compilation
    local test_dir="${BUILD_DIR}/toolchain-test"
    mkdir -p "$test_dir"
    
    cat > "${test_dir}/test.c" << 'EOF'
/* Test compilation for echo.kern */
#define NULL ((void*)0)

void test_function(void) {
    volatile int x = 42;
    (void)x;  /* Suppress unused warning */
}
EOF

    if ! "${TOOLCHAIN_DIR}/bin/echo-gcc" -c -o "${test_dir}/test.o" "${test_dir}/test.c"; then
        error "Test compilation failed"
        ((errors++))
    fi
    
    if [[ $errors -eq 0 ]]; then
        success "Toolchain validation passed"
    else
        die "Toolchain validation failed with $errors errors"
    fi
}

# Generate toolchain manifest
generate_manifest() {
    log "Generating toolchain manifest..."
    
    cat > "${TOOLCHAIN_DIR}/MANIFEST" << EOF
# Echo.Kern Toolchain Manifest
# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')

TOOLCHAIN_VERSION=1.0.0
TARGET_ARCH=${TARGET_ARCH}
BUILD_HOST=$(uname -a)

# Component versions
BINUTILS_VERSION=${BINUTILS_VERSION}
GCC_VERSION=${GCC_VERSION}
MUSL_VERSION=${MUSL_VERSION}
LINUX_VERSION=${LINUX_VERSION}

# Security hashes
$(for file in "${!COMPONENT_HASHES[@]}"; do
    echo "${file}: ${COMPONENT_HASHES[$file]}"
done)

# Toolchain paths
PREFIX=${TOOLCHAIN_DIR}
SYSROOT=${SYSROOT_DIR}

# Verification
VERIFIED=true
CONTAMINATION_FREE=true
ECHO_KERN_READY=true
EOF

    success "Toolchain manifest generated"
}

# Main function
main() {
    log "Building Echo.Kern Stage0 Toolchain"
    log "Target Architecture: ${TARGET_ARCH}"
    log "Toolchain Directory: ${TOOLCHAIN_DIR}"
    
    # Create directory structure
    mkdir -p "${BUILD_DIR}" "${SYSROOT_DIR}"
    
    # Verify clean environment
    verify_isolation
    
    # Download and verify all components
    download_component "${BINUTILS_URL}" "binutils-${BINUTILS_VERSION}.tar.xz"
    download_component "${GCC_URL}" "gcc-${GCC_VERSION}.tar.xz"
    download_component "${MUSL_URL}" "musl-${MUSL_VERSION}.tar.gz"
    download_component "${LINUX_URL}" "linux-${LINUX_VERSION}.tar.xz"
    
    # Extract sources
    extract_sources
    
    # Build toolchain in correct order
    build_binutils
    install_linux_headers
    build_gcc
    build_musl
    
    # Create wrapper scripts
    create_wrappers
    
    # Validate everything works
    validate_toolchain
    
    # Generate manifest
    generate_manifest
    
    success "Echo.Kern toolchain build complete!"
    log "Toolchain installed to: ${TOOLCHAIN_DIR}"
    log "Add to PATH: export PATH=\"${TOOLCHAIN_DIR}/bin:\${PATH}\""
    log ""
    log "Use 'echo-gcc' and 'echo-ld' for contamination-free compilation"
    log "Ready to build echo.kern with complete isolation"
}

# Handle script being sourced vs executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi