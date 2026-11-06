import json
import os
import shutil
import subprocess
import tempfile

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)


class ClassifyOutdoorPointCloudAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    PDAL = "PDAL"
    WINDOW = "WINDOW"
    SLOPE = "SLOPE"
    THRESHOLD = "THRESHOLD"
    SCALAR = "SCALAR"
    LOW_MAX = "LOW_MAX"
    MEDIUM_MAX = "MEDIUM_MAX"

    def name(self):
        return "classify_outdoor_point_cloud"

    def displayName(self):
        return "Classify outdoor point cloud (ground + vegetation)"

    def group(self):
        return "Outdoor classification"

    def groupId(self):
        return "outdoor_classification"

    def shortHelpString(self):
        return (
            "Runs PDAL SMRF ground classification, calculates height above ground, "
            "then assigns LAS classes 3, 4 and 5 by configurable height ranges. "
            "The source file is read-only; results are written to a separate LAS/LAZ file. "
            "This is a first-version terrain/vegetation workflow, not a building classifier. "
            "Inspect the output against the source before using it for production."
        )

    def createInstance(self):
        return ClassifyOutdoorPointCloudAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                "Input LAS/LAZ point cloud",
                behavior=QgsProcessingParameterFile.File,
                fileFilter="LAS/LAZ (*.las *.laz)",
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                "Output classified LAS/LAZ",
                fileFilter="LAS/LAZ (*.las *.laz)",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PDAL,
                "PDAL executable",
                defaultValue="pdal",
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.WINDOW,
                "SMRF window (m)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=18.0,
                minValue=1.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.SLOPE,
                "SMRF slope parameter",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.15,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD,
                "SMRF elevation threshold (m)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.5,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.SCALAR,
                "SMRF scalar",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1.25,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LOW_MAX,
                "Low vegetation maximum height above ground (m)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.5,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MEDIUM_MAX,
                "Medium vegetation maximum height above ground (m)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=2.0,
                minValue=0.01,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        input_path = self.parameterAsFile(self.INPUT, parameters, context)
        output_path = self.parameterAsFileOutput(self.OUTPUT, parameters, context)
        executable = self.parameterAsString(self.PDAL, parameters, context).strip()
        low_max = self.parameterAsDouble(self.LOW_MAX, parameters, context)
        medium_max = self.parameterAsDouble(self.MEDIUM_MAX, parameters, context)

        if not input_path or not os.path.isfile(input_path):
            raise QgsProcessingException("Input LAS/LAZ file does not exist.")
        if not output_path:
            raise QgsProcessingException("Choose an output LAS/LAZ file.")
        if os.path.abspath(input_path) == os.path.abspath(output_path):
            raise QgsProcessingException("Output must be a different file; the input is never overwritten.")
        if low_max >= medium_max:
            raise QgsProcessingException("Low vegetation maximum must be less than medium vegetation maximum.")
        if os.path.splitext(output_path)[1].lower() not in (".las", ".laz"):
            raise QgsProcessingException("Output filename must end in .las or .laz.")
        if not executable or not (shutil.which(executable) or os.path.isfile(executable)):
            raise QgsProcessingException(
                "PDAL executable was not found. Install PDAL and enter its full path if needed."
            )

        pipeline = [
            {"type": "readers.las", "filename": os.path.abspath(input_path)},
            {
                "type": "filters.smrf",
                "window": self.parameterAsDouble(self.WINDOW, parameters, context),
                "slope": self.parameterAsDouble(self.SLOPE, parameters, context),
                "threshold": self.parameterAsDouble(self.THRESHOLD, parameters, context),
                " scalar": self.parameterAsDouble(self.SCALAR, parameters, context),
            },
            {"type": "filters.hag_delaunay"},
            {
                "type": "filters.assign",
                "value": ["Classification = 3"],
                "where": f"HeightAboveGround >= 0 && HeightAboveGround < {low_max}",
            },
            {
                "type": "filters.assign",
                "value": ["Classification = 4"],
                "where": f"HeightAboveGround >= {low_max} && HeightAboveGround < {medium_max}",
            },
            {
                "type": "filters.assign",
                "value": ["Classification = 5"],
                "where": f"HeightAboveGround >= {medium_max}",
            },
            {"type": "writers.las", "filename": os.path.abspath(output_path)},
        ]
        # Keep the JSON in a temporary directory; PDAL writes only to the requested output.
        try:
            with tempfile.TemporaryDirectory(prefix="qgis_pc_classifier_") as temp_dir:
                pipeline_path = os.path.join(temp_dir, "pipeline.json")
                with open(pipeline_path, "w", encoding="utf-8") as pipeline_file:
                    json.dump(pipeline, pipeline_file, indent=2)
                feedback.pushInfo("Starting PDAL pipeline. The input file will not be modified.")
                result = subprocess.run(
                    [executable, "pipeline", pipeline_path],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    feedback.pushInfo(result.stdout.strip())
                if result.returncode != 0:
                    details = result.stderr.strip() or result.stdout.strip() or "No PDAL error details."
                    raise QgsProcessingException("PDAL failed:\n" + details)
        except QgsProcessingException:
            raise
        except OSError as error:
            raise QgsProcessingException(f"Could not run PDAL: {error}")

        if not os.path.isfile(output_path):
            raise QgsProcessingException("PDAL reported success but the output file was not created.")
        feedback.pushInfo("Classification complete. Review the output visually before production use.")
        return {self.OUTPUT: output_path}
