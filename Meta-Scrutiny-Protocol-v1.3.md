Meta-Scrutiny Protocol v1.3
​This protocol governs Scrutiny v1.3, which in turn governs Omega Engine v2.3.
It ensures the guardian ritual itself is invariant, complete, and version-tagged.
​1. Protocol Integrity (MI)
​MI-1: Coverage completeness → Scrutiny protocol.md must include all sections (CV, PI, SD, AM).
​MI-2: Executable alignment → Every documented rule (e.g., "CV-1", "AM-2") must have a corresponding, discoverable pytest test.
​MI-3: No orphan tests → No test should lack a documented rule.
​MI-4: PBT enforcement → Rules designated as "Property-Based" (like CV-5) must be implemented using the @given decorator.
​MI-5: Artifact section check → Scrutiny protocol must contain all 4 rule sections: CV, PI, SD, and AM.
​2. Ritual Invariance (RI)
​RI-1: Idempotence of Scrutiny → Running scrutiny twice must yield identical results (e.g., SBOM content).
​RI-2: Ledger hook integrity → Scrutiny failures must be logged correctly.
​3. Governance & Versioning (GV)
​GV-1: Version tagging → Scrutiny protocol file must declare that it governs "Omega Engine v2.3".
​GV-2: Update ritual → Changes to Scrutiny must pass Meta-Scrutiny.
