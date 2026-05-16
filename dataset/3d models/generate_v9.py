"""
v0.9 - Adds to v0.8:
1. Saves asset library .blend (reusable parts)
2. Saves per-scene .blend files
3. Computes 2D bounding box annotations per defect
4. Writes COCO-style annotation JSON files
"""
import bpy, math, os, time, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT_DIR = "/home/claude/exemplar9/renders"
ASSETS_DIR = "/home/claude/exemplar9/assets"
SCENES_DIR = "/home/claude/exemplar9/scene_blends"
ANNOT_DIR = "/home/claude/exemplar9/annotations"
RES_X, RES_Y = 1024, 1024
EEVEE_SAMPLES = 32
for d in (OUT_DIR, ASSETS_DIR, SCENES_DIR, ANNOT_DIR):
    os.makedirs(d, exist_ok=True)

POLE_TOTAL_FT = 35.0
POLE_EMBED_FT = 6.0
POLE_ABOVE_M = (POLE_TOTAL_FT - POLE_EMBED_FT) * 0.3048
POLE_TOP_D = 0.18
POLE_BASE_D = 0.30
PRIMARY_HEIGHT = POLE_ABOVE_M - 0.3
NEUTRAL_HEIGHT = PRIMARY_HEIGHT - 1.5

DEFECT_CLASSES = {
    "veg_contact_branch": 1,
    "broken_crossarm": 2,
    "downed_conductor": 3,
    "ice_buildup": 4,
}

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                 bpy.data.lights, bpy.data.curves, bpy.data.images,
                 bpy.data.collections):
        for item in list(coll):
            try:
                coll.remove(item)
            except RuntimeError:
                pass

def mat(name, color, roughness=0.7, metallic=0.0, alpha=1.0, transmission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, alpha)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if transmission > 0:
        try:
            bsdf.inputs["Transmission"].default_value = transmission
        except KeyError:
            try:
                bsdf.inputs["Transmission Weight"].default_value = transmission
            except KeyError:
                pass
    if alpha < 1.0:
        m.blend_method = 'BLEND'
    return m

MATERIALS = {}
def init_materials():
    MATERIALS.clear()
    MATERIALS["wood_pole"] = mat("wood_pole", (0.625, 0.486, 0.314), roughness=0.85)
    MATERIALS["wood_arm"] = mat("wood_arm", (0.478, 0.361, 0.165), roughness=0.85)
    MATERIALS["wood_dark"] = mat("wood_dark", (0.235, 0.157, 0.063), roughness=0.85)
    MATERIALS["metal_hw"] = mat("metal_hw", (0.373, 0.369, 0.353), roughness=0.4, metallic=0.8)
    MATERIALS["insulator"] = mat("insulator", (0.92, 0.90, 0.85), roughness=0.2)
    MATERIALS["conductor"] = mat("conductor", (0.235, 0.235, 0.235), roughness=0.4, metallic=0.7)
    MATERIALS["conductor_red"] = mat("conductor_red", (0.639, 0.176, 0.176), roughness=0.5)
    MATERIALS["grass"] = mat("grass", (0.231, 0.427, 0.067), roughness=0.95)
    MATERIALS["foliage"] = mat("foliage", (0.231, 0.427, 0.067), roughness=0.9)
    MATERIALS["bark"] = mat("bark", (0.361, 0.267, 0.149), roughness=0.9)
    MATERIALS["ice"] = mat("ice", (0.78, 0.88, 0.93), roughness=0.1, alpha=0.6, transmission=0.85)
    MATERIALS["snow"] = mat("snow", (0.98, 0.99, 1.0), roughness=0.8)

def make_pole(x=0, y=0):
    bpy.ops.mesh.primitive_cone_add(
        vertices=24, radius1=POLE_BASE_D / 2, radius2=POLE_TOP_D / 2,
        depth=POLE_ABOVE_M, location=(x, y, POLE_ABOVE_M / 2))
    pole = bpy.context.object
    pole.name = "Pole"
    pole.data.materials.append(MATERIALS["wood_pole"])
    return pole

