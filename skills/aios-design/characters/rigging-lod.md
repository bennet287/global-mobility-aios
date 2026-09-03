# Character Rigging & LOD

## Rig strategy

Prefer a small number of compatible rig families.

Benefits:
- animation reuse
- lower asset complexity
- consistent motion
- easier LOD

## Variation

Identity comes from:
- mesh
- head
- hair
- wardrobe
- material
- proportions within bounded rig compatibility
- motion personality

## LOD

Candidate levels:
- close inspector
- standard office
- distant HQ

Distant characters retain:
- silhouette
- department/role readability
- selection
- state cue

before fine facial detail.

## Runtime

Consider:
- animation clip reuse
- offscreen suspension
- shared materials/atlases
- compressed textures
- simplified distant meshes

Hard thresholds follow measurement.
