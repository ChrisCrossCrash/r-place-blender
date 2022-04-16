#!/usr/bin/env python

import os
import argparse
from trim import trim
from generate import generate
from pathlib import Path


def trim_command(args):
    infile = args.infile
    outfile = args.outfile
    try:
        trim(infile, outfile)
    except AssertionError:
        print("The outfile must have a .parquet extension.")


def generate_command(args):
    infile = args.infile
    colorpath = args.colorpath
    agepath = args.agepath
    start_ms = args.start_ms
    timescale = args.timescale
    frames = args.frames
    fps = args.fps
    generate(
        infile,
        colorpath,
        agepath,
        start_ms=start_ms,
        timescale=timescale,
        frames=frames,
        fps=fps,
    )


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
        "generate", help="Generate age and color maps from the sorted parquet dataset."
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
        "agepath", help="The path to save the age map PNG images to.", type=dir_path
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
    parser_generate.set_defaults(func=generate_command)

    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_args()
    except NotADirectoryError as e:
        print(f"The directory '{e.args[0]}' does not exist.")
        exit(1)

    args.func(args)
