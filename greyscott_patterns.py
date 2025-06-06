from utilities import np

###############################################################################
# Pattern presets
###############################################################################

GREY_SCOTT_PATTERNS = {
    "labyrinthine": {"feed": 0.037, "kill": 0.060, "du": 0.16, "dv": 0.08},
    "spots": {"feed": 0.029, "kill": 0.062, "du": 0.16, "dv": 0.08},
    "holes": {"feed": 0.039, "kill": 0.058, "du": 0.16, "dv": 0.08},
    "worms": {"feed": 0.078, "kill": 0.061, "du": 0.16, "dv": 0.08},
    "coral_growth": {"feed": 0.055, "kill": 0.062, "du": 0.16, "dv": 0.08}
}


ALL_PATTERNS = list(GREY_SCOTT_PATTERNS.keys())

def get_random_pattern(rng: np.random.Generator):
    pattern = rng.choice(ALL_PATTERNS)
    return pattern, GREY_SCOTT_PATTERNS[pattern]