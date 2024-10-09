"""Testing the stability of the API in this module"""
import omni.graph.core.tests as ogts
import omni.graph.ui as ogu
from omni.graph.tools.tests.internal_utils import _check_module_api_consistency, _check_public_api_contents


# ======================================================================
class _TestOmniGraphUiApi(ogts.OmniGraphTestCase):
    _UNPUBLISHED = ["bindings", "ogn", "tests", "omni"]

    async def test_api(self):
        _check_module_api_consistency(ogu, self._UNPUBLISHED)  # noqa: PLW0212
        _check_module_api_consistency(ogu.tests, is_test_module=True)  # noqa: PLW0212

    async def test_api_features(self):
        """Test that the known public API features continue to exist"""
        _check_public_api_contents(  # noqa: PLW0212
            ogu,
            [
                "add_create_menu_type",
                "build_port_type_convert_menu",
                "ComputeNodeWidget",
                "find_prop",
                "GraphVariableCustomLayout",
                "OmniGraphAttributeModel",
                "OmniGraphTfTokenAttributeModel",
                "OmniGraphBase",
                "OmniGraphPropertiesWidgetBuilder",
                "PrimAttributeCustomLayoutBase",
                "PrimPathCustomLayoutBase",
                "RandomNodeCustomLayoutBase",
                "ReadPrimsCustomLayoutBase",
                "remove_create_menu_type",
                "SETTING_PAGE_NAME",
            ],
            self._UNPUBLISHED,
            only_expected_allowed=True,
        )
        _check_public_api_contents(ogu.tests, [], [], only_expected_allowed=True)  # noqa: PLW0212
