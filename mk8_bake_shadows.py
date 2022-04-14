import bpy

from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, PointerProperty, EnumProperty

bl_info = {
    "name": "Bake MK8 Shadows",
    "description": "Create a bake map for shadows and ambient occlusion for use in Mario Kart 8.",
    "author": "Scutlet",
    "version": (0, 1),
    "blender": (2, 79, 0),
    "location": "Toolshelf > Layers Tab",
    "warning": "This addon is experimental", # Used for warning icon and text in addons panel
    "doc_url": "https://github.com/Scutlet/blender-mk8-bake-shadows",
    "tracker_url": "https://github.com/Scutlet/blender-mk8-bake-shadows/issues",
    "support": "COMMUNITY",
    "category": "Mario Kart 8 Tools"
}

class MK8BakeShadowsProp(PropertyGroup):
    """ Properties for MK8 Bake Shadows """
    image_name = StringProperty(name="Image Name",
        description="Name of the generated image. It will be replaced if it already exists",
        default="MK8_bakemap"
    )

    res_x = IntProperty(name="X",
        description="X Resolution of the image",
        default=1024,
        min=1,
        max=2**31-1,
        soft_min=1,
        soft_max=1024*4,
        step=1,
        subtype='PIXEL'
    )

    res_y = IntProperty(name="Y",
        description="Y Resolution of the image",
        default=1024,
        min=1,
        max=2**31-1,
        soft_min=1,
        soft_max=1024*4,
        step=1,
        subtype='PIXEL'
    )

    do_bake_ao = BoolProperty(name="Ambient Occlusion (Red Channel)", default=True)
    do_bake_shadows = BoolProperty(name="Shadows (Green Channel)", default=True)

    # Bake Options
    bake_margin = IntProperty(name="Margin",
        description="Extends the baked result as a post process filter",
        default=16,
        min=0,
        max=64,
        step=1,
        subtype='PIXEL'
    )

    use_uv_string = BoolProperty(name="Match UV through name", default=False,
        description="Use the selected object's UV map that matches this name. This is not recommended as the bake's UV map should be at index 1 when exporting a model"
    )

    uv_index = IntProperty(name="UV Index",
        description="Index of the UV Map used for baking. Recommended at 1 as that's where the game expects the bake UV Map to be",
        default=1,
        min=0
    )

    uv_name = StringProperty(name="", description="Name of the UV Map used for baking",
        default=""
    )

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

        # Image name
        layout.row().prop(prop, "image_name")

        # Image info
        row = layout.row()
        col = row.column(align=True)
        col.label(text="Image Resolution:")
        col.prop(prop, "res_x")
        col.prop(prop, "res_y")

        # Bake Channel Options
        row = layout.row()
        col = row.column(align=True)
        col.label(text="Bake Channels:")
        col.prop(prop, "do_bake_ao")
        col.prop(prop, "do_bake_shadows")

        # Check if there's a lamp with shadows enabled in the scene
        if prop.do_bake_shadows and not self.exists_shadow_lamp():
            # No such lamp exists; issue a warning
            layout.label("No Lamps with shadows; enable them in a Lamp's properties.", icon="ERROR")

        # Bake Options
        box_bk = layout.box()
        box_bk.row().label(text="Bake Options")

        row = box_bk.row()
        row.prop(prop, "bake_margin")

        # UV Map
        row = box_bk.row()
        row.column(align=True).prop(prop, "use_uv_string")
        col = row.column(align=True)

        if not prop.use_uv_string:
            col.prop(prop, "uv_index")
        else:
            col.prop(prop, "uv_name", icon="GROUP_UVS")

        # Verify UV Map exists for active object
        obj = context.active_object
        if obj.type == 'MESH':
            uv_selection_valid = False
            if not prop.use_uv_string:
                uv_selection_valid = prop.uv_index < len(context.active_object.data.uv_textures)
            else:
                uv_selection_valid = prop.uv_name in context.active_object.data.uv_textures

            if not uv_selection_valid:
                box_bk.row().label("UV Map does not exist for active object", icon="ERROR")
            elif not prop.use_uv_string:
                box_bk.row().label("UV map at this index: %s" % obj.data.uv_textures[prop.uv_index].name, icon="FILE_TICK")

        # This would've been nice, but I can't seem to find a way to list the UV maps of all selected objects
        # objs = context.selected_objects
        # obj = context.active_object
        # if obj is not None and obj.type == 'MESH':
        #     col.prop_search(prop, "uv_name", obj.data, "uv_textures", text="")

        # Bake button
        layout.row().separator()
        layout.row().operator("object.bake_mk8", icon="RENDER_STILL")

    def exists_shadow_lamp(self):
        """ Returns whether there exists at least one lamp casting shadows """
        for lamp in bpy.data.lamps:
            if lamp.shadow_method != 'NOSHADOW':
                return True
        return False

