import "../../../styles/v2/tokens.css";
import "../../../styles/v2/motion.css";
import "../../../styles/v2/foundation.css";
import "../../../styles/v2/command-search.css";

import { V2NavigationContext } from "../../../components/v2/V2NavigationContext";

export default function AiosV2PrototypeLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <V2NavigationContext>{children}</V2NavigationContext>;
}