def make_crossarm(z, length=1.83, depth=0.10, width=0.10, x_offset=0, broken_at=None):
    if broken_at is None:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x_offset, 0, z))
        arm = bpy.context.object
        arm.scale = (length, depth, width)
        arm.name = "Crossarm"
        arm.data.materials.append(MATERIALS["wood_arm"])
        return arm
    left_len = (length / 2) + broken_at
    right_len = (length / 2) - broken_at
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-(length/2) + left_len/2, 0, z))
    left = bpy.context.object
    left.scale = (left_len, depth, width)
    left.name = "Crossarm_L"
    left.data.materials.append(MATERIALS["wood_arm"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(broken_at, 0, z))
    right = bpy.context.object
    right.scale = (right_len, depth, width)
    right.location = (broken_at + right_len/2 * math.cos(math.radians(-45)),
                      0, z + right_len/2 * math.sin(math.radians(-45)))
    right.rotation_euler = (0, math.radians(-45), 0)
    right.name = "Crossarm_R_broken"
    right.data.materials.append(MATERIALS["wood_dark"])
    return left, right

def make_insulator(x, y, z):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.025, depth=0.15,
                                         location=(x, y, z + 0.075))
    pin = bpy.context.object
    pin.name = "InsulatorPin"
    pin.data.materials.append(MATERIALS["metal_hw"])
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.07, depth=0.05,
                                         location=(x, y, z + 0.175))
    disc = bpy.context.object
    disc.name = "InsulatorDisc"
    disc.data.materials.append(MATERIALS["insulator"])
    return pin, disc

def make_conductor(x1, x2, z_attach, sag_depth=0.3, color_key="conductor", radius=0.02, name="Conductor"):
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 4
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(2)
    pts = spline.bezier_points
    pts[0].co = (x1, 0, z_attach)
    pts[1].co = ((x1 + x2) / 2, 0, z_attach - sag_depth)
    pts[2].co = (x2, 0, z_attach)
    for p in pts:
        p.handle_left_type = 'AUTO'
        p.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(MATERIALS[color_key])
    return obj

def make_ground(size=50, mat_key="grass"):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "Ground"
    ground.data.materials.append(MATERIALS[mat_key])
    return ground

def make_tree(x, y, trunk_height=7.0, canopy_radius=1.8, branch_to_primary=False):
    bpy.ops.mesh.primitive_cone_add(
        vertices=12, radius1=0.20, radius2=0.08, depth=trunk_height,
        location=(x, y, trunk_height / 2))
    trunk = bpy.context.object
    trunk.name = "TreeTrunk"
    trunk.data.materials.append(MATERIALS["bark"])
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=2, radius=canopy_radius,
        location=(x, y, trunk_height + canopy_radius * 0.4))
    canopy = bpy.context.object
    canopy.name = "TreeCanopy"
    canopy.data.materials.append(MATERIALS["foliage"])
    canopy.scale = (1.1, 1.1, 0.95)
    branch = None
    if branch_to_primary:
        dx, dy = -x, -y
        dist = math.sqrt(dx*dx + dy*dy)
        branch_start = Vector((x + dx/dist * canopy_radius * 0.6,
                                y + dy/dist * canopy_radius * 0.6,
                                trunk_height + canopy_radius * 0.4))
        branch_end = Vector((0, 0, PRIMARY_HEIGHT - 0.05))
        midpoint = (branch_start + branch_end) / 2
        length = (branch_end - branch_start).length
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.04, depth=length, location=midpoint)
        branch = bpy.context.object
        branch.name = "TreeBranchContact"
        branch.data.materials.append(MATERIALS["bark"])
        direction = branch_end - branch_start
        z_axis = Vector((0, 0, 1))
        rot_axis = z_axis.cross(direction.normalized())
        if rot_axis.length > 0.001:
            rot_axis.normalize()
            angle = math.acos(max(-1, min(1, z_axis.dot(direction.normalized()))))
            branch.rotation_mode = 'AXIS_ANGLE'
            branch.rotation_axis_angle = (angle, *rot_axis)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.35, location=branch_end)
        leaves = bpy.context.object
        leaves.name = "BranchLeaves"
        leaves.data.materials.append(MATERIALS["foliage"])
    return trunk, canopy, branch

def make_ice_sleeve_on_conductor(conductor_obj, thickness_mult=1.8):
    new_curve = conductor_obj.data.copy()
    new_curve.bevel_depth = conductor_obj.data.bevel_depth * thickness_mult
    ice_obj = bpy.data.objects.new("IceSleeve", new_curve)
    bpy.context.collection.objects.link(ice_obj)
    new_curve.materials.clear()
    new_curve.materials.append(MATERIALS["ice"])
    return ice_obj

