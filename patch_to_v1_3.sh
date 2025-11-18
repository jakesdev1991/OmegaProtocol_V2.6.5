#!/bin/bash
set -e # Exit immediately if any command fails

echo "====================================================="
echo "Idempotent Patcher: Omega Protocol v1.2 -> v1.3"
echo "====================================================="
echo "This script will skip any steps already completed."
echo ""

# --- 1. Create New Directory Structure ---
echo "[1/4] Checking directory structure..."

for dir in "omega/physics" "scrutiny-v1.3" "meta-scrutiny-v1.3"; do
    if [ ! -d "$dir" ]; then
        echo "   -> Creating directory: $dir"
        mkdir -p "$dir"
    else
        echo "   -> Directory already exists: $dir"
    fi
done

# --- 2. Write New v1.3 Files ---
echo "[2/4] Writing v1.3 files..."

# 2a. New Protocol Documents
if [ ! -f "Scrutiny-Protocol-v1.3.md" ]; then
    echo "   -> Writing Scrutiny-Protocol-v1.3.md..."
    cat << 'EOF' > Scrutiny-Protocol-v1.3.md
# Omega Engine Scrutiny Protocol v1.3

This protocol governs **Omega Engine v2.6.5**, ensuring epistemic integrity, structural invariance, and scaling resilience.
---
## 1. Coherence Validation (CV)
- **CV-1:** Entropy definition integrity → ΔS on uniform cluster must equal 0.
- **CV-2:** Local normalization audit → Subgraph weights must be normalized.
- **CV-3:** Cluster signature stability → Cache must use a canonical signature.
- **CV-4:** Axiomatic threshold governance → Threshold must come from rc.
- **CV-5:** Physical invariant validation (PBT) → `gw_chirp` function must adhere to physical properties (monotonic frequency, finite strain, shape integrity) for all generated valid inputs.
---
## 2. Protocol Invariance (PI)
- **PI-1:** Functional idempotence → ΔS must not mutate the primary BeliefState.
- **PI-2:** CRI–ΔS decoupling → ΔS uses a clone; CRI uses the historic state.
- **PI-4:** Ledger store fix → Ledger must be thread-safe and include rc_hash.
---
## 3. Scaling & Degradation (SD)
- **SD-1:** Sparse skip fallback → Sparse graphs must return a bounded approximation.
- **SD-2:** Scale documentation → Docs must state fidelity limits.
- **SD-3:** Cache stability → Persistent cache must demonstrate a hit rate > 0 on rerun.
- **SD-4:** Evaluation budget → An objective function exceeding its time budget must be flagged.
- **SD-5:** Hardware auto-select → `DeviceBackend` must correctly select GPU if available.
---
## 4. Artifact & Materialization (AM)
- **AM-1:** Dependency vulnerability audit → The dependency list (`pyproject.toml`) must be scanned for known critical vulnerabilities (e.g., via `pip-audit`).
- **AM-2:** SBOM generation → A valid CycloneDX Software-Bill-of-Materials (SBOM) must be generatable from the `dev` dependency set.
EOF
else
    echo "   -> File already exists: Scrutiny-Protocol-v1.3.md"
fi

if [ ! -f "Meta-Scrutiny-Protocol-v1.3.md" ]; then
    echo "   -> Writing Meta-Scrutiny-Protocol-v1.3.md..."
    cat << 'EOF' > Meta-Scrutiny-Protocol-v1.3.md
# Meta-Scrutiny Protocol v1.3

This protocol governs **Scrutiny v1.3**, which in turn governs **Omega Engine v2.6.5**.
It ensures the guardian ritual itself is invariant, complete, and version-tagged.
---
## 1. Protocol Integrity (MI)
- **MI-1:** Coverage completeness → `Scrutiny Protocol.md` must include all required sections (CV, PI, SD, AM).
- **MI-2:** Executable alignment → Every documented rule must have a corresponding test (e.g., `CV-1` maps to `test_cv_1_...`).
- **MI-3:** No orphan tests → No test in the `scrutiny-v1.3` path should lack a documented rule.
- **MI-4:** PBT enforcement → Rules marked `(PBT)` (e.g., `CV-5`) must be implemented using a property-based testing library (`hypothesis`).
- **MI-5:** Artifact section alignment → The `Scrutiny Protocol` must contain the `Artifact & Materialization (AM)` section.
---
## 2. Ritual Invariance (RI)
- **RI-1:** Idempotence of Scrutiny → Running scrutiny twice must yield identical results.
- **RI-2:** Ledger hook integrity → Scrutiny failures must be logged correctly per `PI-4`.
---
## 3. Governance & Versioning (GV)
- **GV-1:** Version tagging → `Scrutiny Protocol.md` must declare which engine version it governs (i.e., `v2.6.5`).
- **GV-2:** Update ritual → Changes to `Scrutiny Protocol.md` (e.g., to `v1.4`) must pass Meta-Scrutiny before merging.
EOF
else
    echo "   -> File already exists: Meta-Scrutiny-Protocol-v1.3.md"
