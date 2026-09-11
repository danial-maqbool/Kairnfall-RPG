"""Fast Blender Workbench entry point for Kairnfall humanoid sprite rendering.

The full 3D geometry, materials, rig poses, face parts, hair, clothing and armour
come from blender_humanoid_batch.py. This entry point changes only the renderer:
Workbench gives crisp studio-lit 3D form at 64 px without the expensive Eevee
sampling that is unnecessary after pixel quantization.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import bpy

HERE = Path(__file__).resolve().parent
BATCH_PATH = HERE / "blender_humanoid_batch.py"
SPEC = importlib.util.spec_from_file_location("kairnfall_blender_humanoid_batch", BATCH_PATH)
batch = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = batch
SPEC.loader.exec_module(batch)


def setup_workbench_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = batch.FRAME
    scene.render.resolution_y = batch.FRAME
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    scene.render.filter_size = 0.35
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "MATERIAL"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "WORLD"
    shading.curvature_ridge_factor = 1.35
    shading.curvature_valley_factor = 1.10
    shading.show_specular_highlight = True
    shading.background_type = "WORLD"

    world = bpy.data.worlds.new("Kairnfall Workbench World") if not bpy.data.worlds else bpy.data.worlds[0]
    scene.world = world
    world.color = (0.12, 0.13, 0.15)

    bpy.ops.object.camera_add(location=(0.0, -18.0, 6.8))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 9.6
    batch.look_at(camera, (0.0, 0.0, 3.15))
    scene.camera = camera
    return scene


batch.setup_scene = setup_workbench_scene

if __name__ == "__main__":
    batch.main()