def make_icicle(x, y, z_top, length=0.25):
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.025, radius2=0.0, depth=length,
                                     location=(x, y, z_top - length/2))
    icicle = bpy.context.object
    icicle.name = "Icicle"
    icicle.data.materials.append(MATERIALS["ice"])
    return icicle

def tag_defect(obj, class_name):
    obj["defect_class"] = class_name
    obj.pass_index = DEFECT_CLASSES.get(class_name, 99)

def build_compliant():
    make_ground(mat_key="grass")
    make_pole()
    make_insulator(0, 0, POLE_ABOVE_M)
    make_crossarm(NEUTRAL_HEIGHT + 0.1, length=1.2)
    make_insulator(-0.5, 0, NEUTRAL_HEIGHT + 0.15)
    make_insulator(0.5, 0, NEUTRAL_HEIGHT + 0.15)
    make_conductor(-12, 12, POLE_ABOVE_M + 0.18, sag_depth=0.4, name="PrimaryConductor")
    make_conductor(-12, 12, NEUTRAL_HEIGHT + 0.25, sag_depth=0.5, name="NeutralConductor")
    make_tree(7, 4, trunk_height=5.0, canopy_radius=1.5, branch_to_primary=False)
    return {"scene": "compliant", "defect_focus": None, "severity": "compliant"}

def build_vegcontact():
    make_ground(mat_key="grass")
    make_pole()
    make_insulator(0, 0, POLE_ABOVE_M)
    make_crossarm(NEUTRAL_HEIGHT + 0.1, length=1.2)
    make_insulator(-0.5, 0, NEUTRAL_HEIGHT + 0.15)
    make_insulator(0.5, 0, NEUTRAL_HEIGHT + 0.15)
    make_conductor(-12, 12, POLE_ABOVE_M + 0.18, sag_depth=0.4, name="PrimaryConductor")
    make_conductor(-12, 12, NEUTRAL_HEIGHT + 0.25, sag_depth=0.5, name="NeutralConductor")
    _trunk, _canopy, branch = make_tree(3.5, 2.0, trunk_height=7.5, canopy_radius=1.8, branch_to_primary=True)
    if branch is not None:
        tag_defect(branch, "veg_contact_branch")
    return {"scene": "vegcontact", "defect_focus": Vector((0, 0, PRIMARY_HEIGHT)),
            "severity": "imminent_danger"}

def build_ice_broken_arm():
    make_ground(mat_key="snow")
    make_pole()
    left, right = make_crossarm(NEUTRAL_HEIGHT + 0.1, length=1.5, broken_at=0.1)
    tag_defect(right, "broken_crossarm")
    make_insulator(0, 0, POLE_ABOVE_M)
    make_insulator(-0.5, 0, NEUTRAL_HEIGHT + 0.15)
    primary = make_conductor(-12, 12, POLE_ABOVE_M + 0.18, sag_depth=0.7,
                              color_key="conductor", name="PrimaryConductor")
    make_ice_sleeve_on_conductor(primary)
    neutral_left = make_conductor(-12, -0.3, NEUTRAL_HEIGHT + 0.25, sag_depth=0.4,
                                   color_key="conductor", name="NeutralConductorLeft")
    make_ice_sleeve_on_conductor(neutral_left)
    dangling = make_conductor(0.7, 12, NEUTRAL_HEIGHT - 1.5, sag_depth=0.8,
                               color_key="conductor_red", name="DownedConductor")
    pts = dangling.data.splines[0].bezier_points
    pts[0].co = (0.7, 0, NEUTRAL_HEIGHT - 0.6)
    tag_defect(dangling, "downed_conductor")
    for x in [-8, -4, 4, 8]:
        z_at = POLE_ABOVE_M + 0.18 - 0.7 * (1 - (x/12)**2) - 0.04
        make_icicle(x, 0, z_at, length=0.30)
    make_icicle(0.07, 0, POLE_ABOVE_M - 0.03, length=0.18)
    return {"scene": "ice_broken_arm", "defect_focus": Vector((0.5, 0, NEUTRAL_HEIGHT)),
            "severity": "imminent_danger"}

