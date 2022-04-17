import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from progressbar import ProgressBar


CHUNK_SIZE = 1_000_000
START_TIME = 1648806250315


def parse_timestamp(timestamp):
    """Convert a YYYY-MM-DD HH:MM:SS.SSS timestamp to milliseconds after the start of r/Place 2022."""
    date_format = "%Y-%m-%d %H:%M:%S.%f"
    try:
        # Remove the UTC timezone from the timestamp and convert it to a POSIX timestamp.
        timestamp = datetime.strptime(timestamp[:-4], date_format).timestamp()
    except ValueError:
        # The timestamp is exactly on the second, so there is no decimal (%f).
        # This happens 1/1000 of the time.
        timestamp = datetime.strptime(timestamp[:-4], date_format[:-3]).timestamp()

    # Convert from a float in seconds to an int in milliseconds
    timestamp *= 1000.0
    timestamp = int(timestamp)

    # The earliest timestamp is 1648806250315, so subtract that from each timestamp
    # to get the time in milliseconds since the beginning of the experiment.
    timestamp -= START_TIME

    return timestamp


def parse_pixel_color(pixel_color):
    """Convert a hex color code to an integer key."""
    hex_to_key = {
        "#000000": 0,
        "#00756F": 1,
        "#009EAA": 2,
        "#00A368": 3,
        "#00CC78": 4,
        "#00CCC0": 5,
        "#2450A4": 6,
        "#3690EA": 7,
        "#493AC1": 8,
        "#515252": 9,
        "#51E9F4": 10,
        "#6A5CFF": 11,
        "#6D001A": 12,
        "#6D482F": 13,
        "#7EED56": 14,
        "#811E9F": 15,
        "#898D90": 16,
        "#94B3FF": 17,
        "#9C6926": 18,
        "#B44AC0": 19,
        "#BE0039": 20,
        "#D4D7D9": 21,
        "#DE107F": 22,
        "#E4ABFF": 23,
        "#FF3881": 24,
        "#FF4500": 25,
        "#FF99AA": 26,
        "#FFA800": 27,
        "#FFB470": 28,
        "#FFD635": 29,
        "#FFF8B8": 30,
        "#FFFFFF": 31,
    }

    return hex_to_key[pixel_color]


def split_coords_single_points(points):
    """
    Given a dataframe containing only rows that have single-point
    coordinates, split the coordinates into x and y columns.
    """

    # Convert the coordinate column to a list of strings.
    points["coordinate"] = points["coordinate"].apply(lambda x: x.split(","))

    # Create new x and y columns from the coordinate column.
    points["x"] = points["coordinate"].apply(lambda x: x[0]).astype("uint16")
    points["y"] = points["coordinate"].apply(lambda x: x[1]).astype("uint16")

    # Drop the coordinate column.
    del points["coordinate"]

    return points


def split_coords_rectangles(rectangles):
    """
    Given a dataframe containing only rows that have rectangle coordinates,
    convert the rectangle rows to point rows with x and y columns.
    """

    # Separate the rectangle coordinate string into a list of ints.
    rectangles["coordinate"] = rectangles["coordinate"].apply(
        lambda x: [int(c) for c in x.split(",")]
    )

    # We will convert each rectangle into several point coordinates.

    # Make a new dataframe to store the points created from the rectangles.
    pts_from_recs = pd.DataFrame(columns=["timestamp", "pixel_color", "x", "y"])

    # Iterate over the rectangles in this chunk.
    for rect in rectangles.itertuples():
        x1, y1, x2, y2 = rect.coordinate
        width = x2 - x1 + 1
        height = y2 - y1 + 1

        for i in range(width):
            for j in range(height):
                x = x1 + i
                y = y1 + j

                pts_from_recs.loc[len(pts_from_recs)] = [
                    rect.timestamp,
                    rect.pixel_color,
                    x,
                    y,
                ]

    # Convert the columns into the correct dtypes.
    pts_from_recs["timestamp"] = pts_from_recs["timestamp"].astype("uint32")
    pts_from_recs["pixel_color"] = pts_from_recs["pixel_color"].astype("uint8")
    pts_from_recs["x"] = pts_from_recs["x"].astype("uint16")
    pts_from_recs["y"] = pts_from_recs["y"].astype("uint16")

    return pts_from_recs


