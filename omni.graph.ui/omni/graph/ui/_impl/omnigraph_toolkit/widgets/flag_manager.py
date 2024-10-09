"""Helper to manage a checkbox flag from a list that are attached to various widgets"""
import omni.graph.tools as ogt
import omni.ui as ui


# ==============================================================================================================
class FlagManager:
    """Base class to manage values and checkboxes for flags attached to inspection widgets"""

    FLAG_COLUMN_WIDTH = 80
    """Constant width used for flag checkboxes"""

    def __init__(self, flag_id: str, flag_name: str, flag_tooltip: str, flag_default: bool):
        self.__id = flag_id
        self.__name = flag_name
        self.__tooltip = flag_tooltip
        self.__value = flag_default
        self.__default_value = flag_default
        self.__checkbox = None
        self.__checkbox_model = None

    # --------------------------------------------------------------------------------------------------------------
    def destroy(self):
        ogt.destroy_property(self, "__id")
        ogt.destroy_property(self, "__name")
        ogt.destroy_property(self, "__tooltip")
        ogt.destroy_property(self, "__default_value")
        ogt.destroy_property(self, "__value")
        ogt.destroy_property(self, "__checkbox_model")
        ogt.destroy_property(self, "__checkbox")

    # --------------------------------------------------------------------------------------------------------------
    @property
    def default_value(self) -> str:
        """Returns the default value of this flag as it will be used by the inspector"""
        return self.__default_value

    # --------------------------------------------------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Returns the name of this flag as it will be used by the inspector"""
        return self.__name

    # --------------------------------------------------------------------------------------------------------------
    @property
    def tooltip(self) -> str:
        """Returns the tooltip of this flag as it will be used by the inspector"""
        return self.__tooltip

    # --------------------------------------------------------------------------------------------------------------
    @property
    def is_set(self) -> bool:
        """Returns True if the flag is currently set to True"""
        return self.__value

    # --------------------------------------------------------------------------------------------------------------
    def __on_flag_set(self, mouse_x: int, mouse_y: int, mouse_button: int, value: str):
        """Callback executed when there is a request to change status of one of the inspection flags"""
        if mouse_button == 0:
            new_flag_value = not self.__checkbox.model.as_bool
            self.__value = new_flag_value

    # --------------------------------------------------------------------------------------------------------------
    def checkbox(self):
        """Define the checkbox that manages this flag's value"""
        self.__checkbox_model = ui.SimpleIntModel(self.__value)
        self.__checkbox = ui.CheckBox(
            model=self.__checkbox_model,
            alignment=ui.Alignment.RIGHT_BOTTOM,
            mouse_released_fn=self.__on_flag_set,
            name=self.__id,
            width=0,
            tooltip=self.__tooltip,
            style_type_name_override="WhiteCheck",
        )
        ui.Label(self.__name, alignment=ui.Alignment.LEFT_TOP, width=self.FLAG_COLUMN_WIDTH, tooltip=self.__tooltip)
