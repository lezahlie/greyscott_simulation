from utilities import Any, Dict, List, Optional, Tuple, np

###############################################################################
# Initial conditions
###############################################################################

MIN_COVERAGE_RATIO = 0.1
MIN_SPACING_FACTOR = 2.5

def _get_num_patches(grid_size: int, patch_radius: int, patch_prob: float, rng: np.random.Generator) -> int:
    assert 2 * patch_radius < grid_size, "Patch radius too large for grid"

    effective_diameter = MIN_COVERAGE_RATIO * patch_radius
    patches_per_row = int(grid_size // effective_diameter)
    max_possible_patches = patches_per_row ** 2
    max_possible_patches = patches_per_row ** 2

    proposed_patches = rng.binomial(max_possible_patches, patch_prob)

    patch_area = np.pi * patch_radius**2
    grid_area = grid_size**2
    max_allowed = int((MIN_COVERAGE_RATIO * grid_area) / patch_area)

    return max(1, min(proposed_patches, max_allowed))


def _sample_patch_centers(
    num_patches: int,
    grid_size: int,
    patch_radius: int,
    rng: np.random.Generator
) -> list[tuple[int,int]]:
    
    centers = []
    tries = 0
    max_tries = 10 * num_patches
    min_dist = (MIN_SPACING_FACTOR * patch_radius) ** 2
    euclid = lambda x1, y1, x2, y2: (x1 - x2)**2 + (y1 - y2)**2

    while len(centers) < num_patches and tries < max_tries:
        cx = int(rng.integers(patch_radius, grid_size - patch_radius))
        cy = int(rng.integers(patch_radius, grid_size - patch_radius))
        if all(euclid(cx, cy, x, y) >= min_dist for x, y in centers):
            centers.append((cx, cy))
        tries += 1

    return centers


def create_initial_fields(
    grid_size: int,
    patch_radius: int,
    patch_prob: float,
    rng: Optional[np.random.Generator] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Creates initial fields for concentrations U and V with *independent* patches.
    """
    if rng is None:
        rng = np.random.default_rng()

    # determine max patches
    num_patches = _get_num_patches(grid_size, patch_radius, patch_prob, rng)

    # start from uniform base
    conc_u = np.ones((grid_size, grid_size), dtype=np.float32)
    conc_v = np.zeros((grid_size, grid_size), dtype=np.float32)

    # sample centers for U and for V independently
    centers_u = _sample_patch_centers(num_patches, grid_size, patch_radius, rng)
    centers_v = _sample_patch_centers(num_patches, grid_size, patch_radius, rng)

    # helper grid for mask creation
    Y, X = np.ogrid[:grid_size, :grid_size]
    radius2 = patch_radius ** 2

    # apply U‐patches
    for cx, cy in centers_u:
        inner_u = rng.uniform(0.35, 0.85)
        mask = (X - cx)**2 + (Y - cy)**2 <= radius2
        conc_u[mask] = inner_u

    # apply V‐patches
    for cx, cy in centers_v:
        inner_v = rng.uniform(0.30, 0.60)
        mask = (X - cx)**2 + (Y - cy)**2 <= radius2
        conc_v[mask] = inner_v

    return conc_u, conc_v


def create_initial_fields_old(
    grid_size: int,
    patch_radius: int,
    patch_prob: float,
    rng: Optional[np.random.Generator] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """Creates initial fields for concentrations U and V

    Args:
        grid_size (int): length of grid in pixels
        patch_radius (int): radius in pixels per patch
        patch_prob (float): probability a patch is placed or not
        rng (Optional[np.random.Generator], optional): random number generator. Defaults to None.

    Returns:
        Tuple[np.ndarray, np.ndarray]: U_init, V_init
    """
    num_patches = _get_num_patches(grid_size, patch_radius, patch_prob, rng)

    conc_u = np.ones((grid_size, grid_size), dtype=np.float32)
    conc_v = np.zeros((grid_size, grid_size), dtype=np.float32)

    patch_centers = []
    tries = 0
    max_tries = 10 * num_patches

    euclid_dist = lambda x1, y1, x2, y2: (x1 - x2)**2 + (y1 - y2)**2
    min_dist = (MIN_SPACING_FACTOR * patch_radius)**2

    while len(patch_centers) < num_patches and tries < max_tries:
        cx = int(rng.integers(patch_radius, grid_size - patch_radius))
        cy = int(rng.integers(patch_radius, grid_size - patch_radius))

        if all(euclid_dist(cx, cy, x, y) >= min_dist for x, y in patch_centers):
            patch_centers.append((cx, cy))

            inner_u = rng.uniform(0.35, 0.85)
            inner_v = rng.uniform(0.3,  0.6) 

            Y, X = np.ogrid[:grid_size, :grid_size]
            dist2 = (X - cx)**2 + (Y - cy)**2
            circle_mask = dist2 <= patch_radius**2

            conc_u[circle_mask] = inner_u
            conc_v[circle_mask] = inner_v

        tries += 1

    return conc_u, conc_v


###############################################################################
# Boundary condition
###############################################################################
    
def compute_laplacian(field: np.ndarray) -> np.ndarray:
    """Return the 5‑point discrete Laplacian under periodic boundaries

    Args:
        field (np.ndarray): U or V field

    Returns:
        np.ndarray: U or V updated
    """

    return (
        -4.0 * field
        + np.roll(field, (0, -1), (0, 1))
        + np.roll(field, (0, 1), (0, 1))
        + np.roll(field, (-1, 0), (0, 1))
        + np.roll(field, (1, 0), (0, 1))
    )

###############################################################################
# Gray‑Scott update step
###############################################################################

def update_gray_scott(
    conc_u: np.ndarray,
    conc_v: np.ndarray,
    *,
    du: float,
    dv: float,
    feed: float,
    kill: float,
) -> None:
    """Advance the concentrations one Euler step in-place on U and V.

    Args:
        conc_u (np.ndarray): concentration U
        conc_v (np.ndarray): concentration V
        du (float): coefficient for U
        dv (float): coefficient for V
        feed (float): feed rate
        kill (float): kill rate
    """
    lap_u = compute_laplacian(conc_u)
    lap_v = compute_laplacian(conc_v)

    reaction = conc_u * (conc_v**2)     # u·v²

    conc_u += (du * lap_u               # D_u ∇²u
            - reaction                  # – u·v²
            + feed * (1.0 - conc_u))    # + F(1−u)

    conc_v += (dv * lap_v               # D_v ∇²v
            + reaction                  # + u·v²
            - (feed + kill) * conc_v)   # – (F+k)·v