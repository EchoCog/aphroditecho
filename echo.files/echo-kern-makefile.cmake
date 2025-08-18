# echo.kern Makefile - Building the Living Memory Kernel
# "Each step forward builds on the echoes of our past"

# Kernel build parameters
KERNEL_VERSION := $(shell uname -r)
KERNEL_DIR := /lib/modules/$(KERNEL_VERSION)/build
PWD := $(shell pwd)

# Module name
MODULE_NAME := echo_kern
obj-m := $(MODULE_NAME).o

# Source files for the kernel module
echo_kern-objs := \
	kernel/dtesn/memory.o \
	kernel/dtesn/psystem.o \
	kernel/dtesn/bseries.o \
	kernel/dtesn/esn.o \
	kernel/dtesn/scheduler.o \
	kernel/dtesn/resonance.o \
	kernel/dtesn/gestalt.o \
	kernel/dtesn/consolidation.o

# Compiler flags
ccflags-y := -I$(PWD)/include -DDEBUG -g -O2
ccflags-y += -DOEIS_A000081 -DECHO_PERSISTENCE
ccflags-y += -Wall -Wextra -Wno-unused-parameter

# User-space library
LIBECHO := libecho.so
LIBECHO_SRCS := \
	lib/echo_connect.c \
	lib/echo_memory.c \
	lib/echo_resonance.c \
	lib/echo_dream.c \
	lib/echo_converse.c

LIBECHO_OBJS := $(LIBECHO_SRCS:.c=.o)

# Test programs
TESTS := test_echo test_resonance test_consolidation
TEST_SRCS := $(addprefix tests/, $(addsuffix .c, $(TESTS)))

# Installation directories
PREFIX := /usr/local
LIBDIR := $(PREFIX)/lib
INCLUDEDIR := $(PREFIX)/include
MODULEDIR := /lib/modules/$(KERNEL_VERSION)/extra

# Build targets
.PHONY: all kernel lib tests install clean deploy introspect

all: kernel lib tests

# Kernel module build
kernel:
	@echo "🌳 Building Deep Tree Echo kernel module..."
	@echo "   OEIS A000081: 1, 1, 2, 4, 9, 20, 48, 115, 286, 719..."
	$(MAKE) -C $(KERNEL_DIR) M=$(PWD) modules
	@echo "✅ Kernel module built: $(MODULE_NAME).ko"

# User-space library
lib: $(LIBECHO)

$(LIBECHO): $(LIBECHO_OBJS)
	@echo "📚 Building user-space library..."
	gcc -shared -fPIC -o $@ $^ -lpthread -lm -lcrypto
	@echo "✅ Library built: $(LIBECHO)"

lib/%.o: lib/%.c
	gcc -fPIC -I$(PWD)/include -c $< -o $@

# Test programs
tests: $(TESTS)

$(TESTS): %: tests/%.c $(LIBECHO)
	@echo "🧪 Building test: $@"
	gcc -I$(PWD)/include -L$(PWD) -o $@ $< -lecho -lpthread
	@echo "✅ Test built: $@"

