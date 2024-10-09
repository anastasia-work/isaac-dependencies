import os

from pxr import Plug
import pxr.UsdSkel
import pxr.Semantics

pluginsRoot = os.path.join(os.path.dirname(__file__), '../../../plugins')
semanticSchemaPath = pluginsRoot + '/SemanticAPI/resources'

Plug.Registry().RegisterPlugins(semanticSchemaPath)
