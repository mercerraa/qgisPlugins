def classFactory(iface):
    from .layer_reverse import LayerReverse
    return LayerReverse(iface)