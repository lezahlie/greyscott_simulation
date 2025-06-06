from setup_logger import setup_logger
logger = setup_logger(__file__, log_stdout=True, log_stderr=True)
from utilities import Any, Dict, List, Optional, Tuple, np, create_save_states_predicate
from greyscott_solvers import *
from greyscott_patterns import *
from visualize_dataset import *

###############################################################################
# Single simulation 
###############################################################################

def run_grayscott_simulation(
    seed:Optional[int] = None,
    *,
    grid_length: int = 64,
    max_iterations: int = 1000,
    patch_radius: int = 2,
    patch_prob: float = 0.5,
    save_states: Optional[Tuple[str, int]|Tuple[str]] = [("first", 20), ("interval", 10)],
) -> Dict[str, Any]:
    """Run a single Gray-Scott simulation given sim_config and a random seed

    Args:
        seed (Optional[int], optional): random seed. Defaults to None.
        grid_size (int): length of grid in pixels
        max_iterations (int, optional): maximum euler steps. Defaults to 1000.
        patch_radius (int): radius in pixels per patch
        patch_prob (float): probability a patch is placed or not
        save_states (Optional[Tuple[str, int] | Tuple[str]], optional): save states predicate config list. Defaults to [("first", 20), ("interval", 10)].

    Returns:
        Dict[str, Any]: 
            - 'meta': configuration and seed
            - 'image': contains u_init, v_init, optional v_frames, and u_final/v_final
    """
    rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng(seed)

    # Generate initial conditions
    u_init, v_init = create_initial_fields(
        grid_length,
        patch_radius,
        patch_prob,
        rng=rng
    )

    pattern, params = get_random_pattern(rng)   

    # Prepare to collect intermediate v-frames
    v_frames: Dict[str, np.ndarray] = {}
    u_frames: Dict[str, np.ndarray] = {}
    u, v = u_init.copy(), v_init.copy()

    save_states_predicate = create_save_states_predicate(save_states)

    for iteration in range(1,max_iterations+1):
        update_gray_scott(
            u,
            v,
            **params
        )

        if save_states_predicate(iteration):
            v_frames[f"v_state_{int(iteration)}"] = v.copy()
            u_frames[f"u_state_{int(iteration)}"] = u.copy()

    u_final, v_final = u.copy(), v.copy()

    meta: Dict[str, Any] = {
        'random_seed': seed,
        'grid_length': grid_length,
        'max_iterations': max_iterations,
        'total_iterations': iteration,
        'patch_radius': patch_radius,
        'patch_prob': patch_prob,
        'pattern_name': pattern,
        **params
    }

    images: Dict[str, Any] = {
        'u_state_initial': u_init,
        'u_state_final': u_final,
        **u_frames,
        'v_state_initial': v_init,
        'v_state_final': v_final,
        **v_frames
    }

    return {'image': images, 'meta': meta}

###############################################################################
# Generate batches
###############################################################################

def generate_grayscott_maps(
    min_seed: int,
    max_seed: int,
    *,
    grid_length: int,
    max_iterations: int,
    patch_radius: int,
    patch_prob: float,
    save_states: Optional[List]
) -> List[Dict[str, Any]]:
    """Run a batch of several Gray-Scott simulation given sim_config and a random seed

    Args:
        min_seed (int): minimum random seed (inclusive)
        max_seed (int): maximum random seed (inclusive)
        grid_size (int): length of grid in pixels
        max_iterations (int, optional): maximum euler steps. Defaults to 1000.
        patch_radius (int): radius in pixels per patch
        patch_prob (float): probability a patch is placed or not

    Returns:
        List[Dict[str, Any]]: List of simulation records
    """
    sim_config = {
        'grid_length': grid_length,
        'max_iterations': max_iterations,
        'patch_radius': patch_radius,
        'patch_prob': patch_prob,
        'save_states': save_states
    }

    results: List[Dict[str, Any]] = []
    for seed in range(min_seed, max_seed + 1):
        result = run_grayscott_simulation(seed, **sim_config)
        results.append(result)

    return results
