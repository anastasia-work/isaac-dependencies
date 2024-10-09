"""Implementation of a test populator that reads from a file with tests listed in it.
See also the omni.graph.core/tools/log_to_tests.py script, which takes a build log as input and provides a list of
tests contained within it as output.
"""
from __future__ import annotations

from pathlib import Path

import carb
from omni.kit.test import TestPopulator, decompose_test_list
from omni.kit.widget.filebrowser import FileBrowserItem
from omni.kit.window.filepicker import FilePickerDialog


# ==============================================================================================================
class TestPopulateFromFile(TestPopulator):
    """Implementation of the TestUiPopulator that returns a list of all tests listed, one per line, in a text file
    Args:
        _test_file_path: Text file chosen for populating the test list
        _test_file_picker: UI Widget with a file picker for selecting the file containing the tests
    """

    def __init__(self):
        super().__init__(
            "From File",
            "Read tests, one per line containing their fully qualified name, from a text file",
        )
        self._test_file_picker: FilePickerDialog = None
        self._test_file_path: Path = None
        self.tests = {}

    # --------------------------------------------------------------------------------------------------------------
    def destroy(self):
        self._test_file_path = None
        if self._test_file_picker is not None:
            del self._test_file_picker
            self._test_file_picker = None

    # --------------------------------------------------------------------------------------------------------------
    def get_tests(self, call_when_done: callable):
        def __on_click_cancel(file_name: str, directory_name: str):
            """Callback executed when the user cancels the text file open dialog"""
            self._test_file_picker.hide()
            call_when_done(canceled=True)

        def __on_text_file_chosen(filename: str, dirname: str):
            """Callback executed when the user has selected a new text file from which to extract tests"""
            self._test_file_picker.hide()
            if dirname is None or filename is None:
                return
            self._test_file_path = Path(dirname) / filename
            try:
                test_list = []
                with open(self._test_file_path, "r", encoding="utf-8") as test_fd:
                    for line in test_fd:
                        if line.find(".") > 0:
                            test_list.append(line.rstrip())
            except IOError:
                carb.log_warn(f"Test file {self._test_file_path} could not be read to look for tests - ignoring")
                return

            (self.tests, not_found, disabled_extensions, missing_modules) = decompose_test_list(test_list)
            # Inform the user if any tests could not be interpreted according to known extensions.
            if not_found:
                carb.log_warn(f"No information available for {len(not_found)} tests")

            # Inform the user if tests come from known locations in disabled extensions
            if disabled_extensions:
                carb.log_warn(f"Found tests that belong to {len(disabled_extensions)} disabled extensions")

            # Inform the user that although they have extensions enabled containing tests, their tests module has not
            # been imported.
            if missing_modules:
                carb.log_warn(f"Found tests in modules from {len(missing_modules)} extensions that are not imported")

            call_when_done()

        def __on_filter_item(item: FileBrowserItem) -> bool:
            """Filter helper that makes only .txt files show in the text file picker dialog"""
            if not item or item.is_folder:
                return True
            if self._test_file_picker.current_filter_option == 0:
                # Show only files with listed extensions
                return item.path.endswith(".txt")
            # Show All Files (*)
            return True

        if self._test_file_picker is None:
            self._test_file_picker = FilePickerDialog(
                "Select Test File",
                apply_button_label="Select",
                allow_multi_selection=False,
                click_apply_handler=__on_text_file_chosen,
                click_cancel_handler=__on_click_cancel,
                item_filter_options=["All Test Files (*.txt)", "All Files (*.*)"],
                item_filter_fn=__on_filter_item,
                error_handler=carb.log_error,
            )
        else:
            self._test_file_picker.show()
