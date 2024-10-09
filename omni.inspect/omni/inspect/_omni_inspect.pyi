from __future__ import annotations
import omni.inspect._omni_inspect
import typing
import omni.core._core

__all__ = [
    "IInspectJsonSerializer",
    "IInspectMemoryUse",
    "IInspectSerializer",
    "IInspector"
]


class IInspectJsonSerializer(_IInspectJsonSerializer, IInspector, _IInspector, omni.core._core.IObject):
    """
    Base class for object inspection requests.
    """
    @typing.overload
    def __init__(self, arg0: omni.core._core.IObject) -> None: ...
    @typing.overload
    def __init__(self) -> None: ...
    def as_string(self) -> str: 
        """
        Get the current output as a string. If the output is being sent to a file path then read the file at that path
        and return the contents of the file (with the usual caveats about file size).

        @returns String representation of the output so far
        """
    def clear(self) -> None: 
        """
        Clear the contents of the serializer output, either emptying the file or clearing the string, depending on
        where the current output is directed.
        """
    def close_array(self) -> bool: 
        """
        Finish writing a JSON array.

        @returns whether or not validation succeeded.
        """
    def close_object(self) -> bool: 
        """
        Finish writing a JSON object.

        @returns whether or not validation succeeded.
        """
    def finish(self) -> bool: 
        """
        Finishes writing the entire JSON dictionary.

        @returns whether or not validation succeeded.
        """
    def open_array(self) -> bool: 
        """
        Begin a JSON array.

        @returns whether or not validation succeeded.
        @note This may throw a std::bad_alloc or a std::length_error if the stack of scopes gets too large
        """
    def open_object(self) -> bool: 
        """
        Begin a JSON object.

        @returns whether or not validation succeeded.
        """
    def set_output_to_string(self) -> None: 
        """
        Set the output location of the serializer data to be a local string.
        No check is made to ensure that the string size doesn't get too large so when in doubt use a file path.
        """
    def write_base64_encoded(self, value: bytes, size: int) -> bool: 
        """
        Write a set of bytes into the output JSON as a base64 encoded string.

        @param[in] value The bytes to be written.
        @param[in] size  The number of bytes of data in @p value.
        @returns whether or not validation succeeded.
        @remarks This will take the input bytes and encode it in base64, then store that as base64 data in a string.
        """
    def write_bool(self, value: bool) -> bool: 
        """
        Write out a JSON boolean value.

        @param[in] value The boolean value.
        @returns whether or not validation succeeded.
        """
    def write_double(self, value: float) -> bool: 
        """
        Write out a JSON double (aka number) value.

        @param[in] value The double value.
        @returns whether or not validation succeeded.
        """
    def write_float(self, value: float) -> bool: 
        """
        Write out a JSON float (aka number) value.

        @param[in] value The double value.
        @returns whether or not validation succeeded.
        """
    def write_int(self, value: int) -> bool: 
        """
        Write out a JSON integer value.

        @param[in] value The integer value.
        @returns whether or not validation succeeded.
        """
    def write_int64(self, value: int) -> bool: 
        """
        Write out a JSON 64-bit integer value.

        @param[in] value The 64-bit integer value.
        @returns whether or not validation succeeded.
        @note 64 bit integers will be written as a string of they are too long
        to be stored as a number that's interoperable with javascript's
        double precision floating point format.
        """
    def write_key(self, key: str) -> bool: 
        """
        Write out a JSON key for an object property.

        @param[in] key The key name for this property. This may be nullptr.
        @returns whether or not validation succeeded.
        """
    def write_key_with_length(self, key: str, key_len: int) -> bool: 
        """
        Write out a JSON key for an object property.

        @param[in] key    The string value for the key. This can be nullptr.
        @param[in] keyLen The length of @ref key, excluding the null terminator.
        @returns whether or not validation succeeded.
        """
    def write_null(self) -> bool: 
        """
        Write out a JSON null value.

        @returns whether or not validation succeeded.
        """
    def write_string(self, value: str) -> bool: 
        """
        Write out a JSON string value.

        @param[in] value The string value. This can be nullptr.
        @returns whether or not validation succeeded.
        """
    def write_string_with_length(self, value: str, len: int) -> bool: 
        """
        Write out a JSON string value.

        @param[in] value The string value. This can be nullptr if @p len is 0.
        @param[in] len   The length of @p value, excluding the null terminator.
        @returns whether or not validation succeeded.
        """
    def write_u_int(self, value: int) -> bool: 
        """
        Write out a JSON unsigned integer value.

        @param[in] value The unsigned integer value.
        @returns whether or not validation succeeded.
        """
    def write_u_int64(self, value: int) -> bool: 
        """
        Write out a JSON 64-bit unsigned integer value.

        @param[in] value The 64-bit unsigned integer value.
        @returns whether or not validation succeeded.
        @note 64 bit integers will be written as a string of they are too long
        to be stored as a number that's interoperable with javascript's
        double precision floating point format.
        """
    @property
    def output_location(self) -> str:
        """
        :type: str
        """
    @property
    def output_to_file_path(self) -> None:
        """
        :type: None
        """
    @output_to_file_path.setter
    def output_to_file_path(self, arg1: str) -> None:
        pass
    pass
