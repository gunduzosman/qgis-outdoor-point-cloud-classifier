from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = "outdoor_point_cloud_classifier"
FILES = (
    "__init__.py",
    "metadata.txt",
    "plugin.py",
    "provider.py",
    "algorithm.py",
)


def main():
    destination = ROOT / "dist" / "outdoor_point_cloud_classifier.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in FILES:
            source = ROOT / filename
            archive.write(source, f"{PLUGIN_DIR}/{filename}")
    print(f"Created {destination}")


if __name__ == "__main__":
    main()
