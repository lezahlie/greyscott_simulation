from setup_logger import setup_logger, set_logger_level
logger = setup_logger(__file__, log_stdout=True, log_stderr=True)
from utilities import (DATATYPE_NAME, DEFAULT_DATAFILE_EXT, 
                        Any, Dict, List, Optional, Tuple, 
                        os_path, np, re, plt, animate, 
                        read_from_hdf5, read_from_json, create_folder, create_file_path)
from arguments import process_args

DEFAULT_FPS = 20
DEFAULT_DELAY = 3

def extract_record_frames(record) -> np.ndarray:
    """
    Given an h5py Group record with a /image/ and /meta/ subgroup,
    extract all V state frames in chronological order.

    Returns:
        A NumPy array of shape (N, H, W).

    Raises:
        KeyError if no V-frame data is found.
    """
    image_dict = record.get("image", {})
    meta_dict = record.get("meta", {})

    # pattern for "v_state_initial", "v_state_<step>", "v_state_final"
    pattern = re.compile(r"v_state_(\d+)$")
    initial_image_key = "v_state_initial"
    final_image_key = "v_state_final"
    iteration_meta_key = "total_iterations"

    if initial_image_key not in image_dict:
        raise KeyError(f"Missing '{initial_image_key}' in image group")
    elif final_image_key not in image_dict:
        raise KeyError(f"Missing '{final_image_key}' in image group")
    elif iteration_meta_key not in meta_dict:
        raise KeyError(f"Missing '{iteration_meta_key}' in meta group")

    total_iterations = meta_dict[iteration_meta_key]

    # validate initial frame (step = 0)
    initial_state = image_dict[initial_image_key][()]
    if not isinstance(initial_state, np.ndarray) or initial_state.ndim != 2:
        raise ValueError("'v_state_initial' must be a 2D NumPy array")

    #validate final frame (step = final)
    final_state = image_dict[final_image_key][()]
    if not isinstance(final_state, np.ndarray) or final_state.ndim != 2:
        raise ValueError("'v_state_final' must be a 2D NumPy array")

    # get intermediate frames and iterations
    states: List[Tuple[int, np.ndarray]] = []
    for key in image_dict.keys():
        m = pattern.match(key)
        if m:
            step = int(m.group(1))
            arr = image_dict[key][()]
            if not isinstance(arr, np.ndarray) or arr.ndim != 2:
                raise ValueError(f"'{key}' must be a 2D NumPy array")
            states.append((step, arr))

    # sort intermediate by iterations
    states.sort(key=lambda x: x[0])

    # build lists for frames and iterations
    steps: List[int] = []
    frames: List[np.ndarray] = []

    # initial (step = 0)
    steps.append(0)
    frames.append(initial_state)

    # intermediate
    for s, arr in states:
        steps.append(s)
        frames.append(arr)

    # final (step = total_iterations)
    steps.append(total_iterations)
    frames.append(final_state)

    # stack all frames into a single 3D array
    frames_stack = np.stack(frames, axis=0)  # shape: (num_frames, N, N)

    return frames_stack, steps


def save_record_frames(
    record: dict,
    *,
    file_path: str,
    fps: int = DEFAULT_FPS,
    delay: int = DEFAULT_DELAY,
    cmap: str = "turbo",
    title: str = "Grey-Scott Simulation",
    
) -> None:
    """
    Create and save a GIF from a sequence of 2D frames.
    
    Args:
        frames:    np.ndarray of shape (N, H, W).
        steps:     List of length num_frames; steps[i] is the “step index” for frames[i].
        file_path:  Path or filename where the GIF will be written.
        fps:       Playback frames per second (default: 20).
        cmap:      Matplotlib colormap (default: "turbo").
        title:     Main title for the GIF (default: "Grey-Scott Simulation").
        figsize:   Size of each frame in inches as (height, width), [default: (10, 10)].

    Raises:
        ValueError: If `frames` is not 3D.
    """

    frames, steps = extract_record_frames(record)

    if frames.ndim != 3:
        raise ValueError("frames must be a 3D array of shape (N, H, W)")

    N, H, W = frames.shape

    hold_count = int(round(delay * fps))
    frame_indices = list(range(N)) + [N - 1] * hold_count
    total_frames = len(frame_indices)
    
    fig, ax = plt.subplots(figsize=(8, 8))

    img = ax.imshow(
        frames[0],
        cmap=cmap,
        vmin=0.0,
        vmax=1.0
    )
    title_text = ax.set_xlabel(f"t = {steps[0]}", fontsize=16, labelpad=20)

    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.suptitle(title, fontsize=18)
    fig.tight_layout()
    
    def _render(i: int):
        idx = frame_indices[i]
        img.set_data(frames[idx])
        title_text.set_text(f"t = {steps[idx]}")
        return (img, title_text)

    fps2ms = 1000 / fps
    anim = animate.FuncAnimation(
        fig,
        _render,
        frames= total_frames,
        interval= fps2ms,
        repeat=True,
        blit=True
    )

    writer = animate.PillowWriter(fps=fps, metadata={"loop": 0})
    anim.save(file_path, dpi=H, writer=writer)

    plt.close(fig)


