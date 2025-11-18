# FILE: omega/analysis.py
"""
This module contains the "secret sauce" of the Omega Protocol.
It analyzes a completed run history (a "ledger" of trials)
to derive the fundamental physics metrics (COD and CRI)
based on the "ToE-V.Omega.3.3" framework.
"""
from __future__ import annotations
import numpy as np
import logging
from typing import List, TYPE_CHECKING

# This trick avoids a circular import, but still
# gives us type-hinting for the Trial object.
if TYPE_CHECKING:
    from .universal import Trial

logger = logging.getLogger("omega_analysis")

# ==========================================================
# 1. Chain Overlap Density (COD)
# ==========================================================

def calculate_cod(trials: List[Trial]) -> float:
    """
    Calculates the real Chain Overlap Density (COD) based on
    [span_0](start_span)[span_1](start_span)"ToE-V.Omega.3.3", Section 1.2[span_0](end_span)[span_1](end_span).

    This implements the formula:
        phi(Q) = [Sum(Marginal Entropies) - Joint Entropy] / N
    
    We use a classical, Gaussian proxy for entropy, where:
        S(X) ≈ 0.5 * log( (2pi*e)^k * det(Cov(X)) )
    
    This measures the *average mutual information* shared
    between the hyperparameters across the search space.
    """
    logger.info("Calculating real COD (Mutual Information)...")
    
    # Get all normalized parameters from completed trials
    params_norm = np.array([
        t.params_norm for t in trials 
        if t.status == "COMPLETED" and t.best_loss < np.inf
    ])
    
    if params_norm.shape[0] < 2:
        logger.warning("Not enough data to calculate COD.")
        return 0.0

    n_trials, n_dims = params_norm.shape

    # 1. Calculate Joint Entropy: S(ρ_Q)
    # We need to add a tiny amount of noise for numerical stability
    # in case a parameter column is constant.
    noise = 1e-10 * np.random.randn(*params_norm.shape)
    params_norm += noise
    
    try:
        cov_matrix = np.cov(params_norm, rowvar=False)
        # Ensure matrix is positive semi-definite
        cov_matrix = cov_matrix + np.eye(n_dims) * 1e-9
        
        sign, logdet = np.linalg.slogdet(cov_matrix)
        if sign <= 0:
            raise np.linalg.LinAlgError("Covariance determinant is non-positive.")
            
        # S(X) = 0.5 * log( (2pi*e)^k * det(Cov(X)) )
        # We can ignore the (2pi*e)^k constant as it cancels
        # in the final mutual information calculation.
        joint_entropy = 0.5 * logdet
        
    except np.linalg.LinAlgError as e:
        logger.warning(f"Failed to calculate joint entropy: {e}")
        return 0.0

    # 2. Calculate Sum of Marginal Entropies: Σₖ S(ρₖ)
    # This is the entropy of each *column* (hyperparameter)
    # calculated independently.
    marginal_variances = np.diag(cov_matrix)
    
    # S(X_i) = 0.5 * log( 2pi*e * Var(X_i) )
    # Again, we ignore the constant.
    sum_marginal_entropies = 0.5 * np.sum(np.log(marginal_variances))

    # 3. Calculate Mutual Information (the numerator)
    # I = Σ S(ρₖ) - S(ρ_Q)
    mutual_information = sum_marginal_entropies - joint_entropy

    if mutual_information < 0:
        # This can happen due to numerical instability
        mutual_information = 0.0

    # 4. Calculate COD (the average mutual information)
    # φ(Q) = I / |Q|
    # Here we average over dimensions, not trials
    cod_score = mutual_information / n_dims
    
    # Clamp to a reasonable range
    return float(np.clip(cod_score, 0.0, 1.0))

# ==========================================================
# 2. Causal Rate of Influence (CRI)
# ==========================================================

def calculate_cri(trials: List[Trial]) -> float:
    """
    Calculates the real Causal Rate of Influence (CRI) based on
    [span_2](start_span)"ToE-V.Omega.3.3", Section 4[span_2](end_span) and "Emergent Reality...",
    [span_3](start_span)Section 3[span_3](end_span).

    This implements the concept:
        Rate = d(state) / d(perspective)
    
    We proxy this by fitting a linear model to the search space:
        loss ≈ (m_1 * p_1) + ... + (m_k * p_k) + b
        
    The "CRI" is the magnitude of the gradient vector 'm',
    which represents the average "Activity" or "Rate of Influence"
    of the parameters on the final loss.
    """
    logger.info("Calculating real CRI (Global Gradient)...")

    # Get all normalized parameters and losses
    params_norm = []
    losses = []
    for t in trials:
        if t.status == "COMPLETED" and t.best_loss < np.inf:
            params_norm.append(t.params_norm)
            losses.append(t.best_loss)

    if len(losses) < 2 or len(params_norm) == 0:
        logger.warning("Not enough data to calculate CRI.")
        return 0.0

    P = np.array(params_norm)
    L = np.array(losses)

    # We want to solve the linear system L = P*w + b
    # Add a column of ones for the bias 'b'
    A = np.hstack([P, np.ones((P.shape[0], 1))])
    
    try:
        # Use least-squares to find the best-fit gradient vector 'w'
        # [0] gives the solution vector [w_1, ..., w_k, b]
        gradient_vector = np.linalg.lstsq(A, L, rcond=None)[0]
        
        # We only care about the parameter weights, not the bias 'b'
        gradient_vector = gradient_vector[:-1]
        
        # The CRI is the magnitude (L2 norm) of this global gradient
        cri_score = np.linalg.norm(gradient_vector)
        
        return float(cri_score)
        
    except np.linalg.LinAlgError as e:
        logger.warning(f"Failed to calculate CRI (least-squares failed): {e}")
        return 0.0
