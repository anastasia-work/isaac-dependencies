(changelog_omni_graph_ui)=

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.48.0] - 2023-09-12
### Changed
- Don't require omni.kit.window.extensions. Only enable the bits which use it if it's already loaded.

## [1.47.0] - 2023-08-28
### Changed
- Modified extension to explicitly target the kit version.
- Changed version # to be greater than the last untargeted version published out of kit-omnigraph.

## [1.46.5] - 2023-08-21
### Changed
- Use platform-agnostic omni.kit.clipboard instead of pyperclip

## [1.46.2] - 2023-06-27
### Fixed
- Fixed some documentation nits

## [1.46.1] - 2023-06-12
### Changed
- Fixed one deprecated ogt.OmniGraphExtension reference which was missed.

## [1.46.0] - 2023-06-08
### Changed
- Remove widget for input bundle

## [1.45.3] - 2023-06-08
### Changed
- Replaced load-time dependency on omni.kit.window.tests with a runtime dependency

## [1.45.2] - 2023-05-29
### Changed
- Replaced deprecated calls with supported versions

## [1.45.1] - 2023-05-26
### Added
- Added test for layer identifier property widget.

## [1.45.0] - 2023-05-23
### Removed
- Removed OG settings that were referencing now-removed constructs (dynamic scheduler and realm static scheduler).

## [1.44.2] - 2023-05-17
### Changed
- Updated tests to work with ReadPrimsV2 node.

## [1.44.1] - 2023-05-17
### Fixed
- read/write prim attribute name widget shows graph attributes when targeting instanced prim

## [1.44.0] - 2023-05-11
### Added
- OmniGraphTfTokenNoAllowedTokensModel to handle tokens as asset-paths
### Changed
- OG property panel widgets now commit changes on end-edit instead of every change for string/token

## [1.43.0] - 2023-05-08
### Deprecated
- Removed deprecated locations of Python modules

## [1.42.1] - 2023-05-05
### Changed
- Updated `ReadPrims` related tests during to node inputs changes.

## [1.42.0] - 2023-05-04
### Changed
- Filter out problematic event types in on_graph_event

## [1.41.0] - 2023-04-26
### Changed
- Fix wording of bundle/target tooltip
- Fix unresolved attribute label

## [1.40.3] - 2023-04-24
### Changed
- Read/WritePrimAttribute nodes will find attribute names when prim or primPath is connected

## [1.40.2] - 2023-04-24
### Fixed
- Replaced deprecated call to get_elem_count

## [1.40.1] - 2023-04-21
### Fixed
- target property widget without template

## [1.40.0] - 2023-04-20
### Added
- Reset menu item for type-conversion menu

## [1.39.0] - 2023-04-17
### Changed
- target attributes now show instancing target path as relative to symbol

## [1.38.5] - 2023-04-12
### Changed
- Created template class for nodes with prim/primPath structure
- Changed bundle buttons in UI to say "Bundle(s)"

## [1.38.4] - 2023-04-11
### Fixed
- Prim node template allows text editing when non-valid prim is selected

## [1.38.3] - 2023-04-11
### Removed
- Removed node documentation TODO which is no longer relevant

## [1.38.2] - 2023-04-03
### Fixed
- Fixed incorrect object in template
### Added
- Added test for property window output extended attributes

## [1.38.1] - 2023-04-03
### Changed
- Added timcode to read/write prim Inputs group
- Name consistency pass

## [1.38.0] - 2023-04-03
### Added
- Support for picking graph-instancing-target

## [1.37.4] - 2023-03-31
### Changed
- output and state target attributes show values not target inputs
- Relationship attributes now are sorted into thier respective port display group

## [1.37.3] - 2023-03-30
### Changed
- Target widget shows as readonly when port is connected

## [1.37.2] - 2023-03-24
### Fixed
- Fix no len() exception when showing Quat attributes

## [1.37.1] - 2023-03-24
### Changed
- Graph instance variable now show warning when there is a type mismatch

## [1.37.0] - 2023-03-24
### Changed
- Updated Camera, picking nodes to use new target type for prim input
### Fixed
- Fixed ReadPrimAttributes property panel throwing errors

## [1.36.0] - 2023-03-24
### Added
- New button to access the Fabric inspector
### Removed
- Obsolete flags for dumping Fabric data from the graph

