import json
import os
from pathlib import Path
import shutil
import time

pics_path = Path("pics")


def move_images():
    last_data_bytes = b""

    duplicate_images = []  # type: list[str]

    for image in sorted(list(pics_path.iterdir()), key=lambda x: int(x.stem)):
        with image.open("rb") as f:
            curr_data_bytes = f.read()
            if curr_data_bytes == last_data_bytes:
                print(f"Found duplicate: {image}")
                duplicate_images.append(image.absolute().__str__())
            last_data_bytes = curr_data_bytes

    if not os.path.exists("duplicates"):
        os.makedirs("duplicates")
    for image in duplicate_images:
        print(f"Moving {image} to duplicates")
        shutil.move(image, "duplicates")


def save_missing_images_data():
    missing_pics = []
    saved_data = json.loads(Path("data.json").read_text())["pics"]
    for pic in saved_data:
        if not (pics_path / pic).exists():
            missing_pics.append(pic)
    Path("missing_pics.json").write_text(json.dumps(missing_pics))


if __name__ == "__main__":
    move_images()
    save_missing_images_data()
    print("Done")
