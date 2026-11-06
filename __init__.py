def classFactory(iface):
    from .plugin import OutdoorPointCloudClassifierPlugin
    return OutdoorPointCloudClassifierPlugin(iface)