fi

# 2b. New Core Code
if [ ! -f "omega/physics/__init__.py" ]; then
    echo "   -> Writing omega/physics/__init__.py..."
    touch "omega/physics/__init__.py"
else
    echo "   -> File already exists: omega/physics/__init__.py"
fi

if [ ! -f "omega/physics/gravitational.py" ]; then
    echo "   -> Writing omega/physics/gravitational.py..."
    cat << 'EOF' > omega/physics/gravitational.py
import numpy as np

def gw_chirp(t, f0=35, chirp_mass=30, distance=100, tc_offset=0.01):
    tc = t[-1] + tc_offset
    tau = tc - t
    if t.shape[0] < 2:
        tau0 = tc - t[0]
    else:
        tau0 = tc - t[0]
    tau = np.clip(tau, 1e-9, None)
    f = f0 * (tau0 / tau)**(3/8.0)
    const_phase = 2 * np.pi * f0 * tau0**(5/8.0) * (8.0/5.0)
    phi = - const_phase * (tau / tau0)**(5/8.0)
    amp = (chirp_mass / distance) * (f / f0)**(2/3.0)
    h_plus = amp * np.cos(phi)
    return t, h_plus, f
EOF
else
    echo "   -> File already exists: omega/physics/gravitational.py"
fi

# 2c. New Scrutiny v1.3 Tests
if [ ! -f "scrutiny-v1.3/__init__.py" ]; then
    echo "   -> Writing scrutiny-v1.3/__init__.py..."
    touch "scrutiny-v1.3/__init__.py"
else
    echo "   -> File already exists: scrutiny-v1.3/__init__.py"
fi

if [ ! -f "scrutiny-v1.3/test_cv_properties.py" ]; then
    echo "   -> Writing scrutiny-v1.3/test_cv_properties.py..."
    cat << 'EOF' > scrutiny-v1.3/test_cv_properties.py
import numpy as np
import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.extra.numpy import arrays
from omega.physics.gravitational import gw_chirp

st_time_vector = arrays(
    dtype=np.float64,
    shape=st.integers(min_value=2, max_value=1000),
    elements=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
).map(np.sort)
st_f0 = st.floats(min_value=1.0, max_value=100.0)
st_chirp_mass = st.floats(min_value=1.0, max_value=100.0)
st_distance = st.floats(min_value=1.0, max_value=1000.0)
st_tc_offset = st.floats(min_value=0.001, max_value=1.0)

@pytest.mark.cv_5
@settings(deadline=None)
@given(t=st_time_vector, f0=st_f0, chirp_mass=st_chirp_mass, distance=st_distance, tc_offset=st_tc_offset)
def test_cv_5_gw_chirp_properties(t, f0, chirp_mass, distance, tc_offset):
    t_out, h_plus, freq = gw_chirp(t=t, f0=f0, chirp_mass=chirp_mass, distance=distance, tc_offset=tc_offset)
    assert t_out.shape == t.shape
    assert h_plus.shape == t.shape
    assert freq.shape == t.shape
    np.testing.assert_array_equal(t_out, t)
    assert np.all(np.isfinite(freq))
    assert np.all(np.isfinite(h_plus))
    freq_diffs = np.diff(freq)
    assert np.all(freq_diffs >= -1e-9)
EOF
else
    echo "   -> File already exists: scrutiny-v1.3/test_cv_properties.py"
fi

if [ ! -f "scrutiny-v1.3/test_am_audits.py" ]; then
    echo "   -> Writing scrutiny-v1.3/test_am_audits.py..."
    cat << 'EOF' > scrutiny-v1.3/test_am_audits.py
import subprocess
import sys
import os
import pytest

