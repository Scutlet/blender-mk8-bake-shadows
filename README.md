# blender-mk8-bake-shadows
A Blender 2.79 addon that bakes shadows of a model for a Mario Kart 8 custom track. It uses the standard baking capabilities of the internal Blender Renderer, making this plugin essentially a partially glorified shortcut that saves several other steps. Furthermore, it combines the results of the bakes in the correct image channels for the game to recognise (ambient occlusion for red, shadows for green).

When importing the resulting bake map in Switch Toolbox, use the *T_BC1_UNORM* or *T_BC1_SRGB* format.

## How to use
After enabling the plugin, a new baking panel can be found in the Render tab in the properties panel.

**Options:**:
- `Image Name`: Name of the generated image. If an image with this name already exists, it is overwritten. Note that there are two additional images that are generated: `<Image Name>_ao` and `<Image Name>_shadow` for the baked ambient occlusion and shadows respectively.
- `Image Resolution`: Width and Height of the image to generate.
- `Bake Channels`: Whether to bake ambient inclusion and/or shadows and to include them in the final combined image.
- `Bake Margin`: The extra space around UV islands to extend the baked result with. Identical to the bake margin in Blender's standard bake option.
- `UV Index`: Index of the UV Map to use during baking. Index 0 is the first UV map of an object. Recommended setting is `1`.
- `Match UV through name`: Use a name to select which of the object's UV maps should be selected. This is not recommended as the game expects the UV map for the baked texture to be at index 1.

### Recommended Lamp Settings
I've personally had success with the following settings for my lamps:
- Lamp > Falloff: Constant
- Shadow > Samples: 10 (the more the slower the render, but the smoother the edges)
- Shadow > Soft Size: 10 (the width of the "gradient" between light and shadows)
- Shadow > Adaptive QMC (Less precise than Constant QMC but way faster)
- Shadow > Threshold: 0.001 (Used for Adaptive QMC. The higher the faster the render, bu the less precise the result)

More information on lamp settings can be found in the [Blender docs](https://docs.blender.org/manual/en/2.79/render/blender_render/lighting/shadows/raytraced_properties.html).

### Troubleshooting
- **UV Map does not exist for active object**: The active object does not have a UV map at the index provided in *UV Index*, or it does not have a UV Map with the name provided at *Match UV through name*.
- **"<X> did not have a UVMap at index <Y>. Unselect the object or add a UV map there"**: Same as above, except for object `<X>` (which was selected).
- **No Lamps with shadows; enable them in a Lamp's properties.**: In order to generate a shadow map, there needs to be at least one lamp in the scene that casts shadows. This error means that such a lamp did not exist. Ensure that (one of) your lamps have their shadows set at the lamp tab in the properties panel.

## Generating a UV Map without merging objects
The *Texture Atlas*-addon ships with Blender 2.79 but is not enabled by default, and allows creating a UV-map of multiple objects without their UV islands overlapping.

Alternatively, *Edit mode* can be accessed in multiple objects at the same time in Blender 2.8+.
