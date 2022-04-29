#!/usr/bin/env python

import os
import argparse
from trim import trim
from generate import generate
from crop_dir import crop_dir
from pathlib import Path


def trim_command(args):
    infile = args.infile
    outfile = args.outfile
    try:
        trim(infile, outfile)
    except AssertionError:
        print("The outfile must have a .parquet extension.")


def generate_command(args):
    generate(
        args.infile,
        args.colorpath,
        args.datapath,
        start_ms=args.start_ms,
        timescale=args.timescale,
        frames=args.frames,
        fps=args.fps,
        heat_half_life=args.half_life,
        start_frame=args.start_frame,
    )


def crop_dir_command(args):
    in_dir = args.in_dir
    out_dir = args.out_dir
    x1 = args.x1
    y1 = args.y1
    x2 = args.x2
    y2 = args.y2
    crop_dir(in_dir, out_dir, x1, y1, x2, y2)


def dir_path(string):
    if os.path.isdir(string):
        return Path(string)
    else:
        raise NotADirectoryError(string)


def parse_args():
    parser = argparse.ArgumentParser(
        description="A command line tool for processing the r/Place 2022 dataset."
    )
    subparsers = parser.add_subparsers(title="commands")

    parser_trim = subparsers.add_parser("trim", help="Trim and sort the raw dataset.")
    parser_trim.add_argument(
        "infile",
        help="The path to the r/Place 2022 CSV dataset.",
        type=argparse.FileType("rb"),
    )
    parser_trim.add_argument(
        "outfile",
        help="The path to the trimmed dataset.",
        type=argparse.FileType("wb"),
    )
    parser_trim.set_defaults(func=trim_command)

    parser_generate = subparsers.add_parser(
        "generate", help="Generate heat and color maps from the sorted parquet dataset."
    )
    parser_generate.add_argument(
        "infile",
        help="The path to the trimmed parquet dataset.",
        type=argparse.FileType("rb"),
    )
    parser_generate.add_argument(
        "colorpath", help="The path to save the color map PNG images to.", type=dir_path
    )
    parser_generate.add_argument(
        "datapath", help="The path to save the heat map PNG images to.", type=dir_path
    )
    parser_generate.add_argument(
        "--start_ms", type=int, help="The start timestamp in milliseconds.", default=0
    )
    parser_generate.add_argument(
        "--timescale", type=int, help="The time multiplication factor.", default=1000
    )
    parser_generate.add_argument(
        "--frames", type=int, help="The number of frames to generate.", default=600
    )
    parser_generate.add_argument(
        "--fps", type=int, help="The number of frames per second.", default=60
    )
    parser_generate.add_argument(
        "--half_life",
        type=int,
        help="The half life of the heat map.",
        default=10 * 60 * 1000,
    )
    parser_generate.add_argument(
        "--scale_height",
        type=float,
        help="The change in height at which the height increase"
        " for changed pixels is reduced by a factor of e.",
        default=0.3,
    )
    parser_generate.add_argument(
        "--start_frame",
        type=int,
        help="The frame to start generating heat maps at. This only affects the file names.",
        default=0,
    )
    parser_generate.set_defaults(func=generate_command)

    parser_crop_dir = subparsers.add_parser(
        "cropdir", help="Crop a directory of images."
    )
    parser_crop_dir.add_argument(
        "in_dir",
        help="The path to the directory of images to crop.",
        type=dir_path,
    )
    parser_crop_dir.add_argument(
        "out_dir",
        help="The path to the directory to save the cropped images to.",
        type=dir_path,
    )
    parser_crop_dir.add_argument(
        "x1", type=int, help="The x-coordinate of the top left corner (inclusive)."
    )
    parser_crop_dir.add_argument(
        "y1", type=int, help="The y-coordinate of the top left corner (inclusive)."
    )
    parser_crop_dir.add_argument(
        "x2", type=int, help="The x-coordinate of the bottom right corner (exclusive)."
    )
    parser_crop_dir.add_argument(
        "y2", type=int, help="The y-coordinate of the bottom right corner (exclusive)."
    )
    parser_crop_dir.set_defaults(func=crop_dir_command)

    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_args()
    except NotADirectoryError as e:
        print(f"The directory '{e.args[0]}' does not exist.")
        exit(1)

    args.func(args)
