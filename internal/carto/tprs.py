"""
Thin-plate regression splines (TPRS) matching R's mgcv for 1D smooths.

Implements the Wood (2003) truncated eigen-decomposition approach for
bs="tp" with d=1, m=2, following mgcv's C implementation (tprs.c).

Used to fit: log(E[y]) = X_linear @ beta + f(z), y ~ Gamma(log).
"""

import numpy as np
from scipy import linalg, optimize


def tprs_basis(z, k):
    """
    Construct thin-plate regression spline basis and penalty matrix,
    matching mgcv's C implementation exactly.

    For 1D input (d=1), penalty order m=2:
    - Null space dimension M = 2 (intercept + linear)
    - TPS semi-kernel: eta(r) = r^3 / 12

    The algorithm (from mgcv's tprs_setup in tprs.c):
    1. Center z (subtract mean)
    2. Compute E using eta(r) = r^3/12
    3. Get top k eigenvectors/values of E via Lanczos-like iteration
    4. Form T = [1, z_centered], compute T'U
    5. QR decompose T'U, extract null space Z of T'U
    6. Design matrix: X = [U @ diag(v) @ Z, T]
    7. Penalty: S = Z' @ diag(v) @ Z with null space rows/cols zeroed
    8. Normalize each column of X to have RMS = 1

    Parameters
    ----------
    z : array of shape (n,)
        Covariate values.
    k : int
        Basis dimension (same as k in mgcv).

    Returns
    -------
    X_s : array of shape (n, k)
        TPRS basis matrix (columns normalized to RMS=1).
    S : array of shape (k, k)
        Penalty matrix (rescaled to match column normalization).
    z_shift : float
        The centering shift applied to z (= mean(z)).
    """
    z = np.asarray(z, dtype=float)
    n = len(z)
    M = 2  # null space dimension for d=1, m=2

    if k > n:
        k = n
    if k < M + 1:
        raise ValueError(f"k={k} must be >= {M + 1}")

    # Step 1: Center z (mgcv does this)
    z_shift = np.mean(z)
    z_c = z - z_shift

    # Step 2: TPS kernel matrix E (n x n) with eta(r) = r^3/12
    diffs = z_c[:, None] - z_c[None, :]
    E = np.abs(diffs) ** 3 / 12.0

    # Step 3: Get top k eigenvectors of E (by magnitude, like Lanczos)
    # mgcv uses Rlanczos with minus=-1 meaning "largest magnitude"
    eigenvalues_full, eigenvectors_full = np.linalg.eigh(E)
    # eigh gives ascending order. Take top k by magnitude.
    mag_order = np.argsort(np.abs(eigenvalues_full))[::-1]
    v = eigenvalues_full[mag_order[:k]]
    U = eigenvectors_full[:, mag_order[:k]]

    # Step 4: T = [1, z_centered] (null space basis)
    T = np.column_stack([np.ones(n), z_c])

    # Step 5: Compute T'U (M x k), then QR factorize
    # TU = T' @ U  (M x k)
    TU = T.T @ U  # M x k

    # QT factorization: TU @ Q = [0, B] where Q = [Z, Y]
    # Z is the null space of TU (k x (k-M))
    # This is equivalent to: QR of TU' gives Q=[Z|Y]
    # Actually mgcv's QT is: find Q such that TU @ Q = [0, B]
    # This means Q is the right null space basis of TU.
    # QR of TU.T: TU.T = Q_full @ R_full
    # The last (k-M) columns of Q_full form the null space of TU
    Q_tu, R_tu = np.linalg.qr(TU.T, mode="complete")
    # Z = first (k-M) columns of Q that correspond to null space
    # Actually: QR of TU' gives us Q such that TU' = Q @ R
    # TU = R' @ Q' => TU @ Q = R' which is upper triangular
    # The null space of TU corresponds to the zero rows of R'
    # i.e., columns of Q where R has zero diagonal
    # For TU (M x k) with rank M, the null space of TU has dim (k-M)
    # The last (k-M) columns of Q give the null space
    Z = Q_tu[:, M:]  # k x (k-M) null space of TU

    # Step 6: Form design matrix
    # Wiggly part: U @ diag(v) @ Z  (n x (k-M))
    UdvZ = (U * v[None, :]) @ Z  # n x (k-M)

    # Full basis: [wiggly, T]  but mgcv puts constant=1 so includes full T
    X_s = np.column_stack([UdvZ, T])  # n x k

    # Step 7: Penalty matrix
    # S = Z' @ diag(v) @ Z, with null space zeroed
    # Actually: S[i][i] = v[i] for i < k eigenvectors, then QT transform
    # From the C code: S starts as diag(v), then HQmult twice
    # S = Z' @ diag(v) @ Z for the wiggly part, zero for null space
    S_wiggle = Z.T @ np.diag(v) @ Z  # (k-M) x (k-M)
    S_full = np.zeros((k, k))
    S_full[:k - M, :k - M] = S_wiggle

    # Step 8: Normalize each column to have RMS = 1
    # (sum of squares = n, or equivalently norm = sqrt(n))
    col_rms = np.sqrt(np.sum(X_s ** 2, axis=0) / n)
    # Avoid division by zero for constant columns
    col_rms = np.maximum(col_rms, 1e-15)
    w = col_rms  # the scaling factors

    X_s = X_s / w[None, :]

    # Rescale S: S -> W @ S @ W where W = diag(1/w)
    # From C code: S[i][j] /= w for both row i and col j
    S_full = S_full / np.outer(w, w)

    # Also need to rescale UZ for predictions (not returned here but tracked)

    return X_s, S_full, z_shift


