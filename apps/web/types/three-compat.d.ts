declare module "three" {
  export type Group = any;
  export const AmbientLight: any;
  export const BoxGeometry: any;
  export const Color: any;
  export const CylinderGeometry: any;
  export const DirectionalLight: any;
  export const Group: any;
  export const Mesh: any;
  export const MeshPhysicalMaterial: any;
  export const MeshStandardMaterial: any;
  export const PerspectiveCamera: any;
  export const PlaneGeometry: any;
  export const Scene: any;
  export const SphereGeometry: any;
  export const SRGBColorSpace: any;
  export const WebGLRenderer: any;
  export const ACESFilmicToneMapping: any;
}

declare module "three/examples/jsm/loaders/GLTFLoader.js" {
  export class GLTFLoader {
    loadAsync(url: string): Promise<{ scene: import("three").Group }>;
  }
}
