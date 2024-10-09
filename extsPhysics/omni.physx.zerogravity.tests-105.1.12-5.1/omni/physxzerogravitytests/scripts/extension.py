import omni.ext
from omni.physxtests import import_tests_auto

import_tests_auto("omni.physxzerogravitytests.scripts", ["tests"])


class ZeroGravityTestExtension(omni.ext.IExt):
    def on_startup(self):
        pass

    def on_shutdown(self):
        pass
