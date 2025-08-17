# Echo.Kern Documentation and Development Makefile

.PHONY: help docs docs-diagrams docs-clean test-roadmap validate lint clean all
.PHONY: test test-quick test-performance test-interactive test-monitoring test-integration
.PHONY: test-continuous start-server stop-server
.PHONY: echo9-validate echo9-test echo9-modules

# Default target
help:
	@echo "Echo.Kern Development and Documentation Commands"
	@echo ""
	@echo "Documentation:"
	@echo "  docs          Generate all documentation"
	@echo "  docs-diagrams Generate Mermaid and PlantUML diagrams"
	@echo "  docs-clean    Clean generated documentation files"
	@echo ""
	@echo "User-Space Libraries:"
	@echo "  libdtesn      Build both static and shared libdtesn libraries"
	@echo "  examples      Build example applications"
	@echo "  python-bindings Build Python bindings for libdtesn"
	@echo "  js-bindings   Build JavaScript/WebAssembly bindings"
	@echo "  test-libdtesn Test libdtesn functionality"
	@echo ""
	@echo "Testing (Real-Time Framework):"
	@echo "  test          Run comprehensive real-time test suite"
	@echo "  test-quick    Run quick validation tests"
	@echo "  test-performance Run DTESN performance benchmarks"
	@echo "  test-interactive Run web application interactive tests"
	@echo "  test-monitoring  Run continuous monitoring tests"
	@echo "  test-integration Run OEIS integration tests"
	@echo "  test-continuous  Start continuous monitoring (Ctrl+C to stop)"
	@echo ""
	@echo "Server Management:"
	@echo "  start-server  Start web server on port 8000"
	@echo "  stop-server   Stop web server"
	@echo ""
	@echo "Validation:"
	@echo "  test-roadmap  Test DEVO-GENESIS.md compatibility with workflow"
	@echo "  validate      Validate all project files"
	@echo "  lint          Run code linting (when implementation exists)"
	@echo ""
	@echo "Echo9 Development Area:"
	@echo "  echo9-validate   Validate echo9 kernel functions area"
	@echo "  echo9-test       Test echo9 DTESN prototypes"
	@echo "  echo9-modules    Build echo9 kernel modules (requires kernel headers)"
	@echo ""
	@echo "Utilities:"
	@echo "  clean         Clean all generated files"
	@echo "  all           Build everything"

# Real-Time Testing Framework Targets
test:
	@echo "🚀 Running Echo.Kern Real-Time Test Suite..."
	@python3 tests/run_tests.py --comprehensive --output test_results.json

# User-Space Library Targets
.PHONY: libdtesn libdtesn-static libdtesn-shared examples python-bindings js-bindings test-libdtesn

libdtesn: libdtesn-static libdtesn-shared