class MK8BakeShadows(bpy.types.Operator):
    """ Bake shadows and ambient occlusion for Mario Kart 8 """ # Tooltip for menu items and buttons.
    bl_idname = "object.bake_mk8"      # Unique identifier for buttons and menu items to reference.
    bl_label = "Bake MK8 Shadows"      # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    def execute(self, context):
        print("====================\nMK8 Bake Shadows was started!")
        scene = context.scene

        image_name = scene.mk8bakeshadowsprop.image_name
        res_x = scene.mk8bakeshadowsprop.res_x
        res_y = scene.mk8bakeshadowsprop.res_y

        do_bake_ao = scene.mk8bakeshadowsprop.do_bake_ao
        do_bake_shadows = scene.mk8bakeshadowsprop.do_bake_shadows

        bake_margin = scene.mk8bakeshadowsprop.bake_margin

        uv_index = scene.mk8bakeshadowsprop.uv_index
        if scene.mk8bakeshadowsprop.use_uv_string:
            uv_index = scene.mk8bakeshadowsprop.uv_name

        # Enter object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Select UV map
        res = self.select_uv(context, uv_index)
        if not res:
            return {'FINISHED'}

        # Bake AO
        img_ao = None
        if do_bake_ao:
            img_ao = self.generate_image(context, image_name + "_ao", width=res_x, height=res_y)
            self.select_image(context, img_ao, uv_index)
            self.bake(context, bake_type="AO", use_bake_normalize=True, bake_margin=bake_margin)

        # Bake Shadows
        img_shadows = None
        if do_bake_shadows:
            img_shadows = self.generate_image(context, image_name + "_shadow", width=res_x, height=res_y)
            self.select_image(context, img_shadows, uv_index)
            self.bake(context, bake_type="SHADOW", bake_margin=bake_margin)

        # Combine bake maps in relevant image channels
        img_combined = self.generate_image(context, image_name, delete_existing=True,
            color=(1.0, 0.745, 0.0, 1.0), width=res_x, height=res_y
        )
        self.combine_channels(img_combined, red=img_ao, green=img_shadows)

        # Select newly baked image
        for area in bpy.context.screen.areas :
            if area.type == 'IMAGE_EDITOR' :
                area.spaces.active.image = img_combined

        self.show_report("Bake complete!")
        print("MK8 Bake Shadows has finished!\n====================")
        return {'FINISHED'}

    def generate_image(self, context, image_name, delete_existing=True, **kwargs):
        """
            Generates a new image or selects one that already has the given name.
            If `delete_existing = True`, it will delete the one that has the given name first.
        """
        if delete_existing and image_name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[image_name])

        if image_name not in bpy.data.images:
            # Create a new image if existing one doesn't exist
            bpy.ops.image.new(name=image_name, alpha=False, **kwargs)
        return bpy.data.images[image_name]

    def select_image(self, context, img, uv_index):
        """ Selects the given image of the given UV Map in the editor so that it can be used in the baking process """
        # Iterate over all selected objects
        for obj in context.selected_objects:
            # Set the target image
            for d in obj.data.uv_textures[uv_index].data:
                d.image = bpy.data.images[img.name]
        return True

    def select_uv(self, context, uv_index):
        """ Selects the given UV Map in the editor such that it can be used in the baking process. Returns True if successful """
        # Iterate over all selected objects
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                # We cannot bake things that aren't meshes
                obj.select = False
                continue

            # Verify UV textures
            is_number = type(uv_index) == int
            if (is_number and uv_index >= len(obj.data.uv_textures)) or (not is_number and uv_index not in obj.data.uv_textures):
                msg = "%s did not have a UVMap at index %s. Unselect the object or add a UV map there" % (obj.name, uv_index)
                self.show_message(title="UV not found", message=msg, icon='ERROR')
                return False

            # Make bake UVs active
            obj.data.uv_textures[uv_index].active = True
        return True

    def bake(self, context, **kwargs):
        """ Bakes to the currently selected image with given settings """
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

    def combine_channels(self, img, red=None, green=None, blue=None, alpha=None):
        """ Combines multiple images each a separate channel in a new image """
        print("Writing combined image...")

        # Image editing is slow, so we create a copy of all the pixels first: https://blender.stackexchange.com/a/3678
        #   Using the tuple object is way faster than direct access to Image.pixels
        pixels = list(img.pixels)

        # Red Channel
        if red is not None:
            print("\tWriting red channel...")
            red_channel = list(red.pixels)
            for i in range(0, len(pixels), 4):
                pixels[i] = red_channel[i]

        # Green Channel
        if green is not None:
            print("\tWriting green channel...")
            green_channel = list(green.pixels)
            for i in range(1, len(pixels), 4):
                pixels[i] = green_channel[i]

        # Blue Channel
        if blue is not None:
            print("\tWriting blue channel...")
            blue_channel = list(blue.pixels)
            for i in range(2, len(pixels), 4):
                pixels[i] = blue_channel[i]

        # Alpha Channel
        if alpha is not None:
            print("\tWriting alpha channel...")
            alpha_channel = list(alpha.pixels)
            for i in range(3, len(pixels), 4):
                pixels[i] = alpha_channel[i]

        # Write back to image (Slice notation here means to replace in-place, not sure if it's faster...)
        img.pixels[:] = pixels

        # Should probably update image
        img.update()

    def show_message(self, message="", title="Message", icon='INFO'):
        """ Shows a popup menu """
        # https://blender.stackexchange.com/questions/109711/how-to-popup-simple-message-box-from-python-console
        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

    def show_report(self, message):
        """ Shows a message in the top panel """
        self.report({'INFO'}, message)


def register():
    """ Runs when enabling the addon """
    print("Enabled MK8 Bake Shadows. Yahooo!")
    bpy.utils.register_class(MK8BakeShadows)
    bpy.utils.register_class(MK8BakeShadowsPanel)
    bpy.utils.register_class(MK8BakeShadowsProp)

    bpy.types.Scene.mk8bakeshadowsprop = PointerProperty(type=MK8BakeShadowsProp)

def unregister():
    """ Runs when disabling the addon """
    print("Disabled MK8 Bake Shadows. Buh-bye!")
    bpy.utils.unregister_class(MK8BakeShadows)
    bpy.utils.unregister_class(MK8BakeShadowsPanel)
    bpy.utils.unregister_class(MK8BakeShadowsProp)
    del bpy.types.Scene.mk8bakeshadowsprop


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