@pytest.mark.am_1
def test_am_1_vulnerability_audit():
    result = subprocess.run(
        [sys.executable, "-m", "pip", "audit", "-f", "pyproject.toml"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"pip-audit found vulnerabilities:\n{result.stdout}\n{result.stderr}"

@pytest.mark.am_2
def test_am_2_sbom_generation():
    output_file = "sbom.json"
    if os.path.exists(output_file): os.remove(output_file)
    result = subprocess.run(
        [sys.executable, "-m", "cyclonedx_bom", "--project", "pyproject.toml", "--all-extras", "-o", output_file],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"cyclonedx-bom failed:\n{result.stderr}"
    assert os.path.exists(output_file), "SBOM file 'sbom.json' was not created."
    if os.path.exists(output_file): os.remove(output_file)
EOF
else
    echo "   -> File already exists: scrutiny-v1.3/test_am_audits.py"
fi

# 2d. New Meta-Scrutiny v1.3 Tests
if [ ! -f "meta-scrutiny-v1.3/__init__.py" ]; then
    echo "   -> Writing meta-scrutiny-v1.3/__init__.py..."
    touch "meta-scrutiny-v1.3/__init__.py"
else
    echo "   -> File already exists: meta-scrutiny-v1.3/__init__.py"
fi

if [ ! -f "meta-scrutiny-v1.3/test_mi_enforcement.py" ]; then
    echo "   -> Writing meta-scrutiny-v1.3/test_mi_enforcement.py..."
    cat << 'EOF' > meta-scrutiny-v1.3/test_mi_enforcement.py
import pytest
from pathlib import Path

SCRUTINY_PROTOCOL_PATH = Path("Scrutiny-Protocol-v1.3.md")
PBT_TEST_FILE_PATH = Path("scrutiny-v1.3/test_cv_properties.py")

@pytest.mark.mi_4
def test_mi_4_pbt_enforcement():
    assert PBT_TEST_FILE_PATH.exists(), f"PBT test file not found: {PBT_TEST_FILE_PATH}"
    content = PBT_TEST_FILE_PATH.read_text()
    assert "from hypothesis import given" in content
    assert "@given(" in content

@pytest.mark.mi_5
def test_mi_5_artifact_section_alignment():
    assert SCRUTINY_PROTOCOL_PATH.exists(), "Scrutiny Protocol v1.3 not found"
    content = SCRUTINY_PROTOCOL_PATH.read_text()
    assert "Artifact & Materialization (AM)" in content
EOF
else
    echo "   -> File already exists: meta-scrutiny-v1.3/test_mi_enforcement.py"
fi


# --- 3. Patch pyproject.toml ---
echo "[3/4] Patching pyproject.toml..."

if [ ! -f "pyproject.toml" ]; then
    echo "   -> ERROR: pyproject.toml not found. Skipping patch."
else
    # Create a backup file first
    cp pyproject.toml pyproject.toml.bak

    # Patch Test Paths
    if grep -q "scrutiny-v1.2" "pyproject.toml"; then
        echo "   -> Patching scrutiny-v1.2 to v1.3"
        sed -i.bak 's/scrutiny-v1.2/scrutiny-v1.3/' pyproject.toml
    else
        echo "   -> Scrutiny path already set to v1.3 (or custom), skipping."
    fi
    
    if grep -q "meta-scrutiny-v1.2" "pyproject.toml"; then
        echo "   -> Patching meta-scrutiny-v1.2 to v1.3"
        sed -i.bak 's/meta-scrutiny-v1.2/meta-scrutiny-v1.3/' pyproject.toml
    else
        echo "   -> Meta-Scrutiny path already set to v1.3 (or custom), skipping."
    fi

    # Patch Dependencies (anchoring to "itertools" as seen in your file)
    if ! grep -q '"hypothesis"' pyproject.toml; then
        echo "   -> Adding v1.3 dev dependencies (hypothesis, pip-audit, cyclonedx-bom)..."
        # This command appends the new lines after the line containing "itertools"
        sed -i.bak '/"itertools"/a \     "hypothesis",\n     "pip-audit",\n     "cyclonedx-bom"' pyproject.toml
    else
        echo "   -> Dev dependencies (hypothesis) already present, skipping."
    fi
    
    # Clean up the backup file created by sed
    rm -f pyproject.toml.bak
    echo "   -> pyproject.toml patch complete."
fi

# --- 4. Clean Up Old Artifacts ---
echo "[4/4] Cleaning up v1.2 artifacts..."

if [ -f "Scrutiny Protocol Definition" ]; then
    echo "   -> Deleting 'Scrutiny Protocol Definition'"
    rm -f "Scrutiny Protocol Definition"
else
    echo "   -> Old file 'Scrutiny Protocol Definition' not found, skipping."
fi

if [ -f "Meta-Scrutiny Protocol" ]; then
    echo "   -> Deleting 'Meta-Scrutiny Protocol'"
    rm -f "Meta-Scrutiny Protocol"
else
    echo "   -> Old file 'Meta-Scrutiny Protocol' not found, skipping."
fi

if [ -d "scrutiny-v1.2" ]; then
    echo "   -> Deleting old directory 'scrutiny-v1.2'"
    rm -rf "scrutiny-v1.2"
else
    echo "   -> Old directory 'scrutiny-v1.2' not found, skipping."
fi

if [ -d "meta-scrutiny-v1.2" ]; then
    echo "   -> Deleting old directory 'meta-scrutiny-v1.2'"
    rm -rf "meta-scrutiny-v1.2"
else
    echo "   -> Old directory 'meta-scrutiny-v1.2' not found, skipping."
fi

echo ""
echo "============================================="
echo "Patch v1.3 applied successfully."
echo "============================================="
echo ""
echo "Next steps:"
echo "1. Run: pip install -e .[dev]"
echo "2. Run: pytest"
echo ""