def save_record_images(
    record: dict,
    *,
    file_path: str,
    cmap:str = "seismic",
    title:str = "Grey-Scott Simulation",
    statistics:Optional[dict]=None
) -> None:
    """
    Create and save a GIF from a sequence of 2D frames.
    
    Args:
        record:     Record of simulation run from hdf5 dataset
        file_path:  Path or filename where the image will be saved.
        cmap:       Matplotlib colormap (default: "seismic").
        title:      Main title for the GIF (default: "Grey-Scott Simulation").
        statistics: Global statistics for each frame (default: None).
    """

    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    flat_axes = axes.flatten()
    image_dict = record['image']
    stats_dict = statistics.get('image', {}) if statistics else {}
    

    fields = [
        ("u_state_initial", "U: Initial State"),
        ("u_state_final", "U: Final State"),
        ("v_state_initial", "V: Initial State"),
        ("v_state_final", "V: Final State"),
    ]

    for idx, (img_key, img_label) in enumerate(fields):
        arr = image_dict[img_key]
        stats = stats_dict.get(img_key, {})
        ax = flat_axes[idx]

        im = ax.imshow(arr , vmin=stats.get('min', 0.0), vmax=stats.get('max', 1.0), cmap=cmap)
        ax.set_title(img_label, fontsize=12, pad=10)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        ax.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])

    fig.suptitle(title, fontsize=14)
    plt.tight_layout()
    fig.savefig(file_path)
    plt.close(fig)



def visualize_samples(args):
    if args.debug_on:
        set_logger_level(10)

    # all the possible args

    data_file = getattr(args, 'data_file') 
    output_folder = getattr(args, 'output_folder') 
    

    random_seed = getattr(args, 'random_seed') 
    num_samples = getattr(args, 'num_samples') 

    fps = getattr(args, 'gif_fps')
    delay = getattr(args, 'gif_delay')
    gif_cmap = getattr(args, 'gif_cmap')
    image_cmap = getattr(args, 'image_cmap')

    output_folder = create_folder(output_folder)

    data_filename = os_path.basename(data_file)
    json_filename = f"global_statistics_{DEFAULT_DATAFILE_EXT}_{data_filename.replace(DEFAULT_DATAFILE_EXT, 'json')}"
    json_file = data_file.replace(data_filename, json_filename)

    global_statistics = read_from_json(json_file)
    sample_records = read_from_hdf5(data_file, sample_size=num_samples, flatten=False, random_seed=random_seed)

    for record in sample_records:

        meta_dict = record['meta']

        pattern = meta_dict['pattern_name']
        seed = meta_dict['random_seed']
        iterations = meta_dict['total_iterations']

        title = f"Pattern: {pattern.title().replace('_',' ')} — Seed #{seed} — {iterations} Steps"

        gif_path = os_path.join(output_folder,  f"{DATATYPE_NAME}_{pattern}_{seed}.gif")
        save_record_frames(record, fps=fps, delay=delay, title=title, cmap=gif_cmap, file_path=gif_path)
        logger.info(f"Saved test gif → {gif_path}")

        image_path = os_path.join(output_folder,  f"{DATATYPE_NAME}_{pattern}_{seed}.png")
        save_record_images(record, statistics=global_statistics, title=title, cmap=image_cmap, file_path=image_path)
        logger.info(f"Saved test images → {image_path}")



if __name__ == "__main__":
    try:
        args = process_args(__file__)
        visualize_samples(args)
    except Exception as e:
        logger.error(e)