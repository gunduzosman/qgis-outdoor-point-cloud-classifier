# QGIS Outdoor Point Cloud Classifier

A small, free QGIS Processing plugin for an initial **outdoor LiDAR** workflow. It delegates point-cloud processing to [PDAL](https://github.com/PDAL/PDAL): SMRF ground classification, height-above-ground calculation, and height-band assignment to LAS classes for vegetation.

> **Status: early scaffold (0.1.0).** It has not yet been validated in a real QGIS installation or against representative LiDAR data. Treat outputs as experimental and inspect them before using them in production.

## What it does

- Adds a Processing Toolbox provider named **Outdoor Point Cloud Classifier**.
- Reads LAS/LAZ and writes to a separate LAS/LAZ output; it refuses an identical input/output path.
- Runs PDAL `filters.smrf` to classify ground (LAS class 2), then `filters.hag_delaunay` and assigns height bands:
  - class 3: low vegetation, below the configured low-height limit;
  - class 4: medium vegetation, between the low and medium limits;
  - class 5: high vegetation, above the medium limit.
- Exposes the SMRF settings and vegetation height limits in the Processing dialog.

This first version does **not** classify buildings or indoor scans. Height alone cannot reliably distinguish a roof from tall vegetation. Building detection and indoor classification are planned as separate, evaluated workflows rather than being presented as reliable in this initial tool.

## Requirements

- QGIS 3.28 or newer.
- PDAL installed and available on the system path. If it is not on `PATH`, provide the full path to the PDAL executable in the algorithm dialog.
- For LAZ input/output, the installed PDAL build must include a compatible LAZ reader/writer backend.

The plugin does not bundle PDAL or modify the source cloud. Availability of PDAL varies among QGIS installers and operating systems; verify it with `pdal --version` in the same environment used to launch QGIS.

## Install

### Package the plugin ZIP

From the repository root, run:

```bash
python scripts/package_plugin.py
```

This creates `dist/outdoor_point_cloud_classifier.zip` with the plugin directory at the ZIP root. In QGIS, choose **Plugins → Manage and Install Plugins → Install from ZIP** and select that file. Alternatively, copy the `outdoor_point_cloud_classifier` folder into the QGIS Python plugins directory and enable it in the plugin manager.

### Run

1. Confirm `pdal --version` works from QGIS's environment (on Windows, use the OSGeo4W environment where applicable).
2. Restart QGIS and enable **Outdoor Point Cloud Classifier**.
3. Open **Processing Toolbox** and search for **Classify outdoor point cloud (ground + vegetation)**.
4. Select an input file, choose a new output file, adjust the settings if needed, and run.
5. Load the output and inspect classes 2–5 using QGIS's point-cloud renderer. Test on a small copy first.

## Notes on accuracy and parameters

SMRF and height-band thresholds are data-dependent. Point density, coordinate units, terrain slope, vegetation structure, scan angle, and existing classification all affect results. Defaults are starting values, not universal recommendations. The plugin currently reruns classification rather than preserving existing class labels. Keep the original file and compare the output visually and against trusted reference data.

Do not interpret the vegetation classes as semantic object recognition. For example, a tall object can be a tree or a building; this version does not resolve that distinction. Results should be checked for steep terrain, dense canopy, bridges, roofs, and no-ground areas.

## Development

The plugin is intentionally dependency-light: it uses the QGIS Processing API and invokes the PDAL command-line program. Build a ZIP with `python scripts/package_plugin.py`. The package script copies only runtime plugin files and `metadata.txt`.

Issues and test reports are welcome. Please include QGIS and PDAL versions, OS, input format, CRS/units, and a small reproducible sample or synthetic test description (do not upload sensitive point clouds).

## License

MIT. See [LICENSE](LICENSE).
