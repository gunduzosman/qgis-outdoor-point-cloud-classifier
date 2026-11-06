# Test plan

The project currently has no automated QGIS/PDAL integration test environment. Before calling a release production-ready, validate at least:

- Plugin loads on each supported QGIS version and registers one Processing provider/algorithm.
- Missing PDAL executable produces an actionable Processing error.
- LAS input produces a distinct output and the source file checksum remains unchanged.
- LAZ read/write works with the actual PDAL build in use.
- Output LAS classes and counts are checked on known synthetic terrain, vegetation, building, steep-slope, and no-ground cases.
- Invalid thresholds, identical paths, failed PDAL pipeline, and unwritable output locations fail safely.
- A real-world sample is reviewed against independent ground truth.

Do not treat synthetic tests as evidence of general classification accuracy.
