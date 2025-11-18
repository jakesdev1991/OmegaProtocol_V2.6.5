Omega Engine Scrutiny Protocol v1.3
​This protocol governs Omega Engine v2.3, ensuring epistemic integrity, structural invariance,
and scaling resilience. This version (1.3) formalizes property-based testing and
supply-chain artifact generation.
​1. Coherence Validation (CV)
​CV-1: Entropy definition integrity → ΔS on uniform cluster must equal 0.
​CV-2: Local normalization audit → Subgraph weights must be normalized.
​CV-3: Cluster signature stability → Cache must use a canonical signature.
​CV-4: Axiomatic threshold governance → Threshold must come from rc.
​CV-5: Gravitational waveform physical invariants → (Property-Based Test) The gw_chirp function must adhere to physical properties for all valid inputs:
​Frequency must be positive and monotonically increasing.
​Output strain h_plus must be finite.
​Output array shapes must match the input time vector shape.
​2. Protocol Invariance (PI)
​PI-1: Functional idempotence → ΔS must not mutate the primary BeliefState.
​PI-2: CRI–ΔS decoupling → ΔS uses a clone; CRI uses the historic state.
​PI-4: Ledger store fix → Ledger must be thread-safe and include rc_hash.
​3. Scaling & Degradation (SD)
​SD-1: Sparse skip fallback → Sparse graphs must return a bounded approximation.
​SD-2: Scale documentation → Docs must state fidelity limits.
​SD-3: Cache stability → Persistent cache must demonstrate a hit rate > 0 on rerun.
​SD-4: Evaluation budget → An objective function exceeding its time budget must be flagged.
​SD-5: Hardware auto-select → DeviceBackend must correctly select GPU if available.
​4. Artifact & Metrology (AM)
​AM-2: SBOM generation → A CycloneDX SBOM must be generated on every scrutiny pass.
