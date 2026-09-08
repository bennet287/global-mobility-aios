import type { SVGProps } from "react";

const paths = {
  home: "M3 10 12 3l9 7M5 9v12h5v-7h4v7h5V9",
  organization: "M9 3h6v5H9zM3 16h6v5H3zM15 16h6v5h-6zM12 8v4M6 16v-4h12v4",
  missions: "M21 12a9 9 0 1 1-9-9M17 12a5 5 0 1 1-5-5M12 12l9-9M16 3h5v5",
  intelligence: "M12 3a9 9 0 1 0 9 9M12 7a5 5 0 1 0 5 5M12 12l7-7M12 3v2M3 12h2M12 19v2",
  evidence: "M14 3H5v18h14V8zM14 3v5h5M8 14l2 2 5-5",
  decisions: "M12 3v18M5 21h14M4 7h16M6 7l-3 7h6L6 7ZM18 7l-3 7h6l-3-7Z",
  history: "M3 11a9 9 0 1 1 2 7M3 4v7h7M12 7v5l4 3",
  work: "M4 7h16v13H4zM8 7V4h8v3M4 11h16M10 14h4",
  profiles: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM4 21a8 8 0 0 1 16 0",
  pathways: "M5 5h5v5H5zM14 14h5v5h-5zM10 7.5h3a3 3 0 0 1 3 3v3.5M7.5 10v4a3 3 0 0 0 3 3H14",
  communication: "M4 5h16v12H9l-5 4V5ZM8 9h8M8 13h5",
  tools: "M14.7 6.3a4 4 0 0 0-5 5L4 17l3 3 5.7-5.7a4 4 0 0 0 5-5l-3 3-3-3 3-3Z",
  search: "M16 16l5 5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
  theme: "M12 4V2M12 22v-2M4.93 4.93 3.5 3.5M20.5 20.5l-1.43-1.43M4 12H2M22 12h-2M4.93 19.07 3.5 20.5M20.5 3.5l-1.43 1.43M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  menu: "M4 6h16M4 12h16M4 18h16",
  close: "m6 6 12 12M6 18 18 6",
  arrow: "M4 12h16M14 6l6 6-6 6",
  collapse: "M4 3h16v18H4zM9 3v18M16 9l-3 3 3 3",
} as const;

export function V2Icon({ name, ...props }: SVGProps<SVGSVGElement> & { name: keyof typeof paths }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false" {...props}>
      <path d={paths[name]} />
    </svg>
  );
}
