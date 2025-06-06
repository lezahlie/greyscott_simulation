import pytest

from setup_logger import setup_logger
logger = setup_logger(__file__, log_stdout=True, log_stderr=True)
from greyscott_patterns import *
from greyscott_solvers import *
from visualize_dataset import *
from utilities import *

def simulate_patterns(
    seed:Optional[int] = None,
    *,
    grid_length: int = 64,
    max_iterations: int = 1000,
    patch_radius: int = 4,
    patch_prob: float = 0.5,
    save_states: Optional[Tuple[str, int]|Tuple[str]] = [("first", 20), ("interval", 100)],
) -> Dict[str, Any]:
    rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng(seed)
    save_states_predicate = create_save_states_predicate(save_states)

    pattern_records = []
    for pattern, params in GREY_SCOTT_PATTERNS.items():
        # Generate initial conditions
        u_init, v_init = create_initial_fields(
            grid_length,
            patch_radius,
            patch_prob,
            rng=rng
        )

        # Prepare to collect intermediate v-frames
        v_frames: Dict[str, np.ndarray] = {}
        u_frames: Dict[str, np.ndarray] = {}
        u, v = u_init.copy(), v_init.copy()

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

        result = {
            'image': {
                'u_state_initial': u_init,
                'u_state_final': u_final,
                **u_frames,
                'v_state_initial': v_init,
                'v_state_final': v_final,
                **v_frames
            },
            'meta': {
                'random_seed': seed,
                'grid_length': grid_length,
                'max_iterations': max_iterations,
                'total_iterations': iteration,
                'patch_radius': patch_radius,
                'patch_prob': patch_prob,
                'pattern_name': pattern,
                **params
            }
        }

        pattern_records.append(result)
        logger.info(f"Test complete: seed = {seed}, pattern = {pattern}")

    return pattern_records

def visualize_patterns(record, output_path):
    meta_data = record['meta']

    pattern = meta_data['pattern_name']
    seed = meta_data['random_seed']

    title = f"{pattern.title().replace('_',' ')} — Seed #{seed}"
    file_prefix = f"{DATATYPE_NAME}_{pattern}_{seed}"

    file_paths = []
    for prefix, label in zip(['u', 'v'], ['substrate', 'activator']):
        frames, steps = extract_record_frames(record, prefix=prefix)
        gif_path = os_path.join(output_path,  f"{file_prefix}_{label}_{prefix}.gif")
        gif_title = rf"{label.title()} ${prefix.upper()}_t$: {title}"

        save_record_frames(frames, 
                            steps, 
                            fps=15, 
                            delay=3, 
                            cmap="turbo", 
                            title=gif_title, 
                            file_path=gif_path)
        logger.info(f"Saved test {label} {prefix} gif → {gif_path}")
        file_paths.append(str(gif_path))

    image_path = os_path.join(output_path,  f"{file_prefix}_activator_versus_substrate.png")

    save_record_images(
        record,
        cmap="seismic",
        title=title,
        file_path=image_path
    )
    file_paths.append(image_path)

    logger.info(f"Saved test image → {image_path}")
    return file_paths

@pytest.mark.parametrize("seed", [20, 42])
@pytest.mark.parametrize("samples", [1, None])
def test_all_patterns(seed, samples):
    sim_args = {
        'grid_length': 64,
        'max_iterations': 2000,
        'patch_radius': 2,
        'patch_prob': 0.5,
        'save_states': [("first", 20), ("interval", 20)]
    }
    
    output_folder = create_folder("test_results")
    dataset_file = os_path.join(output_folder, f"{DATATYPE_NAME}_test_results.hdf5")
    logger.info(f"Running Grey-Scott pattern test with seed={seed}")

    result_records = simulate_patterns(seed, **sim_args)
    assert len(result_records) > 0, "No patterns were simulated"

    logger.info(f"Saving {len(result_records)} simulations to: {dataset_file}")
    save_to_hdf5(result_records, dataset_file)
    with h5py.File(dataset_file, "r") as h5f:
        logger.info(f"HDF5 contains {len(h5f.keys())} records")
        assert len(h5f.keys()) >= len(GREY_SCOTT_PATTERNS), "Not all patterns were saved"

    sample_records = read_from_hdf5(dataset_file, sample_size=samples, flatten=False, random_seed=seed)
    logger.info(f"Visualizing {len(sample_records)} sampled records")
    for record in sample_records:
        file_paths = visualize_patterns(record, output_folder)
        for fp in file_paths:
            assert os_path.exists(fp), f"Cannot find file path '{fp}'"