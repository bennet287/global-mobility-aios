# AIOS V2 Performance

## Prime rule

The structured shell becomes usable before heavy 3D finishes loading.

## Scene pipeline

```text
Blender
  ↓
GLB / glTF
  ↓
mesh optimization
  ↓
texture compression
  ↓
rig normalization
  ↓
animation clips
  ↓
LOD
  ↓
runtime
```

## Character runtime

Use where appropriate:
- shared rig families
- animation reuse
- texture/material atlases
- LOD
- offscreen suspension
- simplified distant rendering

## Environment

Use:
- instancing
- culling
- compressed textures
- selective baked/lightweight lighting
- lazy room/detail loading

## UI

Avoid:
- main-thread blocking scene initialization
- giant route-level hydration cost
- unnecessary layout thrash
- animation while offscreen

## Budgets

Do not invent hard values before measurement.

Prototype must measure:
- shell time-to-interactive
- scene initialization
- frame stability
- memory
- draw calls
- texture memory
- route transition
- animation feedback
- low-power behavior

Then thresholds become governed acceptance criteria.
