.. _omni_inspect_ext:

omni.inspect: Omniverse Data Inspector
#######################################

The interfaces in this extension don't do anything themselves, they merely provide a conduit through which other
objects can provide various information through a simple ABI without each object being required to provide the
same inspection interface boilerplate.

The general approach is that you create an inspector, then pass it to an object to be inspected. This model provides
full access to the internal data to the inspector and makes it easy for objects to add inspection capabilities.

Inspecting Data
===============

To add inspection to your data you need two things - an interface to pass the inspector, and an implementation of
the inspection, or inspections. We'll take two imaginary interface types, one of which uses the old Carbonite
interface definitions and one which uses ONI. The interfaces just manage an integer and float value, though the
concept extends to arbitrariliy complex structures.

Carbonite ABI Integer
---------------------

.. code-block:: c++

    // Interface definition --------------------------------------------------

    // Implementation for the integer is just a handle, which is an int*, and the interface pointer
    using IntegerHandle = uint64_t;
    struct IInteger;
    struct IntegerObj
    {
        const IInteger* iInteger;
        IntegerHandle integerHandle;
    };
    struct IInteger
    {
        CARB_PLUGIN_INTERFACE("omni::inspect::IInteger", 1, 0);
        void(CARB_ABI* set)(IntegerObj& intObj, int value) = nullptr;
        bool(CARB_ABI* inspect)(const IntegerObj& intObj, inspect::IInspector* inspector) = nullptr;
    };

    // Interface implementation --------------------------------------------------

    void intSet(IntegerObj& intObj, int value)
    {
        intObj.iInteger->set(intObj, value);
    }
    bool intInspect(const IntegerObj& intObj, inspect::IInspector* inspector)
    {
        // This object can handle both a memory use inspector and a serialization inspector
        auto memoryInspector = omni::cast<inspect::IInspectMemoryUse>(inspector);
        if (memoryInspector)
        {
            // The memory used by this type is just a single integer, and the object itself
            memoryInspector->useMemory((void*)&intObj, sizeof(intObj));
            memoryInspector->useMemory((void*)intObj.integerHandle, sizeof(int));
            return true;
        }
        auto jsonSerializer = omni::cast<inspect::IInspectJsonSerializer>(inspector);
        if (jsonSerializer)
        {
            // Valid JSON requires more than just a bare integer.
            // Indenting on the return value gives you a visual representation of the JSON hierarchy
            if (jsonSerializer->openObject())
            {
                jsonSerializer->writeKey("Integer Value");
                jsonSerializer->writeInt(*(int*)(intObj.integerHandle));
                jsonSerializer->closeObject();
            }
            return true;
        }
        auto serializer = omni::cast<inspect::IInspectSerializer>(inspector);
        if (serializer)
        {
            // The interesting data to write is the integer value, though you could also write the pointer if desired
            serializer->write("Integer value %d", *(int*)(intObj.integerHandle));
            return true;
        }
        // Returning false indicates an unsupported inspector
        return false;
    }

    // Interface use --------------------------------------------------

    IInteger iFace{ intInspect, intSet };
    int myInt{ 0 };
    IntegerObj iObj{ &iFace, (uint64_t)&myInt };


ONI Float
---------

.. code-block:: c++

    // Interface definition --------------------------------------------------

    OMNI_DECLARE_INTERFACE(IFloat);
    class IFloat_abi : public omni::Inherits<omni::core::IObject, OMNI_TYPE_ID("omni.inspect.IFloat")>
    {
    protected:
        virtual void set_abi(float newValue) noexcept = 0;
        virtual void inspect_abi(omni::inspect::IInspector* inspector) noexcept = 0;
    };

    // Interface implementation --------------------------------------------------

    class IFloat : public omni::Implements<IIFloat>
    {
    protected:
        void set_abi(float newvalue) noexcept override
        {
            m_value = value;
        }
    
        bool inspect(omni::inspect::IInspector* inspector) noexcept override
        {
            // This object can handle both a memory use inspector and a serialization inspector
            auto memoryInspector = omni::cast<inspect::IInspectMemoryUse>(inspector);
            if (memoryInspector)
            {
                // The memory used by this type is just the size of this object
                memoryInspector->useMemory((void*)this, sizeof(*this));
                return true;
            }
            auto jsonSerializer = omni::cast<inspect::IInspectJsonSerializer>(inspector);
            if (jsonSerializer)
            {
                // Valid JSON requires more than just a bare float.
                // Indenting on the return value gives you a visual representation of the JSON hierarchy
                if (jsonSerializer->openObject())
                {
                    jsonSerializer->writeKey("Float Value");
                    jsonSerializer->writeFloat(m_value);
                    jsonSerializer->closeObject();
                }
                return true;
            }
            auto serializer = omni::cast<inspect::IInspectSerializer>(inspector);
            if (serializer)
            {
                // The interesting data to write is the float value, though you could also write "this" if desired
                serializer->write("float value %g", m_value);
                return true;
            }
            // Returning false indicates an unsupported inspector
            return false;
        }
    
    private:
        float m_value{ 0.0f };
    };


Calling Inspectors From Python
------------------------------

The inspectors, being ONI objects, have Python bindings so they can be instantiated directly and passed to any of
the interfaces that support them.

.. code-block:: python

    import omni.inspect as oi
    memory_inspector = oi.IInspectMemoryUse()
    my_random_object.inspect(memory_inspector)
    print(f"Memory use is {memory_inspector.get_memory_use()} bytes")

    json_serializer = oi.IInspectJsonSerializer()
    my_random_object.inspect(json_serializer)
    print(f"JSON object:\n{json_serializer.as_string()}" )

    serializer = oi.IInspectSerializer()
    my_random_object.inspect(serializer)
    print(f"Serialized object:\n{serializer.as_string()}" )


omni.inspect Python Docs
========================

.. automodule:: omni.inspect
    :platform: Windows-x86_64, Linux-x86_64, Linux-aarch64
    :members:
    :undoc-members:
    :imported-members:


Administrative Details
======================

.. toctree::
   :maxdepth: 1
   :caption: Administrivia
   :glob:

   CHANGELOG