class IInspectMemoryUse(_IInspectMemoryUse, IInspector, _IInspector, omni.core._core.IObject):
    """
    Base class for object inspection requests.
    """
    @typing.overload
    def __init__(self, arg0: omni.core._core.IObject) -> None: ...
    @typing.overload
    def __init__(self) -> None: ...
    def reset(self) -> None: 
        """
        Reset the memory usage data to a zero state
        """
    def total_used(self) -> int: 
        """
        @returns the total number of bytes of memory used since creation or the last call to reset().
        """
    def use_memory(self, ptr: capsule, bytes_used: int) -> bool: 
        """
        Add a block of used memory
        Returns false if the memory was not recorded (e.g. because it was already recorded)

        @param[in] ptr Pointer to the memory location being logged as in-use
        @param[in] bytesUsed Number of bytes in use at that location
        """
    pass
class IInspectSerializer(_IInspectSerializer, IInspector, _IInspector, omni.core._core.IObject):
    """
    Base class for object serialization requests.
    """
    @typing.overload
    def __init__(self, arg0: omni.core._core.IObject) -> None: ...
    @typing.overload
    def __init__(self) -> None: ...
    def as_string(self) -> str: 
        """
        Get the current output as a string.

        @returns The output that has been sent to the serializer. If the output is being sent to a file path then read
        the file at that path and return the contents of the file. If the output is being sent to stdout or stderr
        then nothing is returned as that output is unavailable after flushing.
        """
    def clear(self) -> None: 
        """
        Clear the contents of the serializer output, either emptying the file or clearing the string, depending on
        where the current output is directed.
        """
    def set_output_to_string(self) -> None: 
        """
        Set the output location of the serializer data to be a local string.
        No check is made to ensure that the string size doesn't get too large so when in doubt use a file path.
        """
    def write_string(self, to_write: str) -> None: 
        """
        Write a fixed string to the serializer output location

        @param[in] toWrite String to be written to the serializer
        """
    @property
    def output_location(self) -> str:
        """
        :type: str
        """
    @property
    def output_to_file_path(self) -> None:
        """
        :type: None
        """
    @output_to_file_path.setter
    def output_to_file_path(self, arg1: str) -> None:
        pass
    pass
class _IInspectJsonSerializer(IInspector, _IInspector, omni.core._core.IObject):
    pass
class _IInspectMemoryUse(IInspector, _IInspector, omni.core._core.IObject):
    pass
class _IInspectSerializer(IInspector, _IInspector, omni.core._core.IObject):
    pass
class IInspector(_IInspector, omni.core._core.IObject):
    """
    Base class for object inspection requests.
    """
    @typing.overload
    def __init__(self, arg0: omni.core._core.IObject) -> None: ...
    @typing.overload
    def __init__(self) -> None: ...
    def help_flag(self) -> str: 
        """
        Returns the common flag used to tell the inspection process to put the help information into the
        inspector using the setHelp_abi function. Using this approach avoids having every inspector/object
        combination add an extra ABI function just for retrieving the help information, as well as providing a
        consistent method for requesting it.
        @returns String containing the name of the common flag used for help information
        """
    def help_information(self) -> str: 
        """
        Returns the help information currently available on the inspector. Note that this could change
        from one invocation to the next so it's important to read it immediately after requesting it.
        @returns String containing the help information describing the current configuration of the inspector
        """
    def is_flag_set(self, flag_name: str) -> bool: 
        """
        Checks whether a particular flag is currently set or not.
        @param[in] flagName Name of the flag to check
        @returns True if the named flag is set, false if not
        """
    def set_flag(self, flag_name: str, flag_state: bool) -> None: 
        """
        Enable or disable an inspection flag. It's up to the individual inspection operations or the derived
        inspector interfaces to interpret the flag.
        @param[in] flagName Name of the flag to set
        @param[in] flagState New state for the flag
        """
    @property
    def help(self) -> None:
        """
        :type: None
        """
    @help.setter
    def help(self, arg1: str) -> None:
        pass
    pass
class _IInspector(omni.core._core.IObject):
    pass