## [1.35.2] - 2023-03-16
### Added
- "threadsafe" scheduling hints to OgnGetCameraPosition, OgnGetCameraTarget, OgnOnPicked, OgnOnViewportClicked, OgnOnViewportDragged, OgnOnViewportHovered, OgnOnViewportPressed, OgnOnViewportScrolled, OgnReadMouseState, OgnReadPickState, OgnReadViewportClickState, OgnReadPickState, OgnReadViewportClickState, OgnReadViewportDragState, OgnReadViewportHoverState, OgnReadViewportPressState, and OgnReadViewportScrollState nodes.
- "usd-write" scheduling hint to OgnSetViewportFullscreen node.

## [1.35.1] - 2023-03-09
### Fixed
- Check component index is valid when comparing values

## [1.35.0] - 2023-03-10
### Changed
- Moved all nodes out of this extension, into omni.graph.ui_nodes

## [1.34.3] - 2023-03-09
### Added
- Change default index for static version of internal state to be the authoring graph
- Add wrappers for shared and per-instance state query functions

## [1.34.2] - 2023-03-08
### Fixed
- Fix exception when bringing up the attribute context menu on a non-node attribute.

## [1.34.1] - 2023-03-06
### Fixed
- Fix exceptions from property widget when multi-selecting certain node types

## [1.34.0] - 2023-03-06
### Changed
- Removed the warning about nodes being incompatible with instancing

## [1.33.2] - 2023-02-28
### Fixed
- OmniUiTest-based tests close any stages they open to avoid dangling graph references which crash on exit.

## [1.33.1] - 2023-02-25
### Changed
- Modifed format of Overview to be consistent with the rest of Kit

## [1.33.0] - 2023-02-24
### Added
- build_port_type_convert_menu
- property panel context menu for converting extended types

## [1.32.1] - 2023-02-22
### Added
- Links to JIRA tickets regarding filling in the missing documentation

## [1.32.0] - 2023-02-21
### Changed
- Added usdWriteBack to WritePrimAttribute

## [1.31.4] - 2023-02-21
### Changed
- Change ComputeNodeWidget label to reflect node type

## [1.31.3] - 2023-02-20
### Changed
- Made the interfaces subproject unique to omni.graph.ui

## [1.31.2] - 2023-02-19
### Changed
- Added label to the main doc page so that higher level docs can reference the extension
- Tagged for adding links to node documentation

## [1.31.1] - 2023-02-05
### Added
- Add property filter support

## [1.31.0] - 2023-02-15
### Changed
- unconnected token input arrays can be edited with property panel
### Fixed
- Don't error on default value of NaN for float inputs

## [1.30.2] - 2023-02-13
### Changed
- Runtime initialization for the `inputs:renderer` attribute of `OgnSetViewportRenderer`

## [1.30.1] - 2023-02-10
### Changed
- Correct namespace of `OgnSetViewportFullscreen`

## [1.30.0] - 2023-02-09
### Added
- Added `OgnSetViewportFullscreen`
- Added `OgnSetViewportRenderer` and `OgnGetViewportRenderer`
- Added `OgnSetViewportResolution` and `OgnGetViewportResolution`

## [1.29.3] - 2023-02-06
### Fixed
- Bug in property panel when setting resolved attribute values

## [1.29.2] - 2023-02-02
### Fixed
- Lint error that appeared when pylint updated

## [1.29.1] - 2023-01-30
### Changed
- Removed the kit-sdk landing page
- Moved all of the documentation into the new omni.graph.docs extension

## [1.29.0] - 2023-01-11
### Changed
- ABI calls to take into account instancing
- Changes related to introduction of native vectorization in core

## [1.28.4] - 2022-12-28
### Changed
- Changed the way errors and warnings are surfaced to OgnReadWidgetProperty/OgnWriteWidgetProperty

## [1.28.3] - 2022-12-07
### Fixed
- Make sure variable colour widgets use AbstractItemModel

## [1.28.2] - 2022-12-05
### Fixed
- Fixed tab not working on variable vector fields

## [1.28.1] - 2022-12-05
### Fixed
- Fixed UI update issues with graph variable widgets

## [1.28.0] - 2022-11-24
### Removed
- Widget controlling the deleted setting useSchemaPrims

## [1.27.0] - 2022-11-17
### Removed
- Widget controlling the deleted settings updateToUSD, useLegacySimulationPipeline and enableUSDInPreRender

## [1.26.0] - 2022-11-12
### Removed
- Widget controlling the deleted implicit global graph setting