def setup_camera(angle, scene_info):
    target = Vector((0, 0, POLE_ABOVE_M * 0.55))
    if angle == "front":
        loc = Vector((0, -18, 2.5))
    elif angle == "three_quarter":
        loc = Vector((11, -13, 4.5))
        target = Vector((0, 0, POLE_ABOVE_M * 0.5))
    elif angle == "closeup":
        focus = scene_info.get("defect_focus") or Vector((0, 0, POLE_ABOVE_M * 0.85))
        loc = focus + Vector((4.0, -4.5, 0.4))
        target = focus
    else:
        loc = Vector((0, -18, 2.5))
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    direction = target - cam.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot_quat.to_euler()
    cam.data.lens = 50
    bpy.context.scene.camera = cam
    return cam

def setup_lighting(lighting):
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if lighting == "noon":
        bg_node.inputs["Color"].default_value = (0.55, 0.72, 0.92, 1.0)
        bg_node.inputs["Strength"].default_value = 0.6
        sun_dir = (math.radians(35), 0, math.radians(20))
        sun_color = (1.0, 0.98, 0.92); sun_energy = 4.0
    elif lighting == "golden_hour":
        bg_node.inputs["Color"].default_value = (0.92, 0.62, 0.38, 1.0)
        bg_node.inputs["Strength"].default_value = 0.4
        sun_dir = (math.radians(75), 0, math.radians(-60))
        sun_color = (1.0, 0.72, 0.45); sun_energy = 3.2
    elif lighting == "overcast":
        bg_node.inputs["Color"].default_value = (0.72, 0.74, 0.76, 1.0)
        bg_node.inputs["Strength"].default_value = 1.1
        sun_dir = (math.radians(45), 0, 0)
        sun_color = (0.92, 0.93, 0.94); sun_energy = 0.8
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 12))
    sun = bpy.context.object
    sun.data.energy = sun_energy
    sun.data.color = sun_color
    sun.rotation_euler = sun_dir
    return sun

def configure_render(filepath):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.filepath = filepath
    scene.eevee.taa_render_samples = EEVEE_SAMPLES
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 0.6

def compute_2d_bbox(obj, cam, scene):
    corners_world = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    projected = [world_to_camera_view(scene, cam, c) for c in corners_world]
    in_front = [p for p in projected if p.z > 0]
    if not in_front:
        return None
    xs = [p.x for p in in_front]
    ys = [p.y for p in in_front]
    x_min = max(0.0, min(xs))
    x_max = min(1.0, max(xs))
    y_min = max(0.0, min(ys))
    y_max = min(1.0, max(ys))
    if x_max <= x_min or y_max <= y_min:
        return None
    return {
        "normalized": {
            "x_min": round(x_min, 4), "x_max": round(x_max, 4),
            "y_min": round(1.0 - y_max, 4), "y_max": round(1.0 - y_min, 4),
        },
        "pixels": {
            "x_min": int(x_min * RES_X), "x_max": int(x_max * RES_X),
            "y_min": int((1.0 - y_max) * RES_Y), "y_max": int((1.0 - y_min) * RES_Y),
        },
    }

def collect_defect_annotations(scene, cam):
    annots = []
    for obj in scene.objects:
        if "defect_class" not in obj.keys():
            continue
        bbox = compute_2d_bbox(obj, cam, scene)
        if bbox is None:
            continue
        annots.append({
            "class": obj["defect_class"],
            "pass_index": obj.pass_index,
            "bounding_box_2d": bbox,
            "object_name": obj.name,
        })
    return annots

def write_annotation_json(fpath, scene_info, angle, lighting, cam, annots):
    cam_data = {
        "location": [round(v, 3) for v in cam.location],
        "rotation_euler_rad": [round(v, 4) for v in cam.rotation_euler],
        "lens_mm": cam.data.lens,
        "sensor_width_mm": cam.data.sensor_width,
    }
    # Count scene-level defects (objects tagged) vs visible-from-camera annotations
    scene_defect_objects = [o for o in bpy.context.scene.objects if "defect_class" in o.keys()]
    severity = scene_info.get("severity", "unknown")
    payload = {
        "image": os.path.basename(fpath).replace(".json", ".png"),
        "resolution": [RES_X, RES_Y],
        "scene": scene_info["scene"],
        "scene_severity": severity,
        "angle": angle,
        "lighting": lighting,
        "camera": cam_data,
        "annotations": annots,
        "defect_count_visible": len(annots),
        "defect_count_in_scene": len(scene_defect_objects),
        "is_negative_sample": severity == "compliant",
        "defects_off_frame": len(scene_defect_objects) > 0 and len(annots) < len(scene_defect_objects),
    }
    with open(fpath, "w") as f:
        json.dump(payload, f, indent=2)
    return payload

