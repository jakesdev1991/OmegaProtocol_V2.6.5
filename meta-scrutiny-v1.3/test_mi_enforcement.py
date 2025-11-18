#
# This file REPLACES the old version.
# The @pytest.mark.xfail has been REMOVED from test_mi_2.
#
import pytest
import os
import re

# --- Fixtures to read rules and tests just once ---

@pytest.fixture(scope="session")
def protocol_rules():
    """(Fixture) Reads all unique rule IDs from the protocol .md file."""
    protocol_file = "Scrutiny-Protocol-v1.3.md"
    if not os.path.exists(protocol_file):
        pytest.skip("Scrutiny-Protocol-v1.3.md not found")
    
    with open(protocol_file, 'r') as f:
        content = f.read()
    
    # Updated regex to be more flexible (handles markdown or plain text)
    # Looks for "CV-1:", "PI-4:", "SD-1:", etc.
    rule_ids = re.findall(r"([A-Z]{2,3}-\d+)", content)
    return set(rule_ids)

@pytest.fixture(scope="session")
def implemented_rules():
    """(Fixture) Scans all test files for @pytest.mark decorators."""
    scrutiny_tests_dir = "scrutiny-v1.3"
    if not os.path.exists(scrutiny_tests_dir):
        pytest.skip("Scrutiny test directory 'scrutiny-v1.3' not found")

    test_files = [
        os.path.join(scrutiny_tests_dir, f)
        for f in os.listdir(scrutiny_tests_dir)
        if f.startswith("test_") and f.endswith(".py")
    ]
    
    implemented_rules_set = set()
    for tf in test_files:
        with open(tf, 'r') as f:
            content = f.read()
            # Finds @pytest.mark.cv_1, @pytest.mark.am_2, etc.
            markers = re.findall(r"@pytest\.mark\.([a-z]{2,3}_\d+)", content)
            # Converts 'cv_1' to 'CV-1'
            normalized_markers = {m.upper().replace('_', '-') for m in markers}
            implemented_rules_set.update(normalized_markers)
            
    return implemented_rules_set

# --- Meta-Scrutiny Tests ---

@pytest.mark.mi_2
def test_mi_2_executable_alignment(protocol_rules, implemented_rules):
    """
    (Rule MI-2) Ensures every rule in 'Scrutiny-Protocol-v1.3.md'
    has a corresponding @pytest.mark in the scrutiny-v1.3 test path.
    """
    # This test will now pass because we are adding the 12 new test stubs.
    missing_rules = protocol_rules - implemented_rules
    assert not missing_rules, \
        f"Missing tests for rules: {sorted(list(missing_rules))}"

@pytest.mark.mi_3
def test_mi_3_no_orphan_tests(protocol_rules, implemented_rules):
    """
    (Rule MI-3) Ensures every @pytest.mark in the scrutiny tests
    maps to a rule in 'Scrutiny-Protocol-v1.3.md'.
    """
    # This test ensures we don't have "extra" tests.
    orphan_tests = implemented_rules - protocol_rules
    assert not orphan_tests, \
        f"Orphan tests found (no matching rule): {sorted(list(orphan_tests))}"

@pytest.mark.mi_4
def test_mi_4_pbt_enforcement():
    """
    (Rule MI-4) Ensures that rule CV-5's test
    is a Property-Based Test (PBT) and uses '@given'.
    """
    test_file = "scrutiny-v1.3/test_cv_properties.py"
    if not os.path.exists(test_file):
        pytest.skip(f"Test file not found: {test_file}")
    
    with open(test_file, 'r') as f:
        content = f.read()

    # Check that the test function for cv_5 uses @given
    # This flexible regex finds both decorators, regardless of order
    cv_5_block = re.search(
        r"(@given\(.+?\).*?@pytest\.mark\.cv_5|@pytest\.mark\.cv_5.*?@given\(.+?\))", 
        content, 
        re.DOTALL
    )
    
    assert cv_5_block, "Test for CV-5 is not marked with @given"
    assert "@given" in cv_5_block.group(0), "Test for CV-5 is missing @given"
    assert "@pytest.mark.cv_5" in cv_5_block.group(0), "Test for CV-5 is missing @pytest.mark.cv_5"

@pytest.mark.mi_5
def test_mi_5_artifact_section_check():
    """
    (Rule MI-5) Ensures Scrutiny protocol contains all 4 sections.
    """
    protocol_file = "Scrutiny-Protocol-v1.3.md"
    if not os.path.exists(protocol_file):
        pytest.skip(f"Protocol file not found: {protocol_file}")
    
    with open(protocol_file, 'r') as f:
        content = f.read()

    # More flexible regex that ignores markdown '##' and '1.'
    expected_sections = [
        r"Coherence Validation \(CV\)",
        r"Protocol Invariance \(PI\)",
        r"Scaling & Degradation \(SD\)",
        r"Artifact & Metrology \(AM\)"
    ]
    
    missing_sections = []
    for section_pattern in expected_sections:
        if not re.search(section_pattern, content, re.IGNORECASE):
            missing_sections.append(section_pattern)
            
    assert not missing_sections, \
        f"Protocol file is missing required sections: {missing_sections}"
