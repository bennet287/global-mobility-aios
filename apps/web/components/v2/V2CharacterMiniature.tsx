import { resolveCharacterArtPrototype } from "../../lib/v2/character-art-prototype";
import { resolveCharacterAssetBinding } from "../../lib/v2/character-asset-manifest";
import { resolveV2CharacterPresentation } from "../../lib/v2/character-mission-presentation";
import { V2CharacterArtPrototype } from "./V2CharacterArtPrototype";

export function V2CharacterMiniature({
  positionKey,
  title,
  department,
  variant = "compact",
}: {
  positionKey: string;
  title: string;
  department: string;
  variant?: "compact" | "inspector";
}) {
  const model = resolveV2CharacterPresentation({
    positionKey,
    title,
    department,
  });
  const presentation = model.presentation;
  const art = resolveCharacterArtPrototype({ presentationKey: model.presentationKey });
  const assetBinding = resolveCharacterAssetBinding(presentation);
  const inspector = variant === "inspector";

  return (
    <div
      aria-hidden={inspector ? undefined : true}
      aria-label={inspector ? presentation.accessibilityDescription : undefined}
      className={"aios-v2-character-miniature " + (inspector ? "inspector" : "compact")}
      data-animation-set={presentation.animationSetKey}
      data-art-accent={art.accent}
      data-art-archetype={art.archetype}
      data-art-prop={art.prop}
      data-art-wardrobe={art.wardrobe}
      data-asset-compatible={String(assetBinding.compatible)}
      data-asset-model-available={String(assetBinding.modelAvailable)}
      data-asset-renderer-mode={assetBinding.rendererMode}
      data-canonical-state-writable="false"
      data-lod-class={presentation.lodClass}
      data-presentation-key={model.presentationKey}
      data-presentation-only="true"
      data-presence-claimed="false"
      data-resolution-kind={model.resolutionKind}
      data-rig-class={presentation.rigClass}
      data-role-family={presentation.roleFamily}
      data-semantic-animation-active="false"
      data-silhouette={presentation.silhouette}
      role={inspector ? "img" : undefined}
    >
      <div className="aios-v2-character-stage aios-v2-character-stage-art" aria-hidden="true">
        <V2CharacterArtPrototype
          presentationKey={model.presentationKey}
          variant={inspector ? "inspector" : "compact"}
        />
      </div>

      {inspector ? (
        <div className="aios-v2-character-meta" aria-hidden="true">
          <span>Character presentation</span>
          <strong>{model.presentationKey.replaceAll("-", " ")}</strong>
          <small>
            {art.archetype.replaceAll("-", " ")}
            {" · "}
            {art.wardrobe.replaceAll("-", " ")}
            {" · "}
            {art.prop.replaceAll("-", " ")}
          </small>
          <small>
            {presentation.silhouette.replaceAll("-", " ")}
            {" · "}
            {presentation.locomotionPersonality.replaceAll("-", " ")}
          </small>
          <em>
            {model.resolutionKind.replaceAll("-", " ")}
            {" · "}
            {assetBinding.rendererMode.replaceAll("-", " ")}
            {" · presentation only · semantic motion inactive"}
          </em>
          <small className="aios-v2-character-asset-note">{assetBinding.limitation}</small>
        </div>
      ) : null}
    </div>
  );
}