def process_chunk(chunk, df):
    """Process a chunk of data and append it to a dataframe."""
    # Convert the timestamp and pixel_color columns to the correct dtypes.
    chunk["timestamp"] = chunk["timestamp"].astype("uint32")
    chunk["pixel_color"] = chunk["pixel_color"].astype("uint8")

    # Group by point and rectangle coordinates.
    # Points have x and y coordinates, rectangles have x1, y1, x2, y2 coordinates.
    # We can determine the type of the coordinate by the number of commas.
    groups = chunk.groupby(chunk["coordinate"].str.count(",") == 1)
    rectangles = None
    points = groups.get_group(True).reset_index(drop=True)
    try:
        rectangles = groups.get_group(False).reset_index(drop=True)
    except KeyError:
        # There are no rectangles in this chunk.
        pass

    # Convert point's coordinate column into x and y columns.
    points = split_coords_single_points(points)

    # Append the points to the dataframe.
    df = pd.concat((df, points), ignore_index=True)

    # If this chunk has rectangles, convert them into point coordinates.
    if rectangles is not None:
        rectangles = split_coords_rectangles(rectangles)
        df = pd.concat((df, rectangles), ignore_index=True)

    return df


def trim(infile, outfile):
    """Trim the infile data and write it to outfile."""
    assert outfile.name.endswith(".parquet")

    df = pd.DataFrame(columns=["timestamp", "pixel_color", "x", "y"])
    df["timestamp"] = df["timestamp"].astype("uint32")
    df["pixel_color"] = df["pixel_color"].astype("uint8")
    df["x"] = df["x"].astype("uint16")
    df["y"] = df["y"].astype("uint16")

    file_size_bytes = os.path.getsize(infile.name)
    approx_lines_per_byte = 0.013
    file_approx_lines = int(file_size_bytes * approx_lines_per_byte)

    with pd.read_csv(
        infile,
        usecols=["timestamp", "pixel_color", "coordinate"],
        converters={
            "timestamp": parse_timestamp,
            "pixel_color": parse_pixel_color,
        },
        chunksize=CHUNK_SIZE,
        engine="c",
        compression={"method": "gzip"},
    ) as csv:
        progress_bar = ProgressBar(max_value=file_approx_lines)
        progress_bar.update(0)
        chunk_no = 0
        for chunk in csv:
            progress_bar.update(chunk_no * CHUNK_SIZE)
            chunk_no += 1
            df = process_chunk(chunk, df)

    df["timestamp"] = df["timestamp"].astype("uint32")

    df.sort_values("timestamp", inplace=True, ignore_index=True)
    df.to_parquet(
        outfile,
        # The default pyarrow version is 1.0, which changes the timestamp column to int64.
        # https://github.com/pandas-dev/pandas/issues/37327
        # https://issues.apache.org/jira/browse/ARROW-9215
        version="2.6",
    )


if __name__ == "__main__":
    INFILE_PATH = "data/2022_place_canvas_history.csv.gzip"
    OUTFILE_PATH = "data/test_trimmed.parquet"

    base_dir = Path(__file__).resolve().parent.parent

    infile = base_dir / INFILE_PATH
    outfile = base_dir / OUTFILE_PATH

    with infile.open("rb") as f_in:
        with outfile.open("wb") as f_out:
            trim(f_in, f_out)

    # Print the result.
    df = pd.read_parquet(outfile)
    print(df)
    print(df.dtypes)
    print(df.memory_usage())
