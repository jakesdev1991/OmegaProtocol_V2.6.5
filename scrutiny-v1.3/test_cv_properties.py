import numpy as np
import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.extra.numpy import arrays

# --- Import our target function ---
from omega.physics.gravitational import gw_chirp

# ----------------------------------------------------------------------
# 1. DEFINE THE "STRATEGIES"
# ----------------------------------------------------------------------
st_time_vector = arrays(
    dtype=np.float64,
    shape=st.integers(min_value=2, max_value=2000),
    elements=st.floats(
        min_value=0.0,
        max_value=100.0,
        allow_nan=False,
        allow_infinity=False
    )
).map(np.sort)

# *** FIX: These lines are now at the correct (zero) indentation level ***
st_f0 = st.floats(
    min_value=1.0,
    max_value=100.0,
    allow_nan=False,
    allow_infinity=False
)
st_chirp_mass = st.floats(
    min_value=1.0,
    max_value=100.0,
    allow_nan=False,
    allow_infinity=False
)
st_distance = st.floats(
    min_value=1.0,
    max_value=1000.0,
    allow_nan=False,
    allow_infinity=False
)
st_tc_offset = st.floats(
    min_value=0.001,
    max_value=1.0,
    allow_nan=False,
    allow_infinity=False
)

# ----------------------------------------------------------------------
# 2. WRITE THE TEST USING @given
# ----------------------------------------------------------------------

@given(
    t=st_time_vector,
    f0=st_f0,
    chirp_mass=st_chirp_mass,
    distance=st_distance,
    tc_offset=st_tc_offset
)
@pytest.mark.cv_5
@settings(max_examples=100, deadline=None) # Standard hypothesis settings
def test_cv_5_gw_chirp_properties(t, f0, chirp_mass, distance, tc_offset):
    """
    (Rule CV-5) This test scrutinizes the *physical properties*
    of the gw_chirp output.
    """
    t_out, h_plus, freq = gw_chirp(
        t=t,
        f0=f0,
        chirp_mass=chirp_mass,
        distance=distance,
        tc_offset=tc_offset
    )

    # --- Property 1: Output Shape Integrity ---
    assert t_out.shape == t.shape
    assert h_plus.shape == t.shape
    assert freq.shape == t.shape

    # --- Property 2: Time Vector Integrity ---
    np.testing.assert_array_equal(t_out, t)

    # --- Property 3: Physicality (Frequency) ---
    assert np.all(freq > 0)
    assert np.all(np.isfinite(freq))

    # --- Property 4: Physicality (Amplitude) ---
    assert np.all(np.isfinite(h_plus))

    # --- Property 5: The "Chirp" Property (Monotonicity) ---
    freq_diffs = np.diff(freq)
    assert np.all(freq_diffs >= -1e-9)
