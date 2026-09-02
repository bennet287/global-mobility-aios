// Deliberately narrow boundary for the Three.js WebGPU build.
// AIOS owns the typed renderer adapter contract; Three.js objects never become domain state.
declare module "three/webgpu" {
  export const WebGPURenderer: any;
  export const Scene: any;
  export const PerspectiveCamera: any;
  export const BoxGeometry: any;
  export const MeshBasicMaterial: any;
  export const Mesh: any;
  export const Raycaster: any;
  export const Vector2: any;
}
