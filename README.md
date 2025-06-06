# GREY_SCOTT_SIMULATION

## Create and activate Conda environment

```bash
cd esp_simulation
conda env create -f environment.yaml
conda activate grey_scott
```

### Notes
- Most of the packages are common, so you may already have these installed

## Grey-Scott Patterns

| Pattern        | Feed  | Kill  | du   | dv   |
|----------------|-------|-------|------|------|
| labyrinthine   | 0.037 | 0.060 | 0.16 | 0.08 |
| spots          | 0.029 | 0.062 | 0.16 | 0.08 |
| holes          | 0.039 | 0.058 | 0.16 | 0.08 |
| worms          | 0.078 | 0.061 | 0.16 | 0.08 |
| coral_growth   | 0.055 | 0.062 | 0.16 | 0.08 |

> Reference: [Visual-PDE: Grey-Scott Model](https://visualpde.com/nonlinear-physics/gray-scott.html)

## Test the code

```bash
python -m pytest
```

## Create a dataset

### Program: [create_dataset.py](./create_dataset.py)

#### `create_dataset.py` Command-Line Options

| Option                                | Description                                                        | Choices/Types                                                                              |
|---------------------------------------|--------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| `-h, --help`                          | Show help message and exit                                         | —                                                                                          |
| `--debug, -d`                         | Enables logging with debug level verbosity                         | Flag (presence means `'On'`)                                                               |
| `--ntasks`                            | Number of parallel tasks (CPU cores)                               | Any integer (e.g., `1`, `4`)                                                               |
| `--seed-step`                         | Number of seeds to be processed and written at a time              | Any integer (default: `100`)                                                               |
| `--min-seed`                          | Start seed for generating simulations                              | Any positive integer (default: `1`)                                                        |
| `--max-seed`                          | End seed for generating simulations                                | Any positive integer (default: `5`)                                                        |
| `--grid-length`                       | Length of one side of 2D grid                                      | Any integer > 4 (default: `32`)                                                            |
| `--max-iterations`                    | Maximum Euler integration steps                                    | Any integer (default: `1000`)                                                              |
| `--patch-radius`                      | Half-width of central perturbation                                 | Any integer (default: `20`)                                                                |
| `--patch-prob`                        | Probability of placing each patch                                  | Float between `0.0` and `1.0` (default: `0.5`)                                             |
| `--output-path`                       | Path to directory to create `--output-folder` and save data        | String (e.g., `"./results"`)                                                               |
| `--output-folder`                     | Output folder name to save simulation data                         | String (default: `"esp_dataset"`)                                                          |
| `--save-states`                       | When to save intermediate states                                   | String options:<br>• `all`<br>• `none`<br>• `interval-<N>`<br>• `first-<N>`<br>• `base-<B>`<br>Multiple options can be chained (e.g. `"first-10,interval-50"`) |


### Example command

```bash
python create_dataset.py \
--output-folder "greyscott_dataset_500" \
--min-seed 1 \
--max-seed 500 \
--seed-step 100 \
--ntasks 2 \
--grid-length 64 \
--patch-prob 0.5 \
--patch-radius 2 \
--max-iterations 1500 \
--save-states "first-20,interval-100"
```


## Visualize a dataset

### Program: [visualize_dataset.py](./visualize_dataset.py)

#### `visualize_dataset.py` Command-Line Options
| Option                      | Description                                                                   | Choices/Types                  | Default         |
|-----------------------------|-------------------------------------------------------------------------------|--------------------------------|-----------------|
| `-h`, `--help`              | Show help message and exit                                                    | —                              | —               |
| `-d`, `--debug`             | Enables logging with debug level verbosity                                    | Flag (on if present)           | `false`         |
| `--data-file DATA_FILE`     | Path to the input HDF5 file with saved simulation runs                        | String (file path)             | **required**    |
| `--random-seed RANDOM_SEED`| Random seed for selecting samples                                             | Integer                        | `20`          |
| `--num-samples NUM_SAMPLES`| Number of simulation samples to visualize                                     | Integer                        | `1`             |
| `--output-folder`           | Directory where images and gifs will be saved (created if it doesn't exist)              | String (path to folder)        | **required**    |
| `--gif-fps GIF_FPS`                 | Frames per second for gif playback                                            | Integer                        | `20`            |
| `--gif-delay GIF_DELAY`                 | Delay seconds between gif playback loop                                          | Integer                        | `3`            |
| `--gif-cmap CMAP`               | Colormap for gif plots, perceptually uniform preferred (Matplotlib-compatible)                            | String (e.g. `'turbo'`)      | `'turbo'`     |
| `--image-cmap CMAP`               | Colormap for image plots, diverging preferred (Matplotlib-compatible)                            | String (e.g. `'seismic'`)      | `'seismic'`     |

### Example command

```bash
python visualize_dataset.py \
--data-file "greyscott_dataset_500/greyscott_64x64_1-500.hdf5" \
--output-folder "greyscott_dataset_500/sample_viz" \
--random-seed 24 \
--num-samples 20 \
--gif-fps 10 \
--gif-delay 2 \
--gif-cmap "turbo" \
--image-cmap "seismic"
```

## Example Patterns
### Coral Growth
![Coral Growth](./images/greyscott_coral_growth_42.gif)
### Labyrinthine
![Labyrinthine](./images/greyscott_labyrinthine_42.gif)
### Holes
![Holes](./images/greyscott_holes_42.gif)
### Spots
![Spots](./images/greyscott_spots_42.gif)
### Worms
![Worms](./images/greyscott_worms_42.gif)