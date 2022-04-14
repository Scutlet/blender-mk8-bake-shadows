import bpy

from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty, BoolVectorProperty, PointerProperty
from datetime import datetime

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
    image_name = StringProperty(name="Image Name",
        description="Name of the generated image. It will be replaced if it already exists."
    )

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

    bake_ao = BoolProperty(name="Bake Ambient Occlusion (Red Channel)", default=True)
    bake_shadows = BoolProperty(name="Bake Shadows (Green Channel)", default=True)


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

        # Bake Options
        row = layout.row()
        col = row.column(align=True)
        col.label(text="Bake Options:")
        col.prop(prop, "bake_ao")
        col.prop(prop, "bake_shadows")

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
        print("====================\nMK8 Bake Shadows was started!")
        scene = context.scene

        res_x = scene.mk8bakeshadowsprop.res_x
        res_y = scene.mk8bakeshadowsprop.res_y


        # bpy.ops.object.bake(type="AO", uv_layer=0)

        dt_now = datetime.now()

        image_name = "MK8_Bake1" #+ dt_now.isoformat()
        uv_index = 1





        # # Set bake info
        # context.scene.render.bake_type = "AO"
        # context.scene.render.use_bake_normalize = True
        # print(context.scene.render.bake_samples) # for AO (default 256, [64, 1024])

        # More on light shadows
        # https://docs.blender.org/manual/en/2.79/render/blender_render/lighting/shadows/raytraced_properties.html
        # Shadows should be enabled; constant falloff; more samples ==> better quality; constant > adaptive; soft-size = shadow-gradient size form light to dark

        # Enter object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Bake AO
        img_ao = self.generate_image(context, image_name + "_ao")
        self.select_image_and_uv(context, img_ao, uv_index)
        self.bake(context, bake_type="AO", use_bake_normalize=True)

        # Bake Shadows
        img_shadows = self.generate_image(context, image_name + "_shadow")
        self.select_image_and_uv(context, img_shadows, uv_index)
        self.bake(context, bake_type="SHADOW")

        # Combine bake maps in relevant image channels
        img_combined = self.generate_image(context, image_name)
        self.combine_channels(img_combined, red=img_ao, green=img_shadows, base_red=1.0, base_green=0.745, base_blue=0.0, base_alpha=1.0)

        print("MK8 Bake Shadows has finished!\n====================")
        return {'FINISHED'}

    def generate_image(self, context, image_name):
        """ TODO """
        if image_name not in bpy.data.images:
            # Create a new image if existing one doesn't exist
            bpy.ops.image.new(name=image_name, width=1024, height=1024, alpha=False)
        return bpy.data.images[image_name]

    def select_image_and_uv(self, context, img, uv_index):
        """ TODO """
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
            obj.data.uv_textures[uv_index].active = True

            # Set the target image
            for d in obj.data.uv_textures[uv_index].data:
                d.image = bpy.data.images[img.name]

    def bake(self, context, **kwargs):
        """ TODO """
        render = context.scene.render

        # Set render settings & store old ones
        old_settings = {}
        for setting, val in kwargs.items():
            old_settings[setting] = getattr(render, setting)
            setattr(render, setting, val)

        # Bake the image
        print("Performing %s bake with settings: %s" % (render.bake_type, kwargs))
        bpy.ops.object.bake_image()

        # Cleanup: Restore old render settings
        for setting, val in old_settings.items():
            setattr(render, setting, val)

    def combine_channels(self, img, red=None, green=None, blue=None, alpha=None,
            base_red=1.0, base_green=1.0, base_blue=1.0, base_alpha=1.0):
        """ TODO """
        print("Writing combined channel...")

        # Image editing is slow, so we create a copy of all the pixels first: https://blender.stackexchange.com/a/3678
        #   Using the tuple object is way faster than direct access to Image.pixels
        pixels = list(img.pixels)
        red_channel = red and list(red.pixels)
        green_channel = green and list(green.pixels)
        blue_channel = blue and list(blue.pixels)
        alpha_channel = alpha and list(alpha.pixels)

        # Red Channel
        print("\tWriting red channel...")
        for i in range(0, len(pixels), 4):
            pixels[i] = red_channel[i]

        # Green Channel
        print("\tWriting green channel...")
        for i in range(1, len(pixels), 4):
            pixels[i] = green_channel[i]

        # Blue Channel
        print("\tWriting blue channel...")
        for i in range(2, len(pixels), 4):
            pixels[i] = base_blue

        # Alpha Channel
        print("\tWriting alpha channel...")
        for i in range(3, len(pixels), 4):
            pixels[i] = base_alpha

        # Write back to image (Slice notation here means to replace in-place, not sure if it's faster...)
        img.pixels[:] = pixels

        # Should probably update image
        img.update()

def register():
    """ Runs when enabling the addon """
    print("Enabled MK8 Bake Shadows!")
    import sys
    print(sys.version)

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
