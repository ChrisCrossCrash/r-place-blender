# r/Place Python and Blender Data Visualization

![The Blender logo in r/Place, rendered in Blender](images/blender-logo.jpg)


## Prerequisites

- Python >=3.10 (tested on 3.10.2)
- Blender >=3.1 (tested on 3.1.2)
- ~4 GB of free RAM (for processing the data)
- ~15 GB of free space on the hard drive (until the raw data is trimmed)
- It helps to have a powerful GPU for rendering the frames in Blender.

Some basic knowledge of Python and Blender is assumed. If you are a beginner, here are some Tutorials I highly recommend:

- [Corey Schafer Python Tutorial Playlist](https://youtube.com/playlist?list=PL-osiE80TeTskrapNbzXhwoFUiLCjGgY7)
- [Blender Guru Donut Tutorial Playlist](https://youtube.com/playlist?list=PLjEaoINr3zgFX8ZsChQVQsuDSjEqdWMAD)

## Setup

1. Install [Python](https://www.python.org/) and [Blender](https://www.blender.org/download/) if you haven't already.
2. Clone this repository (or download it as a Zip file and extract).
3. Download the [r/Place 2022 dataset](https://www.reddit.com/r/place/comments/txvk2d/rplace_datasets_april_fools_2022/) as a single file. Do not extract it.
4. Open the repository in a terminal and create a new virtual environment with:
   ```
   python3 -m venv .venv
   ```
5. Activate the virtual environment with:

   Windows:
   ```
   .\.venv\Scripts\activate
   ```
   Linux:
   ```
   source .venv/bin/activate
   ```
6. Install the required packages with:
   ```
   python -m pip install -U pip wheel setuptools
   python -m pip install -r requirements.txt
   ```
   Or, if you have [Poetry](https://python-poetry.org/) installed:
   ```
   poetry install
   ```
7. Open the Jupyter notebook with:
   ```
   jupyter notebook guide.ipynb
   ```
   Follow the guide and execute the code cells to produce the color and age frames that will be loaded in Blender.
8. Open `r-place.blend` in Blender. If you produced the age and color frames with the Jupyter notebook, they will be loaded automatically.

## Development

### Generating a new `requirements.txt` file

Use the following command to generate a new `requirements.txt` file for non-Poetry users:
```
poetry export --without-hashes > requirements.txt
```
