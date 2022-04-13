import bpy

from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty, BoolVectorProperty, PointerProperty

bl_info = {
    "name": "Mario Kart 8 - Bake Shadows",
    "author": "Scutlet",
    "version": (0, 1),
    "blender": (2, 79, 0),
    "location": "Toolshelf > Layers Tab",
    "warning": "This addon is experimental", # Used for warning icon and text in addons panel
    # "doc_url": "",
    # "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Mario Kart 8 Tools"
}

# TODO: Support Cycles render

class MK8BakeShadowsProp(PropertyGroup):
    """ Properties for MK8 Bake Shadows """
    float = BoolProperty(name="32 bit Float")

    res_x = IntProperty (name="X",
        description="X Resolution of the image",
        default=1024,
        min=1,
        max=2**31-1,
        soft_min=1,
        soft_max=1024*4,
        step=1,
        subtype='PIXEL'
    )

    res_y = IntProperty (name="Y",
        description="Y Resolution of the image",
        default=1024,
        min=1,
        max=2**31-1,
        soft_min=1,
        soft_max=1024*4,
        step=1,
        subtype='PIXEL'
    )

    bake_shadows = BoolProperty(name="Bake Shadows (Red Channel)", default=True)
    bake_ao = BoolProperty(name="Bake Ambient Occlusion (Green Channel)", default=True)


class MK8BakeShadowsPanel(bpy.types.Panel):
    """ Panel for MK8 Bake Shadows """
    bl_label = "Mario Kart 8 - Bake Shadows"
    bl_idname = "RENDER_PT_MK8_Bake_Shadows"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        prop = context.scene.mk8bakeshadowsprop

        # Image info
        row = layout.row()
        col = row.column(align=True)
        col.label(text="Image Resolution:")
        col.prop(prop, "res_x")
        col.prop(prop, "res_y")
        col.prop(prop, "float")

        # Bake Options
        row = layout.row()
        col = row.column(align=True)
        col.label(text="Bake Options:")
        col.prop(prop, "bake_shadows")
        col.prop(prop, "bake_ao")

        # # UV Override
        # split = layout.split(percentage=0.3)
        # split.label(text="UV Map (Active Object):")
        # obj = context.scene.objects.active
        # split.prop_search(tex, "uv_layer", ob.data, "uv_textures", text="")

        row = layout.row()
        row.operator("object.bake_mk8")


class MK8BakeShadows(bpy.types.Operator):
    """ Bake shadows and ambient occlusion for Mario Kart 8 """ # Tooltip for menu items and buttons.
    bl_idname = "object.bake_mk8"      # Unique identifier for buttons and menu items to reference.
    bl_label = "Bake MK8 Shadows"      # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    def execute(self, context):
        scene = context.scene

        res_x = scene.mk8bakeshadowsprop.res_x
        res_y = scene.mk8bakeshadowsprop.res_y
        float = scene.mk8bakeshadowsprop.float


        # bpy.ops.object.bake(type="AO", uv_layer=0)

        image_name = "MK8 Shadows"
        uv_index = 1

        # Find bake image
        img = next((img for img in bpy.data.images if img.name == image_name), None)
        if img is None:
            # Create a new image if existing one doesn't exist
            img = bpy.ops.image.new(name=image_name, width=1024, height=1024, alpha=False)

        # Set bake info
        context.scene.render.bake_type = "AO"
        context.scene.render.use_bake_normalize = True

        # Exit edit mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Iterate over all selected objects
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                # We cannot bake things that aren't meshes
                obj.select = False
                continue

            # Verify UV textures
            if len(obj.data.uv_textures) < uv_index:
                raise IndexError("%s did not have a UVMap at index %s. Unselect it or add a UV map there" % (obj.name, uv_index))

            # Make bake UVs active
            obj.data.uv_textures[1].active = True

            # Set the target image
            for d in obj.data.uv_textures[1].data:
                d.image = bpy.data.images[image_name]

        # Bake the image
        bpy.ops.object.bake_image()

        return {'FINISHED'}


def register():
    """ Runs when enabling the addon """
    print("Enabled MK8 Bake Shadows!")
    bpy.utils.register_class(MK8BakeShadows)
    bpy.utils.register_class(MK8BakeShadowsPanel)
    bpy.utils.register_class(MK8BakeShadowsProp)

    bpy.types.Scene.mk8bakeshadowsprop = PointerProperty(type=MK8BakeShadowsProp)


def unregister():
    """ Runs when disabling the addon """
    print("Disabled MK8 Bake Shadows!")
    bpy.utils.unregister_class(MK8BakeShadows)
    bpy.utils.unregister_class(MK8BakeShadowsPanel)
    bpy.utils.unregister_class(MK8BakeShadowsProp)
    del bpy.types.Scene.mk8bakeshadowsprop


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
