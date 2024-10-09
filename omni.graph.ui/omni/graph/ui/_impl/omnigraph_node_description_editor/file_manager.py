"""
Support for all file operations initiated by the Editor interface
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

import omni.graph.tools as ogt
from carb import log_error
from omni.kit.widget.filebrowser import FileBrowserItem
from omni.kit.widget.prompt import Prompt
from omni.kit.window.filepicker import FilePickerDialog

from .ogn_editor_utils import Callback, OptionalCallback, callback_name

# ======================================================================
# Shared set of filters for the open and save dialogs
OGN_FILTERS = [("*.ogn", ".ogn Files (*.ogn)")]


# ======================================================================
class FileManager:
    """Manager of the file interface to .ogn files.

    External Properties:
        ogn_path: Full path to the .ogn file
        ogn_file: File component of ogn_path
        ogn_directory: Directory component of ogn_path

    Internal Properties:
        __controller: Controller class providing write access to the OGN data model
        __current_directory: Directory in which the current file lives.
        __current_file: Name of the .ogn file as of the last open or save. None if the data does not come from a file.
        __open_file_dialog: External window used for opening a new .ogn file
        __save_file_dialog: External window used for saving the .ogn file
        __unsaved_changes: True if there are changes in the file management that require the file to be saved again
    """

    def __init__(self, controller):
        """Set up the default file picker dialogs to be used later"""
        ogt.dbg_ui("Initializing the file manager")
        self.__current_file = None
        self.__current_directory = None
        self.__controller = controller
        self.__unsaved_changes = controller.is_dirty()

        self.__open_file_dialog = None
        self.__save_file_dialog = None

    # ----------------------------------------------------------------------
    def __on_filter_ogn_files(self, item: FileBrowserItem) -> bool:
        """Callback to filter the choices of file names in the open or save dialog"""
        if not item or item.is_folder:
            return True
        ogt.dbg_ui(f"Filtering OGN files on {item.path}")
        # Show only files with listed extensions
        return os.path.splitext(item.path)[1] == ".ogn" and os.path.basename(item.path).startswith("Ogn")

    # ----------------------------------------------------------------------
    def __on_file_dialog_error(self, error: str):
        """Callback executed when there is an error in the file dialogs"""
        log_error(error)

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when the FileManager is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__current_file = None
        self.__current_directory = None
        self.__controller = None
        self.__save_file_dialog = None

    # ----------------------------------------------------------------------
    @property
    def ogn_path(self) -> Optional[str]:
        """Returns the current full path to the .ogn file, None if that path is not fully defined"""
        try:
            return os.path.join(self.__current_directory, self.__current_file)
        except TypeError:
            return None

    # ----------------------------------------------------------------------
    @property
    def ogn_file(self) -> Optional[str]:
        """Returns the name of the current .ogn file"""
        return self.__current_file

    @ogn_file.setter
    def ogn_file(self, new_file: str):
        """Sets a new directory in which the .ogn file will reside. The base name of the file is unchanged"""
        ogt.dbg_ui(f"Setting new FileManager ogn_file to {new_file}")
        if new_file != self.__current_file:
            self.__unsaved_changes = True
            self.__current_file = new_file

    # ----------------------------------------------------------------------
    @property
    def ogn_directory(self) -> Optional[str]:
        """Returns the current directory in which the .ogn file will reside"""
        return self.__current_directory

    @ogn_directory.setter
    def ogn_directory(self, new_directory: str):
        """Sets a new directory in which the .ogn file will reside. The base name of the file is unchanged"""
        ogt.dbg_ui(f"Setting new FileManager ogn_directory to {new_directory}")
        if self.__current_directory != new_directory:
            self.__current_directory = new_directory

    # ----------------------------------------------------------------------
    @staticmethod
    def __on_remove_ogn_file(file_to_remove: str):
        """Callback executed when removal of the file is requested"""
        try:
            os.remove(file_to_remove)
        except Exception as error:  # pylint: disable=broad-except
            log_error(f"Could not remove existing file {file_to_remove} - {error}")

    # ----------------------------------------------------------------------
    def remove_obsolete_file(self, old_file_path: Optional[str]):
        """Check to see if an obsolete file path exists and request deletion if it does"""
        if old_file_path is not None and os.path.isfile(old_file_path):
            old_file_name = os.path.basename(old_file_path)
            Prompt(
                "Remove old file",
                f"Delete the existing .ogn file with the old name {old_file_name}?",
                ok_button_text="Yes",
                cancel_button_text="No",
                cancel_button_fn=self.__on_remove_ogn_file(old_file_path),
                modal=True,
            ).show()

    # ----------------------------------------------------------------------
    def has_unsaved_changes(self) -> bool:
        """Returns True if the file needs to be saved to avoid losing data"""
        return self.__controller.is_dirty() or self.__unsaved_changes

    # ----------------------------------------------------------------------
    def save_failed(self) -> bool:
        """Returns True if the most recent save failed for any reason"""
        return self.has_unsaved_changes()

    # ----------------------------------------------------------------------
    async def __show_prompt_to_save(self, job: Callback):
        """Show a prompt requesting to save the current file.
        If yes then save it and run the job.
        If no then just run the job.
        If cancel then do nothing
        """
        ogt.dbg_ui(f"Showing save prompt with callback {job}")

        Prompt(
            title="Save OGN File",
            text="Would you like to save this file?",
            ok_button_text="Save",
            middle_button_text="Don't Save",
            cancel_button_text="Cancel",
            ok_button_fn=lambda: self.save(on_save_done=lambda *args: job()),
            middle_button_fn=lambda: job() if job is not None else None,
        ).show()

    # ----------------------------------------------------------------------
    def __prompt_if_unsaved_data(self, data_is_dirty: bool, job: Callback):
        """Run a job if there is no unsaved OGN data, otherwise first prompt to save the current data."""
        ogt.dbg_ui("Checking for unsaved data")
        if data_is_dirty:
            asyncio.ensure_future(self.__show_prompt_to_save(job))
        elif job is not None:
            job()

    # ----------------------------------------------------------------------
    def __on_click_open(self, file_name: str, directory_path: str, on_open_done: OptionalCallback):
        """Callback executed when the user selects a file in the open file dialog
        on_open_done() will be executed after the file is opened, if not None
        """
        ogn_path = os.path.join(directory_path, file_name)
        ogt.dbg_ui(f"Trying to open the file {ogn_path}")

        def open_from_ogn():
            """Open the OGN file into the currently managed model.
            Posts an informational dialog if the file could not be opened.
            """
            ogt.dbg_ui(f"Opening data from OGN file {ogn_path} - {callback_name(on_open_done)}")
            try:
                self.__controller.set_ogn_data(ogn_path)
                (self.__current_directory, self.__current_file) = os.path.split(ogn_path)
                if on_open_done is not None:
                    on_open_done()
            except Exception as error:  # pylint: disable=broad-except
                Prompt("Open Error", f"File open failed: {error}", "Okay").show()

        if self.has_unsaved_changes():
            ogt.dbg_ui("...file is dirty, prompting to overwrite")
            asyncio.ensure_future(self.__show_prompt_to_save(open_from_ogn))
        else:
            open_from_ogn()
        self.__open_file_dialog.hide()

    # ----------------------------------------------------------------------
    def open(self, on_open_done: OptionalCallback = None):  # noqa: A003
        """Bring up a file picker to choose a USD file to open.
        If current data is dirty, a prompt will show to let you save it.

        Args:
            on_open_done: Function to call after the open is finished
        """
        ogt.dbg_ui(f"Opening up file open dialog - {callback_name(on_open_done)}")

        def __on_click_cancel(file_name: str, directory_name: str):
            """Callback executed when the user cancels the file open dialog"""
            ogt.dbg_ui("Clicked cancel in file open")
            self.__open_file_dialog.hide()

        if self.__open_file_dialog is None:
            self.__open_file_dialog = FilePickerDialog(
                "Open .ogn File",
                allow_multi_selection=False,
                apply_button_label="Open",
                click_apply_handler=lambda filename, dirname: self.__on_click_open(filename, dirname, on_open_done),
                click_cancel_handler=__on_click_cancel,
                file_extension_options=OGN_FILTERS,
                item_filter_fn=self.__on_filter_ogn_files,
                error_handler=self.__on_file_dialog_error,
            )
        self.__open_file_dialog.refresh_current_directory()
        self.__open_file_dialog.show(path=self.__current_directory)

    # ----------------------------------------------------------------------
    def reset_ogn_data(self):
        """Initialize the OGN content to an empty node."""
        ogt.dbg_ui("Resetting the content")
        self.__controller.set_ogn_data(None)
        self.__current_file = None

    # ----------------------------------------------------------------------
    def new(self):
        """Initialize the OGN content to an empty node.
        If current data is dirty, a prompt will show to let you save it.
        """
        ogt.dbg_ui("Creating a new node")
        self.__prompt_if_unsaved_data(self.has_unsaved_changes(), self.reset_ogn_data)

    # ----------------------------------------------------------------------
    def __save_as_ogn(self, new_ogn_path: str, on_save_done: OptionalCallback):
        """Save the OGN content into the named file.
        Posts an informational dialog if the file could not be saved.
        """
        ogt.dbg_ui(f"Saving OGN to file {new_ogn_path} - {callback_name(on_save_done)}")
        try:
            with open(new_ogn_path, "w", encoding="utf-8") as json_fd:
                json.dump(self.__controller.ogn_data, json_fd, indent=4)
                (self.__current_directory, self.__current_file) = os.path.split(new_ogn_path)
                self.__controller.set_clean()
                self.__unsaved_changes = False
                if on_save_done is not None:
                    on_save_done()
        except Exception as error:  # pylint: disable=broad-except
            Prompt("Save Error", f"File save failed: {error}", "Okay").show()

    # ----------------------------------------------------------------------
    def __on_click_save(self, file_name: str, directory_path: str, on_save_done: OptionalCallback):
        """Save the file, prompting to overwrite if it already exists.

        Args:
            on_save_done: Function to call after save is complete (None if nothing to do)
        """
        (_, ext) = os.path.splitext(file_name)
        if ext != ".ogn":
            file_name = f"{file_name}.ogn"
        new_ogn_path = os.path.join(directory_path, file_name)
        ogt.dbg_ui(f"Saving OGN, checking existence first, to file {new_ogn_path} - {callback_name(on_save_done)}")

        if os.path.exists(new_ogn_path):
            Prompt(
                title="Overwrite OGN File",
                text=f"File {os.path.basename(new_ogn_path)} already exists, do you want to overwrite it?",
                ok_button_text="Yes",
                cancel_button_text="No",
                ok_button_fn=lambda: self.__save_as_ogn(new_ogn_path, on_save_done),
            ).show()
        else:
            self.__save_as_ogn(new_ogn_path, on_save_done)
        self.__save_file_dialog.hide()

    # ----------------------------------------------------------------------
    def save(self, on_save_done: OptionalCallback = None, open_save_dialog: bool = False):
        """Save currently opened OGN data to file. Will call Save As for a newly created file"""
        ogt.dbg_ui(f"Opening up file save dialog - {callback_name(on_save_done)}")

        # If there are no unsaved changes then confirm the file exists to ensure the file system did not delete it
        # and if so then skip the save
        if not self.has_unsaved_changes and os.path.isfile(self.ogn_path):
            ogt.dbg_ui("... file is clean, no need to save")
            return

        def __on_click_cancel(file_name: str, directory_name: str):
            """Callback executed when the user cancels the file save dialog"""
            ogt.dbg_ui("Clicked cancel in file save")
            self.__save_file_dialog.hide()

        if self.ogn_path is None or open_save_dialog:
            if not os.path.isdir(self.__current_directory):
                raise ValueError("Populate extension before saving file")
            ogt.dbg_ui("Opening up the save file dialog")
            if self.__save_file_dialog is None:
                self.__save_file_dialog = FilePickerDialog(
                    "Save .ogn File",
                    allow_multi_selection=False,
                    apply_button_label="Save",
                    click_apply_handler=lambda filename, dirname: self.__on_click_save(filename, dirname, on_save_done),
                    click_cancel_handler=__on_click_cancel,
                    item_filter_fn=self.__on_filter_ogn_files,
                    error_handler=self.__on_file_dialog_error,
                    file_extension_options=OGN_FILTERS,
                    current_file_extension=".ogn",
                )
            self.__save_file_dialog.refresh_current_directory()
            self.__save_file_dialog.show(path=self.__current_directory)
        else:
            ogt.dbg_ui("Saving the file under the existing name")
            self.__save_as_ogn(self.ogn_path, on_save_done)
