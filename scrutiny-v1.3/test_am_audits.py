import subprocess
import sys
import os
import pytest

# AM-1 (Vulnerability Audit) has been removed.

# --- Rule AM-2: SBOM Generation ---
@pytest.mark.am_2
def test_am_2_sbom_generation():
    """
    (Rule AM-2) Generates a CycloneDX SBOM from requirements.txt.
    Fails if the 'cyclonedx' tool fails.
    """
    output_file = "sbom.json"
    if os.path.exists(output_file):
        os.remove(output_file)

    # *** THE DEFINITIVE FIX (Based on the tool's -h output) ***
    # 1. Module is 'cyclonedx_py'
    # 2. Subcommand is 'requirements'
    # 3. Options come *before* the positional <requirements-file>
    
    result = subprocess.run(
        [
            sys.executable,            # The path to the current python
            "-m", "cyclonedx_py",      # The correct base module
            "requirements",            # The correct subcommand
            "--output-format", "JSON", # The correct flag for format
            "--output-file", output_file, # The correct flag for output
            "requirements.txt"         # The positional argument at the end
        ],
        capture_output=True, text=True
    )

    # Assert the command succeeded and the file was created
    assert result.returncode == 0, f"cyclonedx failed:\n{result.stdout}\n{result.stderr}"
    assert os.path.exists(output_file), "SBOM file was not created"
    assert os.path.getsize(output_file) > 0, "SBOM file is empty"
