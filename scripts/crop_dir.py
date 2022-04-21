from pathlib import Path
import imageio as iio


def crop_dir(in_dir, out_dir, x1, y1, x2, y2):
    """
    For each image in the input directory, crop it,
    and then save it to the output directory with the same file name.
    """

    print(f"Cropping images in {in_dir} to {out_dir}")
    for file in in_dir.iterdir():
        with file.open("rb") as f_in:
            img = iio.imread(f_in)

        # Crop the image.
        img = img[y1:y2, x1:x2]

        # Make the out_dir if it doesn't already exist.
        out_dir.mkdir(exist_ok=True)

        iio.imwrite(out_dir / file.name, img)

        # TODO: Implement progressbar2 here.


if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent
    in_dir = base_dir / "data/frames_color"
    out_dir = base_dir / "data/frames_color_cropped"
    x1, y1, x2, y2 = 0, 0, 100, 100
    crop_dir(in_dir, out_dir, x1, y1, x2, y2)