## [1.25.0] - 2022-11-02
### Added
- Display initial and runtime values of graph variables

## [1.24.1] - 2022-10-28
### Fixed
- Undo on node attributes

## [1.24.0] - 2022-10-20
### Added
- Custom Property Panel for OmniGraphCompoundNodeType schema Prims

## [1.23.0] - 2022-09-28
### Added
- Widget for reporting timing information related to extension processing by OmniGraph

## [1.22.2] - 2022-09-19
### Added
- Use id paramteter for Viewport picking request so a node will only generate request.

## [1.22.1] - 2022-09-09
### Added
- Instance variable properties remove underlying attribute when reset to default

## [1.22.0] - 2022-08-31
### Changed
- Added OmniGraphAttributeModel to public API

## [1.21.1] - 2022-08-19
### Changed
- Added OnVariableChange to the list of instancing-compatible ndoes

## [1.21.0] - 2022-08-19
### Added
- UI for controlling new setting that turns deprecations into errors

## [1.20.1] - 2022-08-17
### Changed
- Refactored scene frame to be widget-based instead of monolithic

## [1.20.0] - 2022-08-16
### Fixed
- Modified the import path acceptance pattern to adhere to PEP8 guidelines
- Fixed hot reload for the editors by correctly destroying menu items
- Added FIXME comments recommended in a prior review
### Added
- Button for Save-As to support being able to add multiple nodes in a single session

## [1.19.0] - 2022-08-11
### Added
- ReadWindowSize node
- 'widgetPath' inputs to ReadWidgetProperty, WriteWidgetProperty and WriteWidgetStyle nodes.
### Changed
- WriteWidgetStyle now reports the full details of style sytax errors.

## [1.18.1] - 2022-08-10
### Fixed
- Applied formatting to all of the Python files

## [1.18.0] - 2022-08-09
### Changed
- Removed unused graph editor modules
- Removed omni.kit.widget.graph and omni.kit.widget.fast_search dependencies

## [1.17.1] - 2022-08-06
### Changed
- OmniGraph(API) references changed to 'Visual Scripting'

## [1.17.0] - 2022-08-05
### Added
- Mouse press gestures to picking nodes

## [1.16.4] - 2022-08-05
### Changed
- Fixed bug related to parameter-tagged properties

## [1.16.3] - 2022-08-03
### Fixed
- All of the lint errors reported on the Python files in this extension

## [1.16.2] - 2022-07-28
### Fixed
- Spurious error messages about 'Node compute request is ignored because XXX is not request-driven'

## [1.16.1] - 2022-07-28
### Changed
- Fixes for OG property panel
- compute_node_widget no longer flushes prim to FC

## [1.16.0] - 2022-07-25
### Added
- Viewport mouse event nodes for click, press/release, hover, and scroll
### Changed
- Behavior of drag and picking nodes to be consistent

## [1.15.3] - 2022-07-22
### Changed
- Moving where custom metadata is set on the usd property so custom templates have access to it

## [1.15.2] - 2022-07-15
### Added
- test_omnigraph_ui_node_creation()
### Fixed
- Missing graph context in test_open_and_close_all_omnigraph_ui()
### Changed
- Set all of the old Action Graph Window code to be omitted from pyCoverage

## [1.15.1] - 2022-07-13
- OM-55771: File browser button

## [1.15.0] - 2022-07-12
### Added
- OnViewportDragged and ReadViewportDragState nodes
### Changed
- OnPicked and ReadPickState, most importantly how OnPicked handles an empty picking event

## [1.14.0] - 2022-07-08
### Fixed
- ReadMouseState not working with display scaling or multiple workspace windows
### Changed
- Added 'useRelativeCoordinates' input and 'window' output to ReadMouseState

## [1.13.0] - 2022-07-08
### Changed
- Refactored imports from omni.graph.tools to get the new locations
### Added
- Added test for public API consistency

## [1.12.0] - 2022-07-07
### Changed
- Overhaul of SetViewportMode
- Changed default viewport for OnPicked/ReadPickState to 'Viewport'
- Allow templates in omni.graph.ui to be loaded

## [1.11.0] - 2022-07-04
### Added
- OgnSetViewportMode.widgetPath attribute
### Changed
- OgnSetViewportMode does not enable execOut if there's an error

## [1.10.1] - 2022-06-28
### Changed
- Change default viewport for SetViewportMode/OnPicked/ReadPickState to 'Viewport Next'

