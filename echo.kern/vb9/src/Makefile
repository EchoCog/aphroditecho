# VB9 Portable Makefile
# For Linux/Unix systems without Plan 9

CC = gcc
CFLAGS = -Wall -O2 -std=c99
TARGETS = vb9demo vb9server vb9cognitive
SIZELIMIT = 1400000

all: $(TARGETS)

vb9demo: vb9portable.c
	$(CC) $(CFLAGS) -o vb9demo vb9portable.c

vb9server: vb9server.c
	$(CC) $(CFLAGS) -o vb9server vb9server.c

vb9cognitive: vb9cognitive.c
	$(CC) $(CFLAGS) -o vb9cognitive vb9cognitive.c

# Check if we're under the VB6 1.4MB limit
checksize: $(TARGETS)
	@echo "VB9 Runtime Size Check:"
	@for target in $(TARGETS); do \
		size=$$(stat -f%z $$target 2>/dev/null || stat -c%s $$target 2>/dev/null); \
		echo "$$target: $$size bytes"; \
		if [ $$size -gt $(SIZELIMIT) ]; then \
			echo "ERROR: $$target exceeds 1.4MB VB6 limit!"; \
			exit 1; \
		fi; \
	done
	@echo "SUCCESS: All targets under VB6 1.4MB target!"

# Run the demo
run: vb9demo
	./vb9demo

# Run the 9P server
server: vb9server
	./vb9server

# Run the cognitive integration demo
cognitive: vb9cognitive
	./vb9cognitive

# Clean up
clean:
	rm -f $(TARGETS)
	rm -rf forms/

# Install
install: $(TARGETS) checksize
	cp $(TARGETS) /usr/local/bin/

# Show the VB6 workflow
demo: vb9demo
	@echo "=== The VB6 Workflow in VB9 ==="
	@echo "1. Build the runtime (1.4MB max)"
	@echo "2. Run the form designer"
	@echo "3. Draw your controls"
	@echo "4. Set event handlers"  
	@echo "5. Everything becomes files"
	@echo "6. Drawing IS computing"
	@echo ""
	./vb9demo

# Test the 9P server interactively
demo-server: vb9server
	@echo "=== VB9 9P Server Demo ==="
	@echo "Try these commands:"
	@echo "  ls /forms"
	@echo "  ls /forms/Calculator"  
	@echo "  cat /forms/Calculator/Button1/text"
	@echo "  echo '123' /forms/Calculator/Text1/text"
	@echo "  exec /forms/Calculator/Button1/click"
	@echo "  quit"
	@echo ""
	./vb9server

help:
	@echo "VB9 - Visual Basic for Plan 9 (Portable)"
	@echo "Targets:"
	@echo "  all         - Build all programs"
	@echo "  run         - Run the form demo"
	@echo "  server      - Run the 9P server"
	@echo "  cognitive   - Run Deep Tree Echo integration"
	@echo "  demo        - Show VB6 workflow"
	@echo "  demo-server - Interactive 9P demo"
	@echo "  checksize   - Verify 1.4MB limit"
	@echo "  clean       - Remove build files"
	@echo "  install     - Install to system"

.PHONY: all run server cognitive demo demo-server checksize clean install help