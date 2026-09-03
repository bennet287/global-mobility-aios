# Spatial Selection

## Selectable entities

Current:
- department
- employee
- room
- smart object

Future additions require explicit contract review.

## Selection behavior

Selection:
- changes focus
- changes inspector context
- may change camera
- may change active lens

Selection does **not** mutate canonical state.

## Visual treatment

Use:
- subtle outline/rim
- local light emphasis
- de-emphasis of background
- context HUD

Avoid:
- large glowing circles
- game-style target markers
- excessive floating labels

## Accessibility

Selection must have keyboard and structured-list equivalents.