def build_asset_library_blend():
    clear_scene()
    init_materials()
    def in_coll(name, fn):
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
        before = set(bpy.context.scene.objects)
        fn()
        after = set(bpy.context.scene.objects)
        for obj in (after - before):
            for c in obj.users_collection:
                if c is not coll:
                    c.objects.unlink(obj)
            if obj.name not in coll.objects:
                coll.objects.link(obj)
    in_coll("pole", lambda: make_pole())
    in_coll("crossarm", lambda: make_crossarm(NEUTRAL_HEIGHT + 0.1, length=1.5))
    in_coll("insulator", lambda: make_insulator(0, 0, 0))
    in_coll("conductor", lambda: make_conductor(-5, 5, 1, sag_depth=0.2, name="Conductor"))
    in_coll("tree_compliant", lambda: make_tree(5, 0, branch_to_primary=False))
    in_coll("tree_vegcontact", lambda: make_tree(5, 0, branch_to_primary=True))
    in_coll("crossarm_broken", lambda: make_crossarm(NEUTRAL_HEIGHT + 0.1, length=1.5, broken_at=0.1))
    in_coll("icicle", lambda: make_icicle(0, 0, 1, length=0.3))
    in_coll("ground_grass", lambda: make_ground(size=10, mat_key="grass"))
    in_coll("ground_snow", lambda: make_ground(size=10, mat_key="snow"))
    path = os.path.join(ASSETS_DIR, "pole_asset_library.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    return path

SCENES = {
    "compliant": build_compliant,
    "vegcontact": build_vegcontact,
    "ice_broken_arm": build_ice_broken_arm,
}
ANGLES = ["front", "three_quarter", "closeup"]
LIGHTINGS = ["noon", "golden_hour", "overcast"]

def main():
    t0 = time.time()
    asset_path = build_asset_library_blend()
    print(f"[asset library] {asset_path}")

    all_annots = []
    for scene_name, builder in SCENES.items():
        for angle in ANGLES:
            for lighting in LIGHTINGS:
                clear_scene()
                init_materials()
                info = builder()
                cam = setup_camera(angle, info)
                setup_lighting(lighting)

                if angle == "front" and lighting == "noon":
                    sbpath = os.path.join(SCENES_DIR, f"sp35c5_{scene_name}.blend")
                    if not os.path.exists(sbpath):
                        bpy.ops.wm.save_as_mainfile(filepath=sbpath)
                        print(f"[scene blend] {sbpath}")

                fname = f"sp35c5_{scene_name}_{angle}_{lighting}.png"
                fpath = os.path.join(OUT_DIR, fname)
                jpath = os.path.join(ANNOT_DIR, fname.replace(".png", ".json"))

                # ALWAYS configure the render scene first so world_to_camera_view uses the
                # correct resolution/aspect, even if we skip the actual render.
                configure_render(fpath)

                annots = collect_defect_annotations(bpy.context.scene, cam)

                if not os.path.exists(fpath):
                    bpy.ops.render.render(write_still=True)

                payload = write_annotation_json(jpath, info, angle, lighting, cam, annots)
                all_annots.append(payload)
                print(f"[render+annot] {fname}: {len(annots)} defect(s)")

    coco_index = {
        "info": {"version": "0.9.0", "description": "sp35c5 proof of concept with 2D bbox annotations"},
        "categories": [{"id": idx, "name": name} for name, idx in DEFECT_CLASSES.items()],
        "images": all_annots,
        "total_images": len(all_annots),
        "total_visible_defects": sum(p["defect_count_visible"] for p in all_annots),
        "total_negative_samples": sum(1 for p in all_annots if p["is_negative_sample"]),
        "total_off_frame_views": sum(1 for p in all_annots if p["defects_off_frame"]),
    }
    with open(os.path.join(ANNOT_DIR, "_index.json"), "w") as f:
        json.dump(coco_index, f, indent=2)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. {len(all_annots)} renders, "
          f"{coco_index['total_visible_defects']} visible defects, "
          f"{coco_index['total_negative_samples']} true negatives, "
          f"{coco_index['total_off_frame_views']} off-frame views.")

if __name__ == "__main__":
    main()
