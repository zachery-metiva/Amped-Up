# Pole Compliance Exemplar Library v0.7

Synthetic SVG schematic library for training and evaluating AI models that detect non-compliant conditions on overhead distribution and transmission poles. v0.7 adds weather and seasonal variants alongside the v0.6 multi-defect baseline.

## What's new in v0.7

60 new scenes covering four weather conditions, on top of the 170 baseline scenes from v0.6. Total library is 230 scenes.

| Weather condition | Standalone scenes | Weather + multi-defect compositions |
|---|---|---|
| Ice loading (NESC 250.B heavy district) | 12 | 4 |
| Snow accumulation | 12 | 2 |
| Post-storm damage (wind, lightning) | 12 | 3 |
| Summer thermal sag (NESC 232 at max temp) | 12 | 3 |
| **Total** | **48** | **12** |

### Framings

Each weather scene falls into one of four framings, encoded in the `framing` field of `annotation_metadata`:

1. **compliant_with_weather** (banner stays green): the pole carries the weather event within design capacity. Used for context training so the model learns to recognize winter and summer conditions without flagging compliant poles.
2. **weather_induced_violation** (existing severity: serious, other_than_serious, de_minimis): the weather caused a non-compliant condition. Examples include ice sag below road clearance and summer sag below vehicle clearance.
3. **damage_from_weather** (existing severity, typically serious or imminent_danger): the weather caused physical damage to hardware. Examples include broken crossarms under ice load, downed conductors after storms, and lightning-scorched arresters.
4. **weather_plus_multi_defect** (multi_defect severity, purple banner): the weather event compounds with a pre-existing defect from the v0.6 catalog. Examples include ice loading on a decaying pole and summer sag near vegetation encroachment.

### Naming convention

| Pattern | Use |
|---|---|
| `{pole_id}_{order}_{violation}.svg` | v0.1 through v0.5 single-defect scenes |
| `{pole_id}_md{N}_{theme}.svg` | v0.6 multi-defect compositions |
| `{pole_id}_w_{condition}_{theme}.svg` | v0.7 standalone weather scenes |
| `{pole_id}_wmd_{condition}_{theme}.svg` | v0.7 weather + multi-defect compositions |

Example: `sp35c5_w_ice_sag_violation.svg` is a rural single-phase 35 ft pole showing ice-loading-induced clearance loss. `sp35c5_wmd_ice_pole_decay.svg` is the same pole type with both ice loading and pole groundline decay as compounded findings.

## Visual conventions added in v0.7

Each weather scene includes an **atmospheric layer** rendered between the neighborhood backdrop and the pole. The atmospheric layer is controlled by helper functions:

- `winter_atmosphere()`: pale overcast sky tint, snowy house roof. Used for ice-loading scenes.
- `snow_atmosphere()`: heavy white ground cover, snow on house, falling flakes, pale sky.
- `storm_cleared_atmosphere()`: post-storm gray sky with breaking cloud blobs, no active rain. Used for damage assessment scenes.
- `summer_atmosphere()`: warm yellow sky tint, sun glare in upper right, heat haze near ground.

**Weather marks** are rendered as overlays on top of the pole and conductors. The library includes:

- Ice helpers: `ice_on_conductor_with_drips`, `icicle`, `ice_buildup_lump`
- Snow helpers: `snow_on_horizontal_arm`, `snow_cap_on_top`
- Storm helpers: `downed_tree_limb`, `broken_crossarm_dangling`, `debris_pile`, `lightning_scorch`
- Thermal helpers: `heat_thermal_sag_curve`, `galloping_indicator`
- Clearance helpers: `clearance_violation_marker` (a red dashed line with a labeled distance)

## Standards anchored

Each scene cites the regulations and standards relevant to the framing:

- NESC 2023 (IEEE C2): Rules 218 (vegetation), 230 (services), 232 (clearances), 234 (special clearances), 235 (phase separation), 238 (joint use safety zone), 250 (loading districts), 261 (strength factors), 277 (insulators)
- OSHA 29 CFR 1910.269: minimum approach distance, downed conductor handling
- OSHA 29 CFR 1903.14: severity classification (imminent danger, serious, other-than-serious, de minimis)
- MIOSHA Part 86: Michigan worker clearance standards
- MPSC R 460.3504 and R 460.601: Michigan PSC corrective action and inspection
- IEEE Std 738: conductor thermal rating for summer sag scenes
- IEEE Std 1313: insulation coordination for lightning scenes
- IEEE Std 1410: galloping conductor for ice loading scenes
- NERC FAC-003: transmission vegetation management
- ANSI O5.1: wood pole standards
- ANSI C29: insulator standards
- ASTM A475: guy strand standards
- USACE: navigable water clearance
- AAR Specification M-1004: railroad clearance

## Metadata schema additions

Each weather scene includes these fields in its `annotation_metadata` block (rendered inside the SVG and visible to a parser):

- `scene_type`: one of `weather_context`, `weather_violation`, `weather_damage`, `multi_defect`
- `weather_condition`: one of `ice_loading`, `snow_accumulation`, `post_storm`, `summer_thermal`
- `framing`: one of `compliant_with_weather`, `weather_induced_violation`, `damage_from_weather`, `weather_plus_multi_defect`
- For multi-defect compositions: `defect_count`, `overall_severity`, `worst_severity_present`, `defects` (array of {violation, severity})

The top-level `metadata.json` adds a `weather_conditions` block describing supported conditions and framings.

## Pole types covered by v0.7 weather scenes

| Pole type | Description | Weather scenes |
|---|---|---|
| sp35c5 | Single-phase rural 35 ft Class 5 | 10 |
| ju40c4 | Joint-use 40 ft Class 4 (urban, comm) | 11 |
| de45c3 | Dead-end 45 ft Class 3 | 11 |
| daw46 | Sub-transmission 46 kV wood | 6 |
| serv30c6 | Service pole 30 ft Class 6 | 7 |
| ang40c4 | Angle pole 40 ft Class 4 | 5 |
| hfw69 | H-frame wood 69 kV transmission | 4 |
| tap40c4 | Tap pole 40 ft Class 4 | 2 |
| hfs138 | H-frame steel 138 kV | 1 |
| tds115 | Transmission dead-end steel 115 kV | 1 |
| bank45c3 | Transformer bank pole | 1 |
| riser40c4 | Underground riser | 1 |

## Library structure

```
pole_compliance_exemplar_v7/
  README.md
  metadata.json
  out/                  230 SVGs (170 from v0.6 + 60 new in v0.7)
  preview/              230 PNGs rendered at 680 px width
```

## Use cases supported by v0.7

1. **Seasonal context training**: model learns to recognize the same pole types in different seasons without flagging compliant winter or summer presentations.
2. **Weather-induced violation detection**: model learns to detect when normal weather effects push a pole into non-compliance (ice sag below clearance, summer thermal sag below vehicle clearance).
3. **Storm response triage**: model learns to recognize the visual signatures of post-storm damage and apply the appropriate severity classification.
4. **Compound risk recognition**: model learns that weather events on already-degraded assets are higher priority than weather on healthy assets.

## Known limitations

- Tree foliage in v0.7 scenes still uses the v0.6 green compliant tree. A future version could add a deciduous-bare variant for winter scenes.
- Storm scenes use a "cleared" atmosphere (post-event survey angle). Active-storm scenes with rain streaks and active wind effects could be added if needed for storm-in-progress training.
- Summer scenes use a single sag depth per pole type. A future version could include intermediate sag levels keyed to specific conductor temperatures.

## Version history

- v0.1 through v0.3: baseline distribution wood pole defects, 54 scenes
- v0.4: extended pole type coverage to 14 types, 90 scenes
- v0.5: 18 pole types, 122 scenes
- v0.6: multi-defect compositions added, 170 scenes
- v0.7: weather and seasonal variants added, 230 scenes
