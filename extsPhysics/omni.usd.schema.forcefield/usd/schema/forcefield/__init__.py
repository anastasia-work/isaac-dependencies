import os

from pxr import Plug

pluginsRoot = os.path.join(os.path.dirname(__file__), '../../../plugins')
forceFieldSchemaPath = pluginsRoot + '/ForceFieldSchema/resources'

Plug.Registry().RegisterPlugins(forceFieldSchemaPath)
