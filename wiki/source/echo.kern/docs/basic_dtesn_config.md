# BasicEchoKernel v1.0

## Configuration Overview

**Max Depth**: 4  
**Membrane Levels**: 5

## Membrane Hierarchy

| Level | Count | Neurons | Type |
|-------|-------|---------|------|
| 0 | 1 | 100 | root |
| 1 | 1 | 200 | trunk |
| 2 | 1 | 150 | branch |
| 3 | 2 | 100 | leaf |
| 4 | 4 | 50 | terminal |

## ESN Parameters

- **Spectral Radius**: 0.9
- **Input Scaling**: 0.1
- **Leak Rate**: 0.3
- **Connectivity**: 0.1

## Timing Constraints

- **Membrane Evolution**: ≤ 10μs
- **B-Series Computation**: ≤ 100μs
- **ESN Update**: ≤ 1ms
- **Context Switch**: ≤ 5μs