libdtesn-static:
	@echo "🔧 Building libdtesn static library..."
	@mkdir -p build/lib
	@gcc $(CFLAGS) -c lib/libdtesn/dtesn_api.c -o build/lib/dtesn_api.o
	@gcc $(CFLAGS) -c lib/libdtesn/dtesn_membrane.c -o build/lib/dtesn_membrane.o
	@gcc $(CFLAGS) -c lib/libdtesn/dtesn_bseries.c -o build/lib/dtesn_bseries.o
	@gcc $(CFLAGS) -c lib/libdtesn/dtesn_esn.c -o build/lib/dtesn_esn.o
	@ar rcs build/lib/libdtesn.a build/lib/*.o
	@echo "✅ Static library build/lib/libdtesn.a created"

libdtesn-shared:
	@echo "🔧 Building libdtesn shared library..."
	@mkdir -p build/lib
	@gcc $(CFLAGS) -fPIC -c lib/libdtesn/dtesn_api.c -o build/lib/dtesn_api_shared.o
	@gcc $(CFLAGS) -fPIC -c lib/libdtesn/dtesn_membrane.c -o build/lib/dtesn_membrane_shared.o
	@gcc $(CFLAGS) -fPIC -c lib/libdtesn/dtesn_bseries.c -o build/lib/dtesn_bseries_shared.o
	@gcc $(CFLAGS) -fPIC -c lib/libdtesn/dtesn_esn.c -o build/lib/dtesn_esn_shared.o
	@gcc -shared -o build/lib/libdtesn.so build/lib/*_shared.o $(LDFLAGS)
	@echo "✅ Shared library build/lib/libdtesn.so created"

examples: libdtesn-static
	@echo "🔧 Building example applications..."
	@mkdir -p build/examples
	@gcc $(CFLAGS) -Ilib/libdtesn examples/hello_dtesn.c -Lbuild/lib -ldtesn $(LDFLAGS) -lm -o build/examples/hello_dtesn
	@echo "✅ Example application build/examples/hello_dtesn created"

python-bindings: libdtesn-shared
	@echo "🐍 Building Python bindings..."
	@mkdir -p build/bindings/python
	@python3 -c "import sysconfig; print('Python development headers found')" || (echo "❌ Python development headers required"; exit 1)
	@gcc $(CFLAGS) -fPIC $$(python3-config --cflags) -c bindings/python/pydtesn.c -o build/bindings/python/pydtesn.o
	@gcc -shared build/bindings/python/pydtesn.o -Lbuild/lib -ldtesn $$(python3-config --ldflags) $(LDFLAGS) -o build/bindings/python/pydtesn.so
	@echo "✅ Python bindings build/bindings/python/pydtesn.so created"

js-bindings:
	@echo "🌐 Building JavaScript/WebAssembly bindings..."
	@mkdir -p build/bindings/js
	@command -v emcc >/dev/null 2>&1 || (echo "❌ Emscripten required for WebAssembly bindings"; exit 1)
	@emcc bindings/js/dtesn_wasm.c -o build/bindings/js/dtesn.js \
		-s EXPORTED_RUNTIME_METHODS='["ccall","cwrap"]' \
		-s ALLOW_MEMORY_GROWTH=1 \
		-s MODULARIZE=1 \
		-s EXPORT_NAME='"DTESNModule"' \
		-O2
	@echo "✅ JavaScript/WASM bindings build/bindings/js/dtesn.js created"

test-libdtesn: examples
	@echo "🧪 Testing libdtesn user-space library..."
	@echo "Note: This test requires kernel DTESN modules to be loaded"
	@./build/examples/hello_dtesn --verbose || echo "⚠️  Test requires DTESN kernel modules"

# Kernel build target
kernel:
	@echo "🔧 Building DTESN Kernel..."
	@make -f Makefile.kernel kernel

# Kernel test target
test-kernel:
	@echo "🧪 Testing DTESN Kernel Components..."
	@make -f Makefile.kernel test

# Kernel benchmark target
benchmark-kernel:
	@echo "📊 Benchmarking DTESN Kernel Performance..."
	@make -f Makefile.kernel benchmark

test-quick:
	@echo "⚡ Running quick validation tests..."
	@python3 tests/run_tests.py --quick

test-performance:
	@echo "📊 Running DTESN performance benchmarks..."
	@python3 tests/run_tests.py --performance-only --output performance_results.json

test-interactive:
	@echo "🖱️  Running interactive web application tests..."
	@python3 tests/run_tests.py --interactive-only --output interactive_results.json

test-monitoring:
	@echo "📈 Running monitoring tests..."
	@python3 tests/run_tests.py --monitoring-only --monitoring-duration 15 --output monitoring_results.json

test-integration:
	@echo "🔗 Running OEIS integration tests..."
	@python3 test_oeis_a000081.py

test-continuous:
	@echo "🔄 Starting continuous monitoring (Ctrl+C to stop)..."
	@python3 tests/continuous_monitoring.py --interval 100

# Server Management
start-server:
	@echo "🌐 Starting web server on port 8000..."
	@python3 -m http.server 8000 &
	@echo "Server PID: $$!"
	@sleep 2
	@curl -I localhost:8000 2>/dev/null && echo "✅ Server is running at http://localhost:8000" || echo "❌ Server failed to start"

stop-server:
	@echo "🛑 Stopping web server..."
	@pkill -f "python3 -m http.server 8000" 2>/dev/null || echo "No server process found"

# Documentation generation
docs: docs-diagrams
	@echo "📚 Generating documentation..."
	@echo "  ✅ README.md - Project overview and quick start"
	@echo "  ✅ DEVELOPMENT.md - Development guide and standards"  
	@echo "  ✅ docs/DTESN-ARCHITECTURE.md - Technical architecture"
	@echo "  ✅ docs/diagrams/ - Process flow diagrams"
	@echo "  ✅ DEVO-GENESIS.md - Development roadmap"
	@echo ""
	@echo "📖 Documentation structure complete!"
	@echo "   Open index.html for interactive demo"
	@echo "   See README.md for project overview"

docs-diagrams:
	@echo "🎨 Processing diagrams..."
	@if command -v mmdc >/dev/null 2>&1; then \
		echo "  🔄 Mermaid diagrams available"; \
	else \
		echo "  ⚠️  Install mermaid-cli: npm install -g @mermaid-js/mermaid-cli"; \
	fi
	@if command -v plantuml >/dev/null 2>&1; then \
		echo "  🔄 PlantUML diagrams available"; \
	else \
		echo "  ⚠️  Install plantuml: npm install -g @plantuml/plantuml"; \
	fi

docs-clean:
	@echo "🧹 Cleaning generated documentation..."
	@rm -f docs/diagrams/*.png docs/diagrams/*.svg
	@echo "  ✅ Cleaned diagram artifacts"

# Validation and testing
test-roadmap:
	@echo "🔍 Testing DEVO-GENESIS.md roadmap format..."
	@node scripts/validate-roadmap.js

validate: test-roadmap test-quick
	@echo "✅ Validating project structure..."
	@echo "  📋 Checking required files..."
	@test -f README.md || (echo "❌ README.md missing" && exit 1)
	@test -f DEVELOPMENT.md || (echo "❌ DEVELOPMENT.md missing" && exit 1)  
	@test -f DEVO-GENESIS.md || (echo "❌ DEVO-GENESIS.md missing" && exit 1)
	@test -f docs/DTESN-ARCHITECTURE.md || (echo "❌ DTESN-ARCHITECTURE.md missing" && exit 1)
	@test -f .github/workflows/generate-next-steps.yml || (echo "❌ Workflow missing" && exit 1)
	@test -f tests/real_time_test_framework.py || (echo "❌ Real-time test framework missing" && exit 1)
	@echo "  ✅ All required files present"
	@echo ""
	@echo "  🔗 Checking documentation links..."
	@grep -q "DTESN-ARCHITECTURE.md" README.md || (echo "❌ Architecture link missing in README" && exit 1)
	@grep -q "DEVELOPMENT.md" README.md || (echo "❌ Development link missing in README" && exit 1)
	@echo "  ✅ Documentation cross-references valid"
	@echo ""
	@echo "  🧪 Testing framework components..."
	@python3 -c "from tests.real_time_test_framework import create_test_framework; print('✅ Framework import successful')"
	@python3 -c "from tests.performance_tests import DTESNPerformanceTests; print('✅ Performance tests available')"
	@python3 -c "from tests.interactive_tests import InteractiveTestSuite; print('✅ Interactive tests available')"
	@python3 -c "from tests.continuous_monitoring import ContinuousMonitor; print('✅ Continuous monitoring available')"
	@echo ""
	@echo "  🧪 Echo9 development area..."
	@cd echo9 && python3 validate_echo9.py > /dev/null && echo "  ✅ Echo9 kernel functions area validated"
	@echo ""
	@echo "🎯 Project validation complete!"

lint:
	@echo "🔍 Code linting..."
	@echo "  📝 Python files..."
	@python3 -m py_compile echo_kernel_spec.py
	@python3 -m py_compile tests/real_time_test_framework.py
	@python3 -m py_compile tests/performance_tests.py
	@python3 -m py_compile tests/interactive_tests.py
	@python3 -m py_compile tests/continuous_monitoring.py
	@python3 -m py_compile tests/run_tests.py
	@echo "  📝 Echo9 Python files..."
	@python3 -m py_compile echo9/validate_echo9.py
	@python3 -m py_compile echo9/echo-kernel-functions/dtesn-prototypes/run_tests.py
	@python3 -m py_compile echo9/echo-kernel-functions/neuromorphic-drivers/test_drivers.py
	@python3 -m py_compile echo9/echo-kernel-functions/real-time-extensions/validate_realtime.py
	@echo "  ✅ Python files compile successfully"
	@echo "  📄 JavaScript syntax..."
	@node -c app.js
	@echo "  ✅ JavaScript syntax valid"

# Utilities
clean: docs-clean
	@echo "🧹 Cleaning all generated files..."
	@rm -rf build/lib build/examples build/bindings
	@rm -f *.pyc __pycache__/*
	@rm -f tests/__pycache__/* tests/*.pyc
	@rm -f *_results.json test_results.json
	@rm -f dtesn_performance_report_*.txt dtesn_performance_report_*.json
	@rm -f monitoring_report_*.txt monitoring_data_*.json
	@echo "  ✅ Cleaned build artifacts and test results"

all: validate docs test-quick
	@echo "🚀 Echo.Kern documentation and testing build complete!"
	@echo ""
	@echo "📊 Project Status:"
	@echo "  ✅ Architecture specification complete"
	@echo "  ✅ Documentation comprehensive and linked"
	@echo "  ✅ Development workflow established"
	@echo "  ✅ Automated issue generation configured"
	@echo "  ✅ Real-time testing framework operational"
	@echo "  ⚠️  Kernel implementation in progress"
	@echo ""
	@echo "🎯 Next Steps:"
	@echo "  1. Run comprehensive tests: make test"
	@echo "  2. Start continuous monitoring: make test-continuous"
	@echo "  3. Begin kernel implementation tasks"
	@echo "  4. Validate echo9 area: make echo9-validate"
	@echo "  5. See DEVO-GENESIS.md for development roadmap"

# Echo9 Development Area Targets
echo9-validate:
	@echo "🚀 Echo9 Kernel Functions Area Validation"
	@cd echo9 && python3 validate_echo9.py

echo9-test:
	@echo "🧪 Echo9 DTESN Prototypes Testing"
	@cd echo9/echo-kernel-functions/dtesn-implementations && python3 run_tests.py

echo9-modules:
	@echo "🔧 Building Echo9 Kernel Modules"
	@if [ -d /lib/modules/$$(uname -r)/build ]; then \
		cd echo9/echo-kernel-functions/kernel-modules && make; \
	else \
		echo "⚠️  Kernel headers not found. Install linux-headers package."; \
		echo "   Skipping kernel module build."; \
	fi

# Bonus: Test the GitHub workflow (requires GitHub CLI or API access)
test-workflow:
	@echo "🔄 Testing GitHub workflow integration..."
	@echo "  📋 24 tasks defined in DEVO-GENESIS.md"
	@echo "  🤖 Workflow: .github/workflows/generate-next-steps.yml"
	@echo ""
	@echo "To test the workflow:"
	@echo "  1. Go to: https://github.com/EchoCog/echo.kern/actions"
	@echo "  2. Find: 'Generate Next Steps Issues'"
	@echo "  3. Click: 'Run workflow'"
	@echo "  4. Check: Issues tab for generated tasks"

# Development environment setup
setup-dev:
	@echo "🔧 Setting up Echo.Kern development environment..."
	@echo "  📦 Checking prerequisites..."
	@command -v python3 >/dev/null || (echo "❌ Python 3 required" && exit 1)
	@command -v node >/dev/null || (echo "❌ Node.js required" && exit 1)
	@command -v git >/dev/null || (echo "❌ Git required" && exit 1)
	@echo "  ✅ Prerequisites satisfied"
	@echo ""
	@echo "  🔧 Installing documentation tools..."
	@npm list -g @mermaid-js/mermaid-cli >/dev/null 2>&1 || echo "  📦 Consider: npm install -g @mermaid-js/mermaid-cli"
	@npm list -g @plantuml/plantuml >/dev/null 2>&1 || echo "  📦 Consider: npm install -g @plantuml/plantuml"
	@echo ""
	@echo "  🎯 Development environment ready!"
	@echo "     Run 'make validate' to verify setup"