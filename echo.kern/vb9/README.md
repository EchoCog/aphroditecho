# VB9 - Visual Basic for Plan 9

**Drawing is Computing. Rendering is Execution.**

VB9 recreates the legendary simplicity of Visual Basic 6 on Plan 9's distributed architecture.

## Core Philosophy

- **One IDE** - everything included
- **One compile** - produces actual Plan 9 binary  
- **One file** - Form + Code together
- **Zero dependencies** - Plan 9 has the runtime
- **Visual = Actual** - What you draw is what you get

## The VB6 Workflow, Perfected

```
1. Draw form (drag & drop to /dev/draw)
2. Double-click button (writes to /forms/button1/click)
3. Write: echo "Hello" > /dev/cons
4. Hit F5 (mk myapp)
5. IT WORKS. Ship the binary (1.4MB max)
```

## Architecture

Every VB9 form is a Plan 9 service. Every control is a file. Every event is a transaction.

```
/forms/myapp/
├── form.vb9          # Form definition
├── button1/
│   ├── click         # Event handler (executable)
│   ├── text          # Button text
│   └── geometry      # Position and size
├── textbox1/
│   ├── text          # Current value
│   ├── change        # Change event handler
│   └── geometry      # Position and size
└── Makefile          # Auto-generated build file
```

## Runtime Target: 1.4MB

Just like the original VB6 runtime. No bloat, no frameworks, no containers.

## Getting Started

```bash
# Phase 1: Basic form designer
cd vb9/src
mk formdesigner

# Draw your first form
./formdesigner

# Compile and run
mk hello
./hello
```

**VB9**: Because the future should be simpler than the past.