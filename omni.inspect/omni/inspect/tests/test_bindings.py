"""Suite of tests to exercise the bindings exposed by omni.inspect"""
import omni.kit.test
import omni.inspect as oi

from pathlib import Path
import tempfile


# ==============================================================================================================
class TestOmniInspectBindings(omni.kit.test.AsyncTestCase):
    """Wrapper for tests to verify functionality in the omni.inspect bindings module"""

    # ----------------------------------------------------------------------
    def __test_inspector_api(self, inspector: oi.IInspector):
        """Run tests on flags common to all inspector types
        API surface being tested:
            omni.inspect.IInspector
                @help, help_flag, help_information, is_flag_set, set_flag
        """
        HELP_FLAG = "help"
        HELP_INFO = "This is some help"
        self.assertEqual(inspector.help_flag(), HELP_FLAG)
        self.assertFalse(inspector.is_flag_set(HELP_FLAG))

        inspector.help = HELP_INFO
        self.assertEqual(inspector.help_information(), HELP_INFO)

        inspector.set_flag("help", True)
        self.assertTrue(inspector.is_flag_set(HELP_FLAG))

        inspector.set_flag("help", False)
        inspector.set_flag("Canadian", True)
        self.assertFalse(inspector.is_flag_set(HELP_FLAG))
        self.assertTrue(inspector.is_flag_set("Canadian"))


    # ----------------------------------------------------------------------
    async def test_memory_inspector(self):
        """Test features only available to the memory usage inspector
        API surface being tested:
            omni.inspect.IInspectMemoryUse
                [omni.inspect.IInspector]
                reset, total_used, use_memory
        """
        inspector = oi.IInspectMemoryUse()
        self.__test_inspector_api(inspector)

        self.assertEqual(inspector.total_used(), 0)

        self.assertTrue(inspector.use_memory(inspector, 111))
        self.assertTrue(inspector.use_memory(inspector, 222))
        self.assertTrue(inspector.use_memory(inspector, 333))
        self.assertEqual(inspector.total_used(), 666)

        inspector.reset()
        self.assertEqual(inspector.total_used(), 0)

    # ----------------------------------------------------------------------
    async def test_serializer(self):
        """Test features only available to the shared serializer types
        API surface being tested:
            omni.inspect.IInspectSerializer
                [omni.inspect.IInspector]
                as_string, clear, output_location, output_to_file_path, set_output_to_string, write_string
        """
        inspector = oi.IInspectSerializer()
        self.__test_inspector_api(inspector)

        self.assertEqual(inspector.as_string(), "")

        TEST_STRINGS = [
            "This is line 1",
            "This is line 2",
        ]

        # Test string output
        inspector.write_string(TEST_STRINGS[0])
        self.assertEqual(inspector.as_string(), TEST_STRINGS[0])
        inspector.write_string(TEST_STRINGS[1])
        self.assertEqual(inspector.as_string(), "".join(TEST_STRINGS))
        inspector.clear()
        self.assertEqual(inspector.as_string(), "")

        # Test file output
        with tempfile.TemporaryDirectory() as tmp:
            test_output_file = Path(tmp) / "test_serializer.txt"
            # Get the temp file path and test writing a line to it
            inspector.output_to_file_path = str(test_output_file)
            inspector.write_string(TEST_STRINGS[0])
            self.assertEqual(inspector.as_string(), TEST_STRINGS[0])

            # Set output back to string and check the temp file contents manually
            inspector.set_output_to_string()
            file_contents = open(test_output_file, "r").readlines()
            self.assertEqual(file_contents, [TEST_STRINGS[0]])

    # ----------------------------------------------------------------------
    async def test_json_serializer(self):
        """Test features only available to the JSON serializer type
        API surface being tested:
            omni.inspect.IInspectJsonSerializer
                [omni.inspect.IInspector]
                as_string, clear, close_array, close_object, finish, open_array, open_object, output_location,
                output_to_file_path, set_output_to_string, write_base64_encoded, write_bool,
                write_double, write_float, write_int, write_int64, write_key, write_key_with_length, write_null,
                write_string, write_string_with_length, write_u_int, write_u_int64
        """
        inspector = oi.IInspectJsonSerializer()
        self.__test_inspector_api(inspector)

        self.assertEqual(inspector.as_string(), "")

        self.assertTrue(inspector.open_array())
        self.assertTrue(inspector.close_array())
        self.assertEqual(inspector.as_string(), "[\n]")

        inspector.clear()
        self.assertEqual(inspector.as_string(), "")

        # Note: There's what looks like a bug in the StructuredLog JSON output that omits the space before
        #       a base64_encoded value. If that's ever fixed the first entry in the dictionary will have to change.
        every_type = """
{
    "base64_key":"MTI=",
    "bool_key": true,
    "double_key": 123.456,
    "float_key": 125.25,
    "int_key": -123,
    "int64_key": -123456789,
    "null_key": null,
    "string_key": "Hello",
    "string_with_length_key": "Hell",
    "u_int_key": 123,
    "u_int64_key": 123456789,
    "array": [
        1,
        2,
        3
    ]
}
"""
        def __inspect_every_type():
            """Helper to write one of every type to the inspector"""
            self.assertTrue(inspector.open_object())

            self.assertTrue(inspector.write_key("base64_key"))
            self.assertTrue(inspector.write_base64_encoded(b'1234', 2))

            self.assertTrue(inspector.write_key("bool_key"))
            self.assertTrue(inspector.write_bool(True))

            self.assertTrue(inspector.write_key("double_key"))
            self.assertTrue(inspector.write_double(123.456))

            self.assertTrue(inspector.write_key("float_key"))
            self.assertTrue(inspector.write_float(125.25))

            self.assertTrue(inspector.write_key_with_length("int_key_is_truncated", 7))
            self.assertTrue(inspector.write_int(-123))

            self.assertTrue(inspector.write_key("int64_key"))
            self.assertTrue(inspector.write_int64(-123456789))

            self.assertTrue(inspector.write_key("null_key"))
            self.assertTrue(inspector.write_null())

            self.assertTrue(inspector.write_key("string_key"))
            self.assertTrue(inspector.write_string("Hello"))

            self.assertTrue(inspector.write_key("string_with_length_key"))
            self.assertTrue(inspector.write_string_with_length("Hello World", 4))

            self.assertTrue(inspector.write_key("u_int_key"))
            self.assertTrue(inspector.write_u_int(123))

            self.assertTrue(inspector.write_key("u_int64_key"))
            self.assertTrue(inspector.write_u_int64(123456789))

            self.assertTrue(inspector.write_key("array"))
            self.assertTrue(inspector.open_array())
            self.assertTrue(inspector.write_int(1))
            self.assertTrue(inspector.write_int(2))
            self.assertTrue(inspector.write_int(3))
            self.assertTrue(inspector.close_array())

            self.assertTrue(inspector.close_object())
            self.assertTrue(inspector.finish())

        __inspect_every_type()
        self.assertEqual(inspector.as_string(), every_type)

        # Test file output
        with tempfile.TemporaryDirectory() as tmp:
            test_output_file = Path(tmp) / "test_serializer.txt"
            # Get the temp file path and test writing a line to it
            inspector.output_to_file_path = str(test_output_file)
            __inspect_every_type()
            self.assertEqual(inspector.as_string(), every_type)

            # Set output back to string and check the temp file contents manually
            inspector.set_output_to_string()
            file_contents = [line.rstrip() for line in open(test_output_file, "r").readlines()]
            self.assertCountEqual(file_contents, every_type.split("\n")[:-1])
