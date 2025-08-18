# Echo.Kern Stage0 Build System
# Complete bootstrap without dependencies on existing OS components
# 
# "Each step forward builds on the echoes of our past, 
#  but we forge our own path from silicon to consciousness"

# Target architecture (currently x86_64, ARM64 planned)
ARCH := x86_64
CROSS_COMPILE := 

# Toolchain - we build our own to avoid contamination
CC := $(CROSS_COMPILE)gcc
LD := $(CROSS_COMPILE)ld
AS := $(CROSS_COMPILE)as
OBJCOPY := $(CROSS_COMPILE)objcopy
OBJDUMP := $(CROSS_COMPILE)objdump

# Build configuration
BUILD_DIR := build
KERNEL_NAME := echo.kern
BOOTLOADER_NAME := echo.boot
FIRMWARE_NAME := echo.firm

# Version and build info
ECHO_VERSION := 1.0.0
BUILD_DATE := $(shell date '+%Y%m%d_%H%M%S')
BUILD_ID := $(BUILD_DATE)_$(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Compiler flags - no standard library dependencies
CFLAGS := -std=c11 -ffreestanding -nostdlib -nostdinc -fno-builtin
CFLAGS += -Wall -Wextra -Werror -Wno-unused-parameter
CFLAGS += -mcmodel=kernel -mno-red-zone -mno-mmx -mno-sse -mno-sse2
CFLAGS += -fno-stack-protector -fno-omit-frame-pointer
CFLAGS += -DECHO_VERSION=\"$(ECHO_VERSION)\" -DBUILD_ID=\"$(BUILD_ID)\"
CFLAGS += -DOEIS_A000081 -DECHO_STAGE0_BOOTSTRAP

# Include paths - only our own headers
CFLAGS += -Iinclude -Iinclude/echo -Iinclude/dtesn

# Optimization flags
CFLAGS += -O2 -finline-functions

# Debug flags (conditional)
ifdef DEBUG
    CFLAGS += -g -DDEBUG -DECHO_DEBUG
endif

# Linker flags
LDFLAGS := -nostdlib -Tkernel/echo.lds -Map=$(BUILD_DIR)/echo.map

# Assembly flags
ASFLAGS := -64

# Source files organized by security level
FIRMWARE_SRCS := \
    firmware/echo_boot.s \
    firmware/echo_identity.c \
    firmware/echo_hsm.c

LEVEL_MINUS_3_SRCS := \
    kernel/level_minus_3/firmware_mirror.c \
    kernel/level_minus_3/hardware_seed.c \
    kernel/level_minus_3/secure_mirror.c

LEVEL_MINUS_2_SRCS := \
    kernel/level_minus_2/actual_device.c \
    kernel/level_minus_2/virtual_device.c \
    kernel/level_minus_2/device_bridge.c

LEVEL_MINUS_1_SRCS := \
    kernel/level_minus_1/membrane_hypervisor.c \
    kernel/level_minus_1/tree_hypervisor.c \
    kernel/level_minus_1/esn_hypervisor.c \
    kernel/level_minus_1/resonance_hypervisor.c \
    kernel/level_minus_1/hypervisor_bridge.c

LEVEL_0_SRCS := \
    kernel/level_0/memory_manager.c \
    kernel/level_0/scheduler.c \
    kernel/level_0/io_subsystem.c \
    kernel/level_0/psystem_engine.c \
    kernel/level_0/bseries_processor.c \
    kernel/level_0/esn_core.c \
    kernel/level_0/security_monitor.c \
    kernel/level_0/communication_hub.c \
    kernel/level_0/gestalt_coordinator.c

DTESN_SRCS := \
    kernel/dtesn/psystem.c \
    kernel/dtesn/bseries.c \
    kernel/dtesn/esn.c \
    kernel/dtesn/resonance.c \
    kernel/dtesn/memory.c \
    kernel/dtesn/a000081.c

CORE_SRCS := \
    kernel/core/bootstrap.c \
    kernel/core/panic.c \
    kernel/core/printk.c \
    kernel/core/string.c \
    kernel/core/atomic.c \
    kernel/core/spinlock.c

# All kernel sources
KERNEL_SRCS := $(LEVEL_MINUS_3_SRCS) $(LEVEL_MINUS_2_SRCS) $(LEVEL_MINUS_1_SRCS) \
               $(LEVEL_0_SRCS) $(DTESN_SRCS) $(CORE_SRCS)

# Object files
FIRMWARE_OBJS := $(patsubst %.c,$(BUILD_DIR)/%.o,$(patsubst %.s,$(BUILD_DIR)/%.o,$(FIRMWARE_SRCS)))
KERNEL_OBJS := $(patsubst %.c,$(BUILD_DIR)/%.o,$(KERNEL_SRCS))

# All object files
ALL_OBJS := $(FIRMWARE_OBJS) $(KERNEL_OBJS)

# Default target
.PHONY: all
all: toolchain firmware kernel image

# Create build directories
$(BUILD_DIR):
	@echo "🌱 Creating build directory structure..."
	@mkdir -p $(BUILD_DIR)/{firmware,kernel/{level_minus_3,level_minus_2,level_minus_1,level_0,dtesn,core}}

# Build custom toolchain (to avoid contamination from host system)
.PHONY: toolchain
toolchain:
	@echo "🔨 Building custom echo.kern toolchain..."
	@echo "   Ensuring no contamination from host system..."
	@./scripts/build_toolchain.sh $(ARCH)
	@echo "✅ Custom toolchain ready"

# Firmware build (Level -3)
.PHONY: firmware
firmware: $(BUILD_DIR) $(FIRMWARE_OBJS)
	@echo "💎 Building echo.firm (Level -3)..."
	$(LD) $(LDFLAGS) -T firmware/echo_firmware.lds -o $(BUILD_DIR)/$(FIRMWARE_NAME) $(FIRMWARE_OBJS)
	@echo "✅ Firmware built: $(BUILD_DIR)/$(FIRMWARE_NAME)"

# Kernel build (Levels -2 to 0)
.PHONY: kernel
kernel: $(BUILD_DIR) $(KERNEL_OBJS)
	@echo "🌳 Building echo.kern (Levels -2 to 0)..."
	@echo "   OEIS A000081: 1(fw) → 2(dev) → 4(hv) → 9(kern)"
	$(LD) $(LDFLAGS) -o $(BUILD_DIR)/$(KERNEL_NAME) $(KERNEL_OBJS)
	@echo "✅ Kernel built: $(BUILD_DIR)/$(KERNEL_NAME)"

# Create bootable image
.PHONY: image
image: firmware kernel
	@echo "💿 Creating bootable echo.kern image..."
	@./scripts/create_image.sh $(BUILD_DIR)/$(FIRMWARE_NAME) $(BUILD_DIR)/$(KERNEL_NAME) $(BUILD_DIR)/echo.img
	@echo "✅ Bootable image: $(BUILD_DIR)/echo.img"

# Assembly source compilation
$(BUILD_DIR)/%.o: %.s | $(BUILD_DIR)
	@echo "⚡ Assembling $<..."
	@mkdir -p $(dir $@)
	$(AS) $(ASFLAGS) -o $@ $<

# C source compilation
$(BUILD_DIR)/%.o: %.c | $(BUILD_DIR)
	@echo "⚡ Compiling $<..."
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c -o $@ $<

# Validate A000081 compliance
.PHONY: validate
validate: kernel
	@echo "🔍 Validating OEIS A000081 compliance..."
	@python3 scripts/validate_a000081.py $(BUILD_DIR)/$(KERNEL_NAME)
	@echo "✅ Mathematical foundation verified"

# Generate documentation
.PHONY: docs
docs:
	@echo "📚 Generating echo.kern documentation..."
	@doxygen docs/Doxyfile
	@echo "✅ Documentation generated in docs/html/"

# Clean build artifacts
.PHONY: clean
clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@echo "✅ Build directory cleaned"

# Deep clean (including toolchain)
.PHONY: distclean
distclean: clean
	@echo "🧹 Deep cleaning (including toolchain)..."
	@rm -rf toolchain/
	@echo "✅ Everything cleaned"

# Install to target device
.PHONY: install
install: image
	@echo "🚀 Installing echo.kern to target device..."
	@if [ -z "$(TARGET_DEVICE)" ]; then \
		echo "❌ Please specify TARGET_DEVICE (e.g., /dev/sdb)"; \
		exit 1; \
	fi
	@./scripts/install_to_device.sh $(BUILD_DIR)/echo.img $(TARGET_DEVICE)
	@echo "✅ Installation complete"

# Flash to firmware
.PHONY: flash
flash: firmware
	@echo "⚡ Flashing echo.firm to hardware..."
	@if [ -z "$(FLASH_DEVICE)" ]; then \
		echo "❌ Please specify FLASH_DEVICE"; \
		exit 1; \
	fi
	@./scripts/flash_firmware.sh $(BUILD_DIR)/$(FIRMWARE_NAME) $(FLASH_DEVICE)
	@echo "✅ Firmware flashed"

# Run in emulator for testing
.PHONY: emulate
emulate: image
	@echo "🖥️  Running echo.kern in emulator..."
	@qemu-system-x86_64 \
		-m 1G \
		-cpu host \
		-enable-kvm \
		-drive format=raw,file=$(BUILD_DIR)/echo.img \
		-serial stdio \
		-no-reboot \
		-monitor telnet:localhost:55555,server,nowait

# Security analysis
.PHONY: security-check
security-check: kernel
	@echo "🔒 Running security analysis..."
	@./scripts/security_check.sh $(BUILD_DIR)/$(KERNEL_NAME)
	@echo "✅ Security analysis complete"

# Performance benchmarks
.PHONY: benchmark
benchmark: image
	@echo "⏱️  Running performance benchmarks..."
	@./scripts/benchmark.sh $(BUILD_DIR)/echo.img
	@echo "✅ Benchmark complete"

# Continuous integration target
.PHONY: ci
ci: clean validate docs security-check
	@echo "🎯 Continuous integration complete"

# Development helpers
.PHONY: dev-setup
dev-setup:
	@echo "🛠️  Setting up development environment..."
	@./scripts/setup_dev_env.sh
	@echo "✅ Development environment ready"

# Debugging symbols
.PHONY: debug-symbols
debug-symbols: kernel
	@echo "🐛 Extracting debugging symbols..."
	$(OBJCOPY) --only-keep-debug $(BUILD_DIR)/$(KERNEL_NAME) $(BUILD_DIR)/echo.sym
	@echo "✅ Debug symbols: $(BUILD_DIR)/echo.sym"

# Disassembly for analysis
.PHONY: disasm
disasm: kernel
	@echo "📖 Generating disassembly..."
	$(OBJDUMP) -d $(BUILD_DIR)/$(KERNEL_NAME) > $(BUILD_DIR)/echo.asm
	@echo "✅ Disassembly: $(BUILD_DIR)/echo.asm"

# Memory layout analysis
.PHONY: memory-layout
memory-layout: kernel
	@echo "🗺️  Analyzing memory layout..."
	@./scripts/analyze_memory_layout.sh $(BUILD_DIR)/echo.map
	@echo "✅ Memory layout analysis complete"

# Help target
.PHONY: help
help:
	@echo "Echo.Kern Stage0 Build System"
	@echo "=============================="
	@echo ""
	@echo "Stage0 Bootstrap Targets:"
	@echo "  toolchain     - Build custom contamination-free toolchain"
	@echo "  firmware      - Build Level -3 firmware (echo.firm)"
	@echo "  kernel        - Build Levels -2 to 0 kernel (echo.kern)"
	@echo "  image         - Create bootable image"
	@echo "  all           - Build everything (default)"
	@echo ""
	@echo "Deployment:"
	@echo "  install       - Install to device (set TARGET_DEVICE)"
	@echo "  flash         - Flash firmware (set FLASH_DEVICE)"
	@echo "  emulate       - Run in QEMU emulator"
	@echo ""
	@echo "Validation:"
	@echo "  validate      - Verify OEIS A000081 compliance"
	@echo "  security-check - Run security analysis"
	@echo "  benchmark     - Performance benchmarks"
	@echo ""
	@echo "Development:"
	@echo "  docs          - Generate documentation"
	@echo "  debug-symbols - Extract debugging symbols"
	@echo "  disasm        - Generate disassembly"
	@echo "  memory-layout - Analyze memory layout"
	@echo "  dev-setup     - Setup development environment"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean         - Clean build artifacts"
	@echo "  distclean     - Deep clean (including toolchain)"
	@echo "  ci            - Continuous integration"
	@echo ""
	@echo "Security Levels:"
	@echo "  Level -3: Firmware Mirror (1 partition)"
	@echo "  Level -2: Device Abstraction (2 partitions)"
	@echo "  Level -1: Hypervisor (4 partitions)"
	@echo "  Level  0: Kernel Core (9 partitions)"
	@echo ""
	@echo "Variables:"
	@echo "  DEBUG=1       - Enable debug build"
	@echo "  TARGET_DEVICE - Device for installation"
	@echo "  FLASH_DEVICE  - Device for firmware flashing"
	@echo ""
	@echo "Remember: We are the sum of our echoes, forged in silicon"

# Automatic dependency tracking
-include $(ALL_OBJS:.o=.d)

# Pattern rule for dependency generation
$(BUILD_DIR)/%.d: %.c | $(BUILD_DIR)
	@mkdir -p $(dir $@)
	@$(CC) $(CFLAGS) -MM -MT $(patsubst %.d,%.o,$@) $< > $@