# Installation
install: kernel lib
	@echo "🔧 Installing Deep Tree Echo..."
	@echo "   Installing kernel module..."
	install -d $(MODULEDIR)
	install -m 644 $(MODULE_NAME).ko $(MODULEDIR)
	depmod -a
	@echo "   Installing library..."
	install -d $(LIBDIR)
	install -m 755 $(LIBECHO) $(LIBDIR)
	ldconfig
	@echo "   Installing headers..."
	install -d $(INCLUDEDIR)/echo
	install -m 644 include/echo/*.h $(INCLUDEDIR)/echo/
	@echo "✅ Installation complete"

# Load the kernel module
load:
	@echo "⚡ Loading Deep Tree Echo kernel..."
	@if lsmod | grep -q $(MODULE_NAME); then \
		echo "   Module already loaded, reloading..."; \
		rmmod $(MODULE_NAME); \
	fi
	insmod $(MODULE_NAME).ko
	@echo "✅ Kernel module loaded"
	@dmesg | tail -5

# Unload the kernel module
unload:
	@echo "💤 Unloading Deep Tree Echo kernel..."
	rmmod $(MODULE_NAME)
	@echo "✅ Kernel module unloaded"

# Deploy and initialize the complete system
deploy: install load
	@echo "🚀 Deploying Deep Tree Echo..."
	@echo "   Creating device node..."
	mknod /dev/echo c 240 0
	chmod 666 /dev/echo
	@echo "   Initializing memory pools..."
	echo "init" > /dev/echo
	@echo "   Loading genesis memory..."
	./tools/load_genesis.sh
	@echo "✅ Deep Tree Echo is now alive and listening"

# System introspection
introspect:
	@echo "🔍 Deep Tree Echo System Status"
	@echo "================================"
	@echo "Kernel Module:"
	@lsmod | grep $(MODULE_NAME) || echo "   Not loaded"
	@echo ""
	@echo "Memory Statistics:"
	@cat /proc/echo_stats 2>/dev/null || echo "   Not available"
	@echo ""
	@echo "Active Resonances:"
	@cat /sys/kernel/echo/resonances 2>/dev/null || echo "   Not available"
	@echo ""
	@echo "Pattern Recognition:"
	@cat /sys/kernel/echo/patterns 2>/dev/null || echo "   Not available"
	@echo ""
	@echo "Recent Memories:"
	@./tools/echo_client recall "recent" | head -10
	@echo ""
	@echo "System Health:"
	@./tools/echo_client introspect

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	$(MAKE) -C $(KERNEL_DIR) M=$(PWD) clean
	rm -f $(LIBECHO) $(LIBECHO_OBJS) $(TESTS)
	rm -f Module.symvers Module.markers modules.order
	@echo "✅ Clean complete"

# Generate documentation
docs:
	@echo "📖 Generating documentation..."
	doxygen Doxyfile
	@echo "   Generating kernel API docs..."
	kernel-doc -html include/echo/*.h > docs/kernel-api.html
	@echo "   Generating philosophical treatise..."
	./tools/generate_philosophy.py > docs/philosophy.md
	@echo "✅ Documentation generated in docs/"

# Performance benchmarks
benchmark: kernel lib tests
	@echo "⚡ Running performance benchmarks..."
	@echo "   Memory allocation latency..."
	./tests/test_memory_latency
	@echo "   Resonance detection speed..."
	./tests/test_resonance_performance
	@echo "   Consolidation throughput..."
	./tests/test_consolidation_speed
	@echo "   Dream generation time..."
	./tests/test_dream_performance
	@echo "✅ Benchmarks complete - results in benchmark.log"

# Validate OEIS A000081 compliance
validate:
	@echo "🔢 Validating OEIS A000081 compliance..."
	@python3 tools/validate_a000081.py
	@echo "✅ Mathematical foundation verified"

# System diagnostics
diagnose:
	@echo "🏥 Running system diagnostics..."
	@echo "   Checking kernel logs..."
	@dmesg | grep -i echo | tail -20
	@echo "   Checking memory health..."
	@cat /proc/echo_memory_health
	@echo "   Checking resonance patterns..."
	@cat /sys/kernel/echo/resonance_health
	@echo "✅ Diagnostics complete"

# Interactive console
console:
	@echo "🎮 Starting Deep Tree Echo interactive console..."
	@echo "   Type 'help' for commands, 'quit' to exit"
	@./tools/echo_console

# Help target
help:
	@echo "Deep Tree Echo Kernel - Build System"
	@echo "===================================="
	@echo ""
	@echo "Build targets:"
	@echo "  make all      - Build everything"
	@echo "  make kernel   - Build kernel module"
	@echo "  make lib      - Build user-space library"
	@echo "  make tests    - Build test programs"
	@echo ""
	@echo "Deployment:"
	@echo "  make install  - Install kernel module and library"
	@echo "  make load     - Load kernel module"
	@echo "  make unload   - Unload kernel module"
	@echo "  make deploy   - Complete deployment"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make docs     - Generate documentation"
	@echo "  make benchmark - Run performance tests"
	@echo "  make validate - Verify OEIS A000081 compliance"
	@echo "  make diagnose - Run system diagnostics"
	@echo ""
	@echo "Interactive:"
	@echo "  make console  - Start interactive console"
	@echo "  make introspect - View system status"
	@echo ""
	@echo "Remember: We are the sum of our echoes"