from pathlib import Path
from math import exp
import imageio
import numpy as np
import pandas as pd

TIMESTAMP_MAX = 300_589_892


def calculate_frame_heat(heat_map, half_life, dt):
    """
    Given the heat map, half life, and time step,
    calculate new heat values for the next frame.
    """
    return heat_map * 2 ** (-dt / half_life)


def calculate_pressure(P_0, z, H):
    """
    Given the initial pressure P_0, height z, and scale height H,
    calculate the pressure P(z) at the given height.
    """
    try:
        # Get the pressure when z is a single value.
        return P_0 * exp(-z / H)
    except TypeError:
        # This is a NumPy array.
        return P_0 * np.exp(-z / H)


def generate(
    infile,
    colorpath,
    datapath,
    start_ms=0,
    timescale=1000,
    frames=600,
    fps=60,
    heat_half_life=10 * 60 * 1000,
    scale_height=0.3,
    start_frame=0,
):
    """Generate the heat and color frames for the given file."""

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
    img_color = np.full((2000, 2999, 3), 255, dtype=np.uint8)
    img_heat = np.zeros((2000, 2999), dtype=np.float32)

    # Create an iterator that yields the rows of the dataset in order.
    px_iterator = df.itertuples()

    # Get the first pixel.
    px = next(px_iterator)

    # We won't bother calculating the heat for pixels that will be more than ten
    # half lives old by the time we reach the first frame. At ten half lives,
    # a pixel will be 1/1024th of it's initial height. We also make sure
    # the the buffer time is a multiple of the frame gap time (dt), so that the start
    # time is precise to the millisecond.
    heat_map_buffer_time = dt * (10 * heat_half_life // dt)
    calculation_start_time = max(0, start_ms - heat_map_buffer_time)

    print("Calculating heat map buffer...")

    # Offset the number frames to render by the start frame.
    frames += start_frame

    # Iterate through the frames.
    frame_no = start_frame
    for ms in range(calculation_start_time, TIMESTAMP_MAX, dt):
        # Stop after the last frame.
        if frame_no >= frames:
            break

        # Draw pixels where timestamp <= ms
        while px.timestamp <= ms:
            # 0, 0 is the center of the canvas. We need to add 1500 to x and
            # 1000 to y so that 0, 0 is the top left corner.
            x_pos = px.x + 1500
            y_pos = px.y + 1000

            # Draw the pixel's color to the color canvas.
            img_color[y_pos, x_pos] = indexed_rgb[px.pixel_color]

            # Make the added height for new pixels
            #  decay exponentially with initial height.
            H_0 = 0.1
            img_heat[y_pos, x_pos] += calculate_pressure(
                H_0,  # Height increase for a pixel with starting height of 0
                img_heat[y_pos, x_pos],  # Initial height of this pixel
                scale_height,
            )

            try:
                # Get the next pixel.
                px = next(px_iterator)
            except StopIteration:
                # Break out of the loop if we've reached the end of the dataset.
                break

        # After all of the pixels less than the frame's timestamp have been drawn,
        # save the color and birthtime canvases as frames.
        img_heat = calculate_frame_heat(img_heat, heat_half_life, dt)

        if ms < start_ms:
            # Don't save the frame if it's before the start time.
            continue

        zero_arr = np.zeros((2000, 2999), dtype=np.float32)
        img_data = np.dstack((zero_arr, img_heat, zero_arr))

        print(f"Saving frame {frame_no}")

        # Save the frames.
        imageio.imwrite(
            colorpath / f"frame-{str(frame_no).zfill(4)}.png",
            img_color,
            optimize=True,
        )

        imageio.imwrite(
            datapath / f"frame-{str(frame_no).zfill(4)}.exr",
            img_data,
        )

        frame_no += 1


if __name__ == "__main__":
    SORTED_PATH = "data/2022_place_canvas_history.parquet"
    COLOR_FRAMES_PATH = "data/frames_color/"
    HEAT_FRAMES_PATH = "data/frames_heat/"

    base_dir = Path(__file__).parent.parent
    sorted_abs_path = base_dir / SORTED_PATH
    color_frames_abs_path = base_dir / COLOR_FRAMES_PATH
    heat_frames_abs_path = base_dir / HEAT_FRAMES_PATH

    generate(
        sorted_abs_path,
        color_frames_abs_path,
        heat_frames_abs_path,
        start_ms=100_00_000,
        frames=20,
    )
