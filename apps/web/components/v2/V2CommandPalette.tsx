"use client";

// AIOS V2 Q2 — command palette over workspace destinations and already-loaded
// registered records.
//
// The palette is presentation-only navigation:
// - it issues no requests and opens no backend writes;
// - it never claims workflow, approval or decision authority;
// - it follows only destinations that already exist in the accepted repository;
// - registered records come from pages that already loaded them.

import Link from "next/link";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  filterNavigationCommands,
  navigationCommands,
} from "../../lib/v2/navigation";
import {
  getRecentDestinations,
  recordRecentDestination,
} from "../../lib/v2/recent-destinations";
import { V2Icon } from "./V2Icon";
import { useV2Search, type V2SearchItem } from "./V2NavigationContext";

type PaletteEntry = {
  readonly key: string;
  readonly label: string;
  readonly description: string;
  readonly href: string;
  readonly icon: (typeof navigationCommands)[number]["icon"];
  readonly group: "Recent" | "Workspace" | "Record";
  readonly kind?: string;
};

function workspaceEntry(
  command: (typeof navigationCommands)[number],
  group: "Recent" | "Workspace",
): PaletteEntry {
  return {
    key: `${group.toLowerCase()}:${command.href}`,
    label: command.label,
    description: command.description,
    href: command.href,
    icon: command.icon,
    group,
  };
}

function filterSearchItems(items: readonly V2SearchItem[], query: string): V2SearchItem[] {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return [];
  return items.filter((item) => {
    const text = `${item.label} ${item.description} ${item.kind}`.toLocaleLowerCase();
    return words.every((word) => text.includes(word));
  });
}

export function V2CommandPalette({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const router = useRouter();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const { items } = useV2Search();

  const entries = useMemo<PaletteEntry[]>(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      const recentHrefs = getRecentDestinations();
      const recentSet = new Set(recentHrefs);
      const recents = recentHrefs
        .map((href) => navigationCommands.find((command) => command.href === href))
        .filter((command): command is (typeof navigationCommands)[number] => Boolean(command))
        .map((command) => workspaceEntry(command, "Recent"));
      const workspaces = navigationCommands
        .filter((command) => !recentSet.has(command.href))
        .map((command) => workspaceEntry(command, "Workspace"));
      return [...recents, ...workspaces];
    }

    const workspaces = filterNavigationCommands(trimmed).map((command) =>
      workspaceEntry(command, "Workspace"),
    );
    const records = filterSearchItems(items, trimmed).map((item) => ({
      key: `record:${item.id}`,
      label: item.label,
      description: item.description,
      href: item.href,
      icon: item.icon,
      group: "Record" as const,
      kind: item.kind,
    }));
    return [...workspaces, ...records];
  }, [items, query]);

  // Selection always starts at the first result of the current query.
  useEffect(() => {
    setSelectedIndex(0);
  }, [entries.length, query]);

  // Drive the native dialog from React state so Escape/close stay in sync.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      setQuery("");
      setSelectedIndex(0);
      searchRef.current?.focus();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  const focusEntry = (index: number) => {
    const link = dialogRef.current?.querySelector<HTMLAnchorElement>(
      `[data-palette-index="${index}"]`,
    );
    link?.focus();
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLDialogElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!entries.length) return;
      const delta = event.key === "ArrowDown" ? 1 : -1;
      const next = (selectedIndex + delta + entries.length) % entries.length;
      setSelectedIndex(next);
      focusEntry(next);
      return;
    }

    if (event.key === "Tab") {
      // Keep Tab cycling inside the palette even when the native dialog's own
      // containment reaches a boundary.
      const dialog = dialogRef.current;
      if (!dialog) return;
      const focusable = Array.from(
        dialog.querySelectorAll<HTMLElement>("input, a[href], button"),
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  };

  const resultWord = entries.length === 1 ? "destination" : "destinations";

  return (
    <dialog
      aria-label="Navigate AIOS"
      className="aios-v2-palette"
      onCancel={(event) => {
        // Route native Escape through React state so the trigger regains focus.
        event.preventDefault();
        onClose();
      }}
      onKeyDown={onKeyDown}
      ref={dialogRef}
    >
      <div className="aios-v2-palette-frame">
        <div className="aios-v2-palette-head">
          <input
            aria-label="Find a workspace"
            autoComplete="off"
            className="aios-v2-palette-search"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search workspaces and loaded records"
            ref={searchRef}
            type="search"
            value={query}
          />
          <button
            aria-label="Close navigation palette"
            className="aios-v2-palette-close"
            onClick={onClose}
            type="button"
          >
            <V2Icon name="close" width={16} height={16} />
          </button>
        </div>

        <p className="aios-v2-palette-count" role="status">
          {entries.length} {resultWord}
        </p>

        {entries.length ? (
          <div className="aios-v2-palette-list" role="listbox" aria-label="Navigation results">
            {entries.map((entry, index) => (
              <Link
                aria-selected={index === selectedIndex}
                className="aios-v2-palette-item"
                data-palette-index={index}
                data-selected={index === selectedIndex ? "true" : "false"}
                href={entry.href}
                key={entry.key}
                onClick={() => {
                  recordRecentDestination(entry.href);
                  onClose();
                }}
                onFocus={() => setSelectedIndex(index)}
                role="option"
              >
                <span className="aios-v2-palette-glyph" aria-hidden="true">
                  <V2Icon name={entry.icon} width={16} height={16} />
                </span>
                <span className="aios-v2-palette-item-copy">
                  <strong>{entry.label}</strong>
                  <small>{entry.description}</small>
                </span>
                <span className="aios-v2-palette-item-meta">{entry.kind || entry.group}</span>
              </Link>
            ))}
          </div>
        ) : (
          <p className="aios-v2-palette-empty" role="status">
            No matching destinations. Only accepted workspaces and already-loaded records are
            offered here.
          </p>
        )}
      </div>
    </dialog>
  );
}