def _gamma_deviance(y, mu):
    """Gamma deviance: 2 * sum( (y-mu)/mu - log(y/mu) )."""
    r = y / mu
    return 2.0 * np.sum(r - 1 - np.log(r))


def _penalized_irls_at_lambda(X, S_full, y, lam, max_iter=50, tol=1e-7):
    """
    Penalized IRLS for Gamma(log) GLM at a given lambda.

    For Gamma with log link, working weights are identically 1.
    """
    n, p = X.shape
    ridge = 1e-8

    mu = y.copy().astype(float)
    mu = np.maximum(mu, 1e-6)

    dev_old = np.inf
    converged = False
    XtX = X.T @ X
    z_work = None

    for it in range(max_iter):
        eta = np.log(mu)
        z_work = eta + (y - mu) / mu

        A_mat = XtX + lam * S_full + ridge * np.eye(p)
        rhs = X.T @ z_work

        try:
            beta = linalg.solve(A_mat, rhs, assume_a="pos")
        except linalg.LinAlgError:
            beta = linalg.lstsq(A_mat, rhs)[0]

        eta_new = X @ beta
        mu = np.exp(eta_new)
        mu = np.maximum(mu, 1e-10)

        dev = _gamma_deviance(y, mu)
        if abs(dev - dev_old) / (abs(dev) + 0.1) < tol:
            converged = True
            break
        dev_old = dev

    P = XtX + lam * S_full + ridge * np.eye(p)
    try:
        P_inv = linalg.inv(P)
    except linalg.LinAlgError:
        P_inv = linalg.pinv(P)

    H = X @ P_inv @ X.T
    edf = np.trace(H)

    # Pearson scale estimate
    pearson_chi2 = np.sum(((y - mu) / mu) ** 2)
    phi = pearson_chi2 / max(n - edf, 1)

    # Working deviance (for REML criterion)
    residuals_w = z_work - X @ beta
    working_dev = np.sum(residuals_w ** 2)

    # Penalty contribution
    bSb = beta @ (lam * S_full) @ beta

    V_beta = P_inv * phi

    return {
        "beta": beta,
        "mu": mu,
        "deviance": dev,
        "edf": edf,
        "converged": converged,
        "V_beta": V_beta,
        "phi": phi,
        "P_inv": P_inv,
        "XtX": XtX,
        "working_dev": working_dev,
        "bSb": bSb,
    }


def _reml_criterion(log_lam, X, S_full, y, n_unpenalized, max_iter=50, tol=1e-7):
    """
    Laplace-approximate REML criterion for smoothing parameter selection.

    Based on the working model REML (Wood 2011):
    V_r = (working_dev + bSb) + (n-Mp)*log(2*pi*phi_w) + log|X'WX+lam*S| - log|lam*S|_+

    where phi_w = (working_dev + bSb) / (n - Mp) is the working REML scale.
    For Gamma(log), W = I.

    Profiling phi out:
    V_r ~ (n-Mp)*(1 + log(2*pi*(D_w+P)/(n-Mp))) + log|H| - log|lam*S|_+
    """
    lam = np.exp(log_lam)
    n, p = X.shape
    ridge = 1e-8

    result = _penalized_irls_at_lambda(X, S_full, y, lam, max_iter, tol)

    working_dev = result["working_dev"]
    bSb = result["bSb"]
    Mp = n_unpenalized

    # Profile REML scale
    phi_w = (working_dev + bSb) / max(n - Mp, 1)
    if phi_w <= 0 or not np.isfinite(phi_w):
        return 1e10

    P = result["XtX"] + lam * S_full + ridge * np.eye(p)
    try:
        sign, logdet_P = np.linalg.slogdet(P)
        if sign <= 0:
            return 1e10
    except np.linalg.LinAlgError:
        return 1e10

    evals_S = np.linalg.eigvalsh(lam * S_full)
    nonzero = evals_S[evals_S > 1e-10]
    logdet_S_plus = np.sum(np.log(nonzero)) if len(nonzero) > 0 else 0.0

    # REML criterion (to minimize)
    reml = (n - Mp) * np.log(2 * np.pi * phi_w) + (n - Mp) + logdet_P - logdet_S_plus

    return reml


