# Spatial Occlusion & LOD

## Occlusion

The selected/important object must stay readable.

Use:
- camera reframe
- local transparency
- foreground fade
- label priority
- temporary roof/wall hiding

Avoid making the user manually orbit around architecture.

## LOD

Define LOD for:
- characters
- furniture
- smart objects
- architecture
- labels

Distant objects lose detail before they lose semantic recognizability.

## Performance

Offscreen/occluded animation may be suspended.

LOD thresholds become hard only after profiling.
