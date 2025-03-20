import shutil
from pathlib import Path

import requests


def download_file(url, output_path):
    """
    Download a file from a URL to the specified output path.
    """
    print(f"Downloading {url} to {output_path}...")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        shutil.copyfileobj(response.raw, f)

    print(f"Downloaded {output_path} successfully.")


def main():
    weights_dir = Path("rave_model_weights")
    weights_dir.mkdir(exist_ok=True)

    # Define the models to download with their URLs and target filenames
    models = [
        {
            "url": "https://play.forum.ircam.fr/rave-vst-api/get_model/nasa",
            "filename": "moon.ts",
        },
        {
            "url": "https://play.forum.ircam.fr/rave-vst-api/get_model/percussion",
            "filename": "percussion.ts",
        },
        {
            "url": "https://huggingface.co/Intelligent-Instruments-Lab/rave-models/resolve/main/birds_dawnchorus_b2048_r48000_z8.ts?download=true",
            "filename": "dawn_birds.ts",
        },
        {
            "url": "https://huggingface.co/Intelligent-Instruments-Lab/rave-models/resolve/main/water_pondbrain_b2048_r48000_z16.ts?download=true",
            "filename": "water.ts",
        },
    ]

    for model in models:
        output_path = weights_dir / model["filename"]
        download_file(model["url"], output_path)


if __name__ == "__main__":
    print("Starting download of RAVE model weights...")
    main()
    print("All RAVE model weights downloaded successfully!")