def fit_gam_gamma_log(X_linear, z, y, k, max_iter=50, tol=1e-7, method="REML"):
    """
    Fit: log(E[y]) = X_linear @ beta_linear + f(z)

    where f(z) is a TPRS with basis dimension k,
    y ~ Gamma, link = log.

    Parameters
    ----------
    X_linear : array of shape (n, p)
        Linear predictor columns (e.g., just x = log(area)).
    z : array of shape (n,)
        Covariate for the smooth term.
    y : array of shape (n,)
        Response variable (must be positive).
    k : int
        Basis dimension for the smooth.
    max_iter : int
        Maximum IRLS iterations.
    tol : float
        Convergence tolerance.
    method : str
        "REML" or "GCV" for smoothing parameter selection.

    Returns
    -------
    dict with coefficients, se, linear_coef, linear_se, converged,
    lambda_opt, edf, deviance, phi.
    """
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    X_linear = np.atleast_2d(X_linear)
    if X_linear.ndim == 1:
        X_linear = X_linear.reshape(-1, 1)

    n = len(y)
    p_lin = X_linear.shape[1]

    # Build TPRS basis (matching mgcv's construction)
    X_s, S_s, z_shift = tprs_basis(z, k)

    # Full design matrix: [X_linear | X_smooth]
    X_full = np.column_stack([X_linear, X_s])
    p_full = X_full.shape[1]

    # Full penalty
    S_full = np.zeros((p_full, p_full))
    S_full[p_lin:, p_lin:] = S_s

    # Number of totally unpenalized parameters
    M_null = 2  # null space dim for d=1, m=2
    n_unpenalized = p_lin + M_null

    if method == "REML":
        # Coarse grid search
        log_lam_grid = np.linspace(-10, 15, 60)
        best_reml = np.inf
        best_log_lam = 0.0
        for ll in log_lam_grid:
            r = _reml_criterion(ll, X_full, S_full, y, n_unpenalized, max_iter, tol)
            if r < best_reml:
                best_reml = r
                best_log_lam = ll

        # Refine with scipy
        try:
            opt = optimize.minimize_scalar(
                _reml_criterion,
                bounds=(best_log_lam - 3, best_log_lam + 3),
                method="bounded",
                args=(X_full, S_full, y, n_unpenalized, max_iter, tol),
            )
            if opt.success and np.isfinite(opt.fun) and opt.fun < best_reml:
                best_log_lam = opt.x
        except Exception:
            pass

        lam_opt = np.exp(best_log_lam)
    else:
        # GCV
        log_lam_grid = np.linspace(-10, 15, 60)
        best_gcv = np.inf
        best_log_lam = 0.0
        for ll in log_lam_grid:
            lam = np.exp(ll)
            res = _penalized_irls_at_lambda(X_full, S_full, y, lam, max_iter, tol)
            gcv = n * res["deviance"] / max((n - res["edf"]) ** 2, 1)
            if gcv < best_gcv:
                best_gcv = gcv
                best_log_lam = ll

        fine = np.linspace(best_log_lam - 1, best_log_lam + 1, 40)
        for ll in fine:
            lam = np.exp(ll)
            res = _penalized_irls_at_lambda(X_full, S_full, y, lam, max_iter, tol)
            gcv = n * res["deviance"] / max((n - res["edf"]) ** 2, 1)
            if gcv < best_gcv:
                best_gcv = gcv
                best_log_lam = ll

        lam_opt = np.exp(best_log_lam)

    best_result = _penalized_irls_at_lambda(X_full, S_full, y, lam_opt, max_iter, tol)

    beta = best_result["beta"]
    V = best_result["V_beta"]
    se = np.sqrt(np.maximum(np.diag(V), 0))

    return {
        "coefficients": beta,
        "se": se,
        "linear_coef": beta[:p_lin],
        "linear_se": se[:p_lin],
        "converged": best_result["converged"],
        "lambda_opt": lam_opt,
        "edf": best_result["edf"],
        "deviance": best_result["deviance"],
        "phi": best_result["phi"],
    }
