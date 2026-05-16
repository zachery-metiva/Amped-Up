# Pole Compliance Exemplar Library v0.9 (3D Pipeline with Annotations)

Extends v0.8 with reusable asset library, per-scene .blend files, and per-image bounding box annotations. This version produces files that are directly consumable by an object-detection training pipeline.

## What's new in v0.9

| Addition | Description |
|---|---|
| `assets/pole_asset_library.blend` | One openable Blender file containing the reusable parts (pole, crossarm, insulator, conductor, tree variants, broken crossarm, icicle, two ground types) each in its own named collection. Use as a source for `Append` or `Link` in other projects. |
| `scene_blends/sp35c5_*.blend` | Three openable scene files (one per scene type), each with full geometry, materials, camera, and lights baked in. Inspect, modify, or re-render at higher quality. |
| `annotations/*.json` | One JSON per rendered image with 2D bounding boxes for every visible defect, classified by defect type. COCO-style format. |
| `annotations/_index.json` | Combined index across all images with category list and dataset statistics. |
| `bbox_overlays/*.png` | Renders with bounding boxes drawn on top for visual verification. Not part of the training data, just a sanity check. |
| `draw_bbox_overlays.py` | Standalone script that reads annotations and produces overlays. |

## Annotation schema

Each per-image JSON has this shape:

```json
{
  "image": "sp35c5_vegcontact_front_noon.png",
  "resolution": [1024, 1024],
  "scene": "vegcontact",
  "scene_severity": "imminent_danger",
  "angle": "front",
  "lighting": "noon",
  "camera": {
    "location": [0.0, -18.0, 2.5],
    "rotation_euler_rad": [1.701, 0.0, 0.0],
    "lens_mm": 50.0,
    "sensor_width_mm": 36.0
  },
  "annotations": [
    {
      "class": "veg_contact_branch",
      "pass_index": 1,
      "bounding_box_2d": {
        "normalized": {"x_min": 0.498, "x_max": 0.680, "y_min": 0.017, "y_max": 0.119},
        "pixels":     {"x_min": 510,    "x_max": 696,   "y_min": 17,    "y_max": 122}
      },
      "object_name": "TreeBranchContact"
    }
  ],
  "defect_count_visible": 1,
  "defect_count_in_scene": 1,
  "is_negative_sample": false,
  "defects_off_frame": false
}
```

Pixel-space `y_min`/`y_max` use image-space convention (origin top-left, y increases downward), matching what most detection frameworks expect. Normalized coords use the same convention.

`is_negative_sample` is True only when the source scene contains zero defects (compliant scene). `defects_off_frame` is True when defects exist in the scene but project entirely outside the visible frame from this camera angle.

## Defect classes

| ID | Class | Severity in v0.9 scenes |
|---|---|---|
| 1 | `veg_contact_branch` | imminent_danger |
| 2 | `broken_crossarm` | imminent_danger |
| 3 | `downed_conductor` | imminent_danger |
| 4 | `ice_buildup` | (reserved, not yet tagged on icicles) |

The class IDs are stable across the project; future versions will add classes (groundline_decay, leaning_pole, missing_guy, etc.) without renumbering.

## Dataset statistics (v0.9)

```
Total images          27
Total visible defects 27
True negative samples  9  (compliant scene at 3 angles x 3 lightings)
Off-frame views        0
```

Per-defect counts:
- `veg_contact_branch`: 9 (vegcontact scene, all 3 angles, all 3 lightings)
- `broken_crossarm`: 9 (ice_broken_arm scene, all 3 angles, all 3 lightings)
- `downed_conductor`: 9 (ice_broken_arm scene, all 3 angles, all 3 lightings)

## How annotations are computed

`generate_v9.py` tags defect objects with a custom property `defect_class` and a `pass_index` matching the class ID. After building each scene and positioning the camera, the script:

1. Walks all scene objects looking for the `defect_class` tag
2. For each tagged object, transforms its 8 local-space bounding box corners through `obj.matrix_world` to get world-space corners
3. Projects each world corner through `bpy_extras.object_utils.world_to_camera_view` to get camera-view normalized coordinates
4. Filters out corners that project behind the camera (z <= 0)
5. Clips the 2D extent to the [0, 1] x [0, 1] frame
6. Converts to pixel coords using the scene's render resolution

Important pitfall fixed in this version: `world_to_camera_view` uses the scene's current render resolution to determine aspect ratio. The render settings must be configured BEFORE projection, even on runs that skip the actual render. The script calls `configure_render` unconditionally before computing annotations.

## Limitations and what's still missing for AI training

1. **No segmentation masks yet.** Annotations are 2D bounding boxes only. Pixel-level masks via Blender's Object Index pass would require a second render output and add per-image render time. Documented as v1.0 work.
2. **Bounding boxes are AABB of the full object.** A long diagonal object (broken arm, downed conductor) gets a bbox covering the diagonal span, which includes empty pixels at the corners. Oriented bounding boxes or segmentation masks would be tighter.
3. **Single pole type, three scenes.** 27 images is enough to validate the pipeline and check that detector training will accept the format. Not enough to actually train a useful model. v1.0 priorities: more pole types (ju40c4, de45c3, daw46, hfw69) and more defect variants.
4. **Some defects can occlude each other.** No occlusion handling. If the broken crossarm hides the downed conductor in some camera angles, the conductor's bounding box is still computed from its full world geometry. Segmentation masks would fix this; for bbox-only detectors it is usually acceptable.

## How to run

```bash
# Generate everything (asset library, scene blends, renders, annotations, index)
blender --background --python generate_v9.py

# Draw bounding box overlays for visual verification
python3 draw_bbox_overlays.py
```

The Blender pipeline is resumable. Existing PNGs are reused; only the .blend files and annotations are recomputed each run. Total runtime on a cold cache is the same as v0.8 (~9 minutes for 27 renders). On a warm cache it is well under 5 seconds.

## Layout

```
pole_compliance_exemplar_v9/
  README.md
  generate_v9.py
  draw_bbox_overlays.py
  assets/
    pole_asset_library.blend
  scene_blends/
    sp35c5_compliant.blend
    sp35c5_vegcontact.blend
    sp35c5_ice_broken_arm.blend
  renders/
    sp35c5_{scene}_{angle}_{lighting}.png   (27 files)
  annotations/
    sp35c5_{scene}_{angle}_{lighting}.json  (27 files)
    _index.json
  bbox_overlays/
    sp35c5_{scene}_{angle}_{lighting}.png   (27 files)
```

## Version history

- v0.1 through v0.7: SVG schematic taxonomy, 230 scenes
- v0.8: Blender 3D proof of concept, 27 renders
- v0.9: adds asset library .blend, per-scene .blend, and 2D bounding box annotations
