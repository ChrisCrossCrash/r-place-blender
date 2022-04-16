import os
from pathlib import Path
from PIL import Image
import numpy as np
import pandas as pd

UINT16_MAX = 65_535
TIMESTAMP_MAX = 300_589_892
SORTED_PATH = "data/2022_place_canvas_history.parquet"
COLOR_FRAMES_PATH = "data/frames_color/"
AGE_FRAMES_PATH = "data/frames_age/"


def age_to_val(px_age, compression=0.001):
    """Convert a pixel age into a 16-bit value.

    Higher compression values make the transformation more extreme (less linear).
    Tip: If you change the compression value here, you will also need to change it
    in Blender's Geometry Nodes modifier settings!
    """

    # Scale along the x-axis.
    scaled_age = px_age * compression

    # Scale along the y-axis.
    scaling_const = UINT16_MAX / np.log(TIMESTAMP_MAX * compression + 1)

    return scaling_const * np.log(scaled_age + 1)


def generate(
    infile, colorpath, agepath, start_ms=0, timescale=1000, frames=600, fps=60
):
    """Generate the age and color frames for the given file."""

    df = pd.read_parquet(infile)

    # The time gap between frames.
    dt = round(timescale * 1000 / fps)

    # earlier we converted the hex colors from the r/Place dataset to a key.
    # We can use this tuple to convert the key to an RGB color.
    indexed_rgb = (
        (0, 0, 0),
        (0, 117, 111),
        (0, 158, 170),
        (0, 163, 104),
        (0, 204, 120),
        (0, 204, 192),
        (36, 80, 164),
        (54, 144, 234),
        (73, 58, 193),
        (81, 82, 82),
        (81, 233, 244),
        (106, 92, 255),
        (109, 0, 26),
        (109, 72, 47),
        (126, 237, 86),
        (129, 30, 159),
        (137, 141, 144),
        (148, 179, 255),
        (156, 105, 38),
        (180, 74, 192),
        (190, 0, 57),
        (212, 215, 217),
        (222, 16, 127),
        (228, 171, 255),
        (255, 56, 129),
        (255, 69, 0),
        (255, 153, 170),
        (255, 168, 0),
        (255, 180, 112),
        (255, 214, 53),
        (255, 248, 184),
        (255, 255, 255),
    )

    # Generate the canvases to hold the running values
    img_color = Image.new("RGB", (2000, 2000), "white")
    px_birthtimes = np.zeros((2000, 2000), dtype="uint32")

    # Create an iterator that yields the rows of the dataset in order.
    px_iterator = df.itertuples()

    # Get the first pixel.
    px = next(px_iterator)

    # Create "frames_color" and "frames_age" directories if they don't already exist.
    # color_frames_abs_path.mkdir(exist_ok=True)
    # age_frames_abs_path.mkdir(exist_ok=True)

    # Iterate through the frames.
    for ms in range(start_ms, TIMESTAMP_MAX, dt):
        frame_no = (ms - start_ms) // dt
        if frame_no >= frames:
            # Stop after the last frame.
            break

        # Draw pixels where timestamp == ms
        # There may be multiple pixels with the same timestamp.
        while px.timestamp <= ms:
            # Draw the pixel's color to the color canvas.
            img_color.putpixel(
                (px.x, px.y),
                indexed_rgb[px.pixel_color],
            )
            # Draw the pixel's birthtime to the birthtime canvas.
            px_birthtimes[px.y, px.x] = px.timestamp
            try:
                # Get the next pixel.
                px = next(px_iterator)
            except StopIteration:
                # Break out of the loop if we've reached the end of the dataset.
                break

        # After all of the pixels less than the frame's timestamp have been drawn,
        # save the color and birthtime canvases as frames.
        filename = f"frame-{str(frame_no).zfill(4)}.png"

        # Subtract the birthtimes of the pixels from the current time to get their ages.
        # If the pixel has a timestamp of 0, treat it as having max age.
        # (it's one of the original white pixels)
        px_ages = np.where(
            px_birthtimes == 0, UINT16_MAX, age_to_val(ms - px_birthtimes)
        )

        # Convert the NumPy array to a Pillow 16-bit Image object.
        # FIXME: This should be a black and white image, not color.
        img_age = Image.fromarray(px_ages.astype("uint16"), "I;16")

        # Save the frames.
        print(filename)
        img_age.save(agepath / filename, "PNG", optimize=True, bits=16)
        img_color.save(colorpath / filename, "PNG", optimize=True)


if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent
    sorted_abs_path = base_dir / SORTED_PATH
    color_frames_abs_path = base_dir / COLOR_FRAMES_PATH
    age_frames_abs_path = base_dir / AGE_FRAMES_PATH

    generate(
        sorted_abs_path,
        color_frames_abs_path,
        age_frames_abs_path,
        start_ms=100_00_000,
        frames=20,
    )