## [1.10.0] - 2022-06-27
### Changed
- Move ReadMouseState into omni.graph.ui
- Make ReadMouseState coords output window-relative

## [1.9.0] - 2022-06-24
### Added
- Added PickingManipulator for prim picking nodes controlled from SetViewportMode
- Added OnPicked and ReadPickState nodes for prim picking

## [1.8.5] - 2022-06-17
### Added
- Added instancing ui elements

## [1.8.4] - 2022-06-07
### Changed
- Updated imports to remove explicit imports
- Added explicit generator settings

## [1.8.3] - 2022-05-24
### Added
- Remove dependency on Viewport for Camera Get/Set operations
- Run tests with omni.hydra.pxr/Storm instead of RTX

## [1.8.2] - 2022-05-23
### Added
- Use omni.kit.viewport.utility for Viewport nodes and testing.

## [1.8.1] - 2022-05-20
### Fixed
- Change cls.default_model_table to correctly set model_cls in _create_color_or_drag_per_channel
 for vec2d, vec2f, vec2h, and vec2i omnigraph attributes
- Infer default values from type for OG attributes when not provided in metadata

## [1.8.0] - 2022-05-05
### Added
- Support for enableLegacyPrimConnections setting, used by DS but deprecated
### Fixed
- Tooltips and descriptions for settings that are interdependent

## [1.7.1] - 2022-04-29
### Changed
- Made tests derive from OmniGraphTestCase

## [1.7.0] - 2022-04-26
### Added
- GraphVariableCustomLayout property panel widget moved from omni.graph.instancing

## [1.6.1] - 2022-04-21
### Fixed
- Some broken and out of date tests.

## [1.6.0] - 2022-04-18
### Changed
- Property Panel widget for OG nodes now reads attribute values from Fabric backing instead of USD.

## [1.5.0] - 2022-03-17
### Added
- Added _add\_create\_menu\_type_ and _remove\_create\_menu\_type_ functions to allow kit-graph extensions to add their corresponding create graph menu item
### Changed
- _Menu.create\_graph_ now return the wrapper node, and will no longer pops up windows
- _Menu_ no longer creates the three menu items _Create\Visual Sciprting\Action Graph_, _Create\Visual Sciprting\Push Graph_, _Create\Visual Sciprting\Lazy Graph_ at extension start up
- Creating a graph now will directly create a graph with default title and open it

## [1.4.4] - 2022-03-11
### Added
- Added glyph icons for menu items _Create/Visual Scripting/_ and items under this submenu
- Added Create Graph context menu for viewport and stage windows.

## [1.4.3] - 2022-03-11
### Fixed
- Node is written to backing store when the custom widget is reset to ensure that view is up to date with FC.

## [1.4.2] - 2022-03-07
### Changed
- Add spliter for items in submenu _Window/Visual Scripting_
- Renamed menu item _Create/Graph_ to _Create/Visual Scripting_
- Changed glyph icon for _Create/Visual Scripting_ and added glyph icons for all sub menu items under

## [1.4.1] - 2022-02-22
### Changed
- Change _Window/Utilities/Attribute Connection_, _Window/Visual Scripting/Node Description Editor_ and _Window/Visual Scripting/Toolkit_ into toggle buttons
- Added OmniGraph.svg glyph for _Create/Graph_

## [1.4.0] - 2022-02-16
### Changes
- Decompose the original OmniGraph menu in toolbar into several small menu items under correct categories

## [1.3.0] - 2022-02-10
### Added
- Toolkit access to the setting that uses schema prims in graphs, and a migration tool for same

## [1.2.2] - 2022-01-28
### Fixed
- Potential crash when handling menu or stage changes

## [1.2.1] - 2022-01-21
### Fixed
- ReadPrimAttribute/WritePrimAttribute property panel when usePath is true

## [1.2.0] - 2022-01-06
### Fixed
- Property window was generating exceptions when a property is added to an OG prim.

## [1.1.0] - 2021-12-02
### Changes
- Fixed compute node widget bug with duplicate graphs

## [1.0.2] - 2021-11-24
### Changes
- Fixed compute node widget to work with scoped graphs
## [1.0.1] - 2021-02-10
### Changes
- Updated StyleUI handling

## [1.0.0] - 2021-02-01
### Initial Version
- Started changelog with initial released version of the OmniGraph core
