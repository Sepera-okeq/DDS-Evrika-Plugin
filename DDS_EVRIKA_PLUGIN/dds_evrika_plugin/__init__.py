from .dds_evrika_plugin import DDSEvrikaPlugin

# Registering the plugin in Krita
Krita.instance().addExtension(DDSEvrikaPlugin(Krita.instance()))
