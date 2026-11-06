from qgis.core import QgsProcessingProvider

from .algorithm import ClassifyOutdoorPointCloudAlgorithm


class OutdoorPointCloudProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(ClassifyOutdoorPointCloudAlgorithm())

    def id(self):
        return "outdoor_point_cloud"

    def name(self):
        return "Outdoor Point Cloud Classifier"

    def longName(self):
        return self.name()
