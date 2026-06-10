# Author: Samik Banerjee

import os

# Physical Dimensions (Z, Y, X)
PHYSICAL_SCALE = (0.5, 0.1102, 0.1102)

# Global variables (defaults, can be overridden by CLI)
DEFAULT_INPUT_DIR = r"c:\Users\banerjee\Desktop\um1_3d_volume"
DEFAULT_OUTPUT_DIR = r"c:\Users\banerjee\Desktop\um1_3d_volume\neurite_detection\pipeline_output"

# Detection Parameters
FRANGI_SIGMAS = [2.0, 4.0, 6.0, 8.0, 12.0]
MIN_NEURITE_SIZE = 2000

# File patterns
CHANNEL_488 = "B3Well7_1_AN_20260529_233255_Area1_round0_20260529_233740_488_F0044_cmle.tif"
CHANNEL_555 = "B3Well7_1_AN_20260529_233255_Area1_round0_20260529_233740_555_F0044_cmle.tif"
CHANNEL_640 = "B3Well7_1_AN_20260529_233255_Area1_round0_20260529_233740_640_F0044_cmle.tif"

# GPU Settings
USE_GPU = True
