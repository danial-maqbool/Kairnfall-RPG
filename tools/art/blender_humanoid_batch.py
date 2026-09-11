"""Render Kairnfall's twelve base humanoid sheets from simple 3D anatomy.

Run inside Blender:
    blender -b --python tools/art/blender_humanoid_batch.py -- --output <dir>

The existing 2D rig remains the source of pose timing and screen-space anchors.
This script gives those joints real volume: skull/jaw/ears/face, neck, torso,
shoulders, articulated limbs, hands, clothing, leather armour, hair and boots.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
RIG_PATH = ROOT / "atelier" / "forge" / "rig.py"
SPEC = importlib.util.spec_from_file_location("kairnfall_rig_for_blender", RIG_PATH)
rig = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rig
SPEC.loader.exec_module(rig)

PIXEL = 0.15
GROUND = rig.GROUND
CENTRE = rig.CENTRE
FRAME = 64

SKINS = (
    "#F2C7A5", "#DFAC82", "#C88A63", "#A96949", "#7E4D38", "#563527",
)
HAIRS = ("#2B211D", "#36251F", "#3D2A21", "#2D2220", "#43281F", "#332521")
EYES = ("#4B342A", "#34534A", "#4A3B2A", "#2E4857", "#4A3127", "#2B2625")


def rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) / 255.0 for i in (0, 2, 4)) + (1.0,)


def material(name, colour, roughness=0.72, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = rgb(colour) if isinstance(colour, str) else colour
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = mat.diffuse_color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def assign(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def screen(point, depth=0.0):
    return Vector(((point[0] - CENTRE) * PIXEL, depth, (GROUND - point[1]) * PIXEL))


def sphere(name, segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0)
    obj = bpy.context.object
    obj.name = name
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def cylinder(name, vertices=10):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=1.0, depth=2.0)
    obj = bpy.context.object
    obj.name = name
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def cube(name):
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    obj = bpy.context.object
    obj.name = name
    bevel = obj.modifiers.new("soft bevel", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 2
    return obj


def place_segment(obj, a, b, width_px, depth_a, mat, depth_b=None):
    if depth_b is None:
        depth_b = depth_a
    va = screen(a, depth_a)
    vb = screen(b, depth_b)
    delta = vb - va
    length = max(0.01, delta.length)
    obj.location = (va + vb) / 2
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(delta.normalized())
    radius = max(0.05, width_px * PIXEL * 0.5)
    obj.scale = (radius, radius, length * 0.5)
    assign(obj, mat)
    obj.hide_render = False


def place_ellipsoid(obj, point, scale_px, depth, mat, angle=0.0):
    obj.location = screen(point, depth)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (0.0, angle, 0.0)
    obj.scale = tuple(max(0.03, value * PIXEL) for value in scale_px)
    assign(obj, mat)
    obj.hide_render = False


def place_box(obj, point, scale_px, depth, mat, angle=0.0):
    obj.location = screen(point, depth)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (0.0, angle, 0.0)
    obj.scale = tuple(max(0.025, value * PIXEL) for value in scale_px)
    assign(obj, mat)
    obj.hide_render = False


def hide(*objects):
    for obj in objects:
        obj.hide_render = True


def build_pool():
    pool = {}
    for key in ("far", "near"):
        pool[f"upper_arm_{key}"] = cylinder(f"upper_arm_{key}")
        pool[f"forearm_{key}"] = cylinder(f"forearm_{key}")
        pool[f"bracer_{key}"] = cylinder(f"bracer_{key}")
        pool[f"hand_{key}"] = sphere(f"hand_{key}", 12, 6)
        pool[f"thigh_{key}"] = cylinder(f"thigh_{key}")
        pool[f"shin_{key}"] = cylinder(f"shin_{key}")
        pool[f"knee_{key}"] = sphere(f"knee_{key}", 12, 6)
        pool[f"boot_{key}"] = cylinder(f"boot_{key}")
        pool[f"toe_{key}"] = sphere(f"toe_{key}", 12, 6)
        pool[f"shoulder_pad_{key}"] = sphere(f"shoulder_pad_{key}", 12, 6)
    for name in ("chest", "waist", "pelvis", "vest", "head", "jaw", "hair_cap", "hair_left", "hair_right", "hair_back", "ear_left", "ear_right", "eye_left", "eye_right", "nose"):
        pool[name] = sphere(name, 16, 8)
    for name in ("neck", "collar"):
        pool[name] = cylinder(name)
    for name in ("belt", "mouth", "brow_left", "brow_right", "chest_strap"):
        pool[name] = cube(name)
    return pool


def setup_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = FRAME
    scene.render.resolution_y = FRAME
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

    world = bpy.data.worlds.new("Kairnfall World") if not bpy.data.worlds else bpy.data.worlds[0]
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.17, 0.18, 0.20, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45

    bpy.ops.object.camera_add(location=(0.0, -18.0, 6.8))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 9.6
    look_at(camera, (0.0, 0.0, 3.15))
    scene.camera = camera

    def area(name, location, energy, size, colour):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = colour
        look_at(light, (0.0, 0.0, 3.0))
        return light

    area("key", (-5.0, -7.0, 11.0), 650, 5.0, (1.0, 0.84, 0.68))
    area("fill", (5.0, -5.0, 7.0), 320, 4.0, (0.58, 0.70, 1.0))
    area("rim", (1.0, 4.0, 10.0), 430, 4.0, (1.0, 0.72, 0.50))
    return scene


def mats(build_index, skin_index):
    skin = material("skin", SKINS[skin_index], 0.78)
    hair = material("hair", HAIRS[skin_index], 0.82)
    eye = material("eye", EYES[skin_index], 0.52)
    mouth = material("mouth", "#6F3B3D", 0.82)
    if build_index == 0:
        cloth = material("cloth", "#48615A", 0.90)
        cloth_dark = material("cloth_dark", "#344740", 0.92)
        pants = material("pants", "#3F4650", 0.92)
        leather = material("leather", "#684A31", 0.80)
        leather_dark = material("leather_dark", "#443225", 0.86)
        metal = material("metal", "#7D8588", 0.40, 0.36)
    else:
        cloth = material("cloth", "#56647A", 0.90)
        cloth_dark = material("cloth_dark", "#3C4657", 0.92)
        pants = material("pants", "#4B4544", 0.92)
        leather = material("leather", "#75533A", 0.80)
        leather_dark = material("leather_dark", "#473427", 0.86)
        metal = material("metal", "#858A8B", 0.40, 0.32)
    return {"skin": skin, "hair": hair, "eye": eye, "mouth": mouth, "cloth": cloth,
            "cloth_dark": cloth_dark, "pants": pants, "leather": leather,
            "leather_dark": leather_dark, "metal": metal}


def render_pose(pool, pose, build_index, skin_index, scene, output):
    for obj in pool.values():
        obj.hide_render = True
    m = mats(build_index, skin_index)
    build = pose.build
    near_depth, far_depth = -0.28, 0.28
    if pose.back:
        near_depth, far_depth = -0.22, 0.22

    # Legs: adult proportions read from the shared joints, with knees and boots.
    for key, depth in (("far", far_depth), ("near", near_depth)):
        hip, knee, foot = pose.hip[key], pose.knee[key], pose.foot[key]
        ankle = (foot[0], foot[1] - 2.2)
        place_segment(pool[f"thigh_{key}"], hip, knee, build.thigh * 1.02, depth, m["pants"])
        place_ellipsoid(pool[f"knee_{key}"], knee, (build.thigh * 0.46, build.thigh * 0.42, build.thigh * 0.48), depth - 0.02, m["pants"])
        place_segment(pool[f"shin_{key}"], knee, ankle, build.thigh * 0.68, depth, m["pants"])
        boot_top = ((knee[0] * 0.18 + foot[0] * 0.82), (knee[1] * 0.18 + foot[1] * 0.82))
        place_segment(pool[f"boot_{key}"], boot_top, foot, build.thigh * 0.72, depth - 0.025, m["leather_dark"])
        toe_shift = pose.facing * 2.2 if pose.side else (1.25 if key == "near" else -1.25)
        toe = (foot[0] + toe_shift, foot[1] - 0.15)
        place_ellipsoid(pool[f"toe_{key}"], toe, (2.5, 1.75, 1.15), depth - 0.12, m["leather_dark"])

    # Torso uses overlapping volumes instead of one flat polygon.
    chest = pose.chest
    pelvis = pose.pelvis
    spine_dx = pelvis[0] - chest[0]
    spine_dy = pelvis[1] - chest[1]
    spine_angle = math.atan2(spine_dx, max(0.1, spine_dy))
    mid = ((chest[0] + pelvis[0]) * 0.5, (chest[1] + pelvis[1]) * 0.5)
    side_width = build.chest_depth * 1.05 if pose.side else build.shoulder * 0.93
    waist_width = build.chest_depth * 0.96 if pose.side else build.hip * 1.02
    place_ellipsoid(pool["chest"], ((chest[0] + mid[0]) * 0.5, (chest[1] + mid[1]) * 0.5),
                    (side_width, build.chest_depth * 0.72, 4.8), -0.02, m["cloth"], spine_angle)
    place_ellipsoid(pool["waist"], mid, (waist_width + 0.8, build.chest_depth * 0.66, 3.4), 0.0, m["cloth_dark"], spine_angle)
    place_ellipsoid(pool["pelvis"], pelvis, (build.hip + 0.8, build.chest_depth * 0.63, 2.7), 0.02, m["pants"], spine_angle)

    # A leather vest/jerkin gives the base character readable construction.
    vest_width = side_width * (0.87 if build_index == 0 else 0.80)
    place_ellipsoid(pool["vest"], ((chest[0] * 0.68 + pelvis[0] * 0.32), (chest[1] * 0.68 + pelvis[1] * 0.32)),
                    (vest_width, build.chest_depth * 0.74, 3.5), -0.20, m["leather"], spine_angle)
    belt_pos = ((chest[0] * 0.25 + pelvis[0] * 0.75), (chest[1] * 0.25 + pelvis[1] * 0.75))
    place_box(pool["belt"], belt_pos, (waist_width + 0.8, build.chest_depth * 0.82, 0.38), -0.35, m["leather_dark"], spine_angle)
    strap_angle = spine_angle + (0.54 if not pose.back else -0.54)
    place_box(pool["chest_strap"], chest, (0.42, build.chest_depth * 0.85, 4.0), -0.37, m["leather_dark"], strap_angle)

    # Neck and arms.
    place_segment(pool["neck"], pose.chest, pose.neck, 3.5, -0.02, m["skin"])
    place_segment(pool["collar"], ((pose.neck[0], pose.neck[1] + 1.4)), ((pose.neck[0], pose.neck[1] + 3.0)), 4.6, -0.26, m["cloth_dark"])
    raised = {key: pose.hand[key][1] < pose.shoulder[key][1] - 1.5 for key in ("far", "near")}
    arm_order = ("far", "near") if not (raised["far"] and not raised["near"]) else ("near", "far")
    for key in arm_order:
        depth = far_depth if key == "far" else near_depth
        shoulder, elbow, hand = pose.shoulder[key], pose.elbow[key], pose.hand[key]
        sleeve_end = ((shoulder[0] * 0.32 + elbow[0] * 0.68), (shoulder[1] * 0.32 + elbow[1] * 0.68))
        place_segment(pool[f"upper_arm_{key}"], shoulder, sleeve_end, build.limb * 1.24, depth, m["cloth"])
        place_segment(pool[f"forearm_{key}"], sleeve_end, hand, build.limb * 0.78, depth - 0.035, m["skin"])
        bracer_start = ((elbow[0] * 0.45 + hand[0] * 0.55), (elbow[1] * 0.45 + hand[1] * 0.55))
        bracer_end = ((elbow[0] * 0.18 + hand[0] * 0.82), (elbow[1] * 0.18 + hand[1] * 0.82))
        place_segment(pool[f"bracer_{key}"], bracer_start, bracer_end, build.limb * 0.88, depth - 0.10, m["leather"])
        place_ellipsoid(pool[f"hand_{key}"], hand, (1.45, 1.05, 1.6), depth - 0.09, m["skin"])
        shoulder_pad = ((shoulder[0] * 0.85 + chest[0] * 0.15), (shoulder[1] * 0.85 + chest[1] * 0.15))
        place_ellipsoid(pool[f"shoulder_pad_{key}"], shoulder_pad, (2.1 if build_index == 0 else 1.7, 1.35, 1.1), depth - 0.08, m["leather"])

    # Head and jaw are separate volumes. The skull is smaller than the old 2D
    # disc so the figure reads closer to an adult human at 64 px.
    hx, hy = pose.head
    r = pose.head_r * 0.86
    head_depth = -0.18 if not pose.back else 0.05
    place_ellipsoid(pool["head"], pose.head, (r * 0.94, r * 0.76, r * 1.02), head_depth, m["skin"], -pose.head_tilt)
    jaw_point = (hx + math.sin(pose.head_tilt) * 1.4, hy + 2.7)
    place_ellipsoid(pool["jaw"], jaw_point, (r * 0.72, r * 0.65, r * 0.55), head_depth - 0.06, m["skin"], -pose.head_tilt)

    # Ears are explicit geometry, not painted dots.
    ear_z = hy + 0.4
    ear_span = r * 0.94
    place_ellipsoid(pool["ear_left"], (hx - ear_span, ear_z), (0.88, 0.62, 1.20), head_depth - 0.01, m["skin"])
    place_ellipsoid(pool["ear_right"], (hx + ear_span, ear_z), (0.88, 0.62, 1.20), head_depth - 0.01, m["skin"])

    # Hair has a skull-conforming cap plus side/back masses. It follows head
    # motion automatically and remains readable under later equipment layers.
    place_ellipsoid(pool["hair_cap"], (hx, hy - r * 0.48), (r * 1.02, r * 0.82, r * 0.66), head_depth - 0.28, m["hair"], -pose.head_tilt)
    place_ellipsoid(pool["hair_left"], (hx - r * 0.72, hy - 0.2), (1.25, 0.88, 2.5), head_depth - 0.22, m["hair"])
    place_ellipsoid(pool["hair_right"], (hx + r * 0.72, hy - 0.2), (1.25, 0.88, 2.5), head_depth - 0.22, m["hair"])
    place_ellipsoid(pool["hair_back"], (hx, hy + 1.1), (r * 0.86, r * 0.62, 2.5 if build_index == 0 else 3.1), 0.22, m["hair"])

    # Face features are positioned in head-local screen space. Front, side and
    # back facings deliberately use different visible feature sets.
    if pose.back:
        hide(pool["eye_left"], pool["eye_right"], pool["nose"], pool["mouth"], pool["brow_left"], pool["brow_right"])
    elif pose.side:
        facing = pose.facing or 1
        eye_pt = (hx + facing * 2.1, hy - 0.5)
        nose_pt = (hx + facing * (r + 0.7), hy + 0.9)
        mouth_pt = (hx + facing * 2.5, hy + 3.0)
        place_ellipsoid(pool["eye_left"], eye_pt, (0.62, 0.50, 0.62), head_depth - 0.72, m["eye"])
        hide(pool["eye_right"])
        place_ellipsoid(pool["nose"], nose_pt, (0.72, 0.62, 0.78), head_depth - 0.58, m["skin"])
        place_box(pool["mouth"], mouth_pt, (0.85, 0.22, 0.18), head_depth - 0.76, m["mouth"])
        brow_pt = (hx + facing * 2.0, hy - 1.75)
        place_box(pool["brow_left"], brow_pt, (0.85, 0.18, 0.18), head_depth - 0.76, m["hair"], -facing * 0.10)
        hide(pool["brow_right"])
        hide(pool["ear_left"] if facing > 0 else pool["ear_right"])
    else:
        for name, sign in (("eye_left", -1), ("eye_right", 1)):
            place_ellipsoid(pool[name], (hx + sign * 1.75, hy - 0.45), (0.58, 0.48, 0.58), head_depth - 0.73, m["eye"])
        place_ellipsoid(pool["nose"], (hx, hy + 0.85), (0.66, 0.58, 0.82), head_depth - 0.72, m["skin"])
        mouth_angle = 0.0
        mouth_z = hy + 3.2
        if pose.state == "attack":
            mouth_angle = -0.10
        elif pose.state == "hit":
            mouth_angle = 0.22
        elif pose.state == "cast":
            mouth_z = hy + 3.35
        elif pose.state == "death" and pose.frame >= 5:
            mouth_angle = 0.30
        place_box(pool["mouth"], (hx, mouth_z), (1.3, 0.22, 0.18), head_depth - 0.78, m["mouth"], mouth_angle)
        brow_tilt = {"attack": 0.18, "cast": -0.10, "hit": 0.26, "death": 0.16}.get(pose.state, 0.02)
        place_box(pool["brow_left"], (hx - 1.8, hy - 1.75), (0.88, 0.18, 0.18), head_depth - 0.78, m["hair"], brow_tilt)
        place_box(pool["brow_right"], (hx + 1.8, hy - 1.75), (0.88, 0.18, 0.18), head_depth - 0.78, m["hair"], -brow_tilt)
        if pose.state == "death" and pose.frame >= 5:
            pool["eye_left"].scale.z *= 0.20
            pool["eye_right"].scale.z *= 0.20

    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    scene = setup_scene()
    pool = build_pool()
    for build_index in range(2):
        for skin_index in range(6):
            sheet_dir = output / f"body_{build_index}_{skin_index}"
            sheet_dir.mkdir(parents=True, exist_ok=True)
            for state_index, state in enumerate(rig.STATES):
                for direction in range(4):
                    for frame in range(rig.FRAMES):
                        pose = rig.pose(build_index, state, frame, direction)
                        path = sheet_dir / f"{state_index:02d}_{direction}_{frame}.png"
                        render_pose(pool, pose, build_index, skin_index, scene, path)
            print(f"Rendered {sheet_dir.name}", flush=True)


if __name__ == "__main__":
    main()
