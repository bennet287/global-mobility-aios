"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AgentChatResponse,
  chatWithAgent,
  ConsultantDecision,
  runControlledAgent,
} from "../lib/api";
import { titleCase } from "../lib/utils";

type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string; decision?: ConsultantDecision };

export function AgentChatWidget({ leadHint }: { leadHint?: string }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm the in-house consultant. Tell me what you'd like to do (e.g. 'draft a follow-up for Bennet') and I'll route it to the right agent.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const clientFacingRoute = pathname.startsWith("/portal")
    || pathname.startsWith("/return")
    || pathname.startsWith("/partner-portal");

  useEffect(() => {
    if (open && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, open]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setLoading(true);

    try {
      const history = messages
        .filter((m): m is Message => Boolean(m))
        .map((m) => ({ role: m.role, content: m.content }));
      const res: AgentChatResponse = await chatWithAgent(userText, history, leadHint);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.reply, decision: res.decision },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat request failed");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (decision: ConsultantDecision) => {
    if (!decision.agent_name || !decision.lead_id || !decision.task_template) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runControlledAgent({
        agent_name: decision.agent_name,
        task: decision.task_template,
        lead_id: decision.lead_id,
        actor: "insider_chatbot",
      });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Queued **${titleCase(decision.agent_name!)}** for lead ${decision.lead_id!.slice(0, 8)}. Run ID: \`${res.run_id}\`. You can review the output in the queue.`,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to queue agent run");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "Got it. Let me know if you'd like to do something else." },
    ]);
  };

  if (clientFacingRoute) return null;

  return (
    <div className={`agent-chat-widget ${open ? "open" : ""}`}>
      {open && (
        <div className="agent-chat-panel">
          <div className="agent-chat-header">
            <strong>In-House Consultant</strong>
            <button onClick={() => setOpen(false)} aria-label="Close chat">
              ✕
            </button>
          </div>
          <div className="agent-chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`agent-chat-message ${msg.role}`}>
                <div className="agent-chat-bubble">
                  {msg.role === "assistant" && <span className="chat-avatar">AI</span>}
                  <div className="chat-content">
                    <p>{msg.content}</p>
                    {msg.role === "assistant" && msg.decision?.decision === "propose_action" && (
                      <div className="agent-chat-proposal">
                        <div className="proposal-meta">
                          <span className="proposal-agent">{titleCase(msg.decision.agent_name || "")}</span>
                          <span className="proposal-lead">{msg.decision.lead_id?.slice(0, 8) || "—"}</span>
                        </div>
                        <p className="proposal-task">{msg.decision.task_template}</p>
                        <div className="proposal-actions">
                          <button
                            className="button primary"
                            disabled={loading}
                            onClick={() => handleConfirm(msg.decision!)}
                          >
                            Confirm
                          </button>
                          <button className="button secondary" disabled={loading} onClick={handleCancel}>
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                    {msg.role === "assistant" && msg.decision?.decision === "wait_for_human" && (
                      <div className="agent-chat-links">
                        <Link href="/agents/console" onClick={() => setOpen(false)}>
                          Open Agent Console
                        </Link>
                        <Link href="/agents/review" onClick={() => setOpen(false)}>
                          Open Review Queue
                        </Link>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {error && <div className="agent-chat-error">{error}</div>}
            <div ref={bottomRef} />
          </div>
          <div className="agent-chat-input">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask the consultant..."
              disabled={loading}
            />
            <button className="button primary" onClick={handleSend} disabled={loading || !input.trim()}>
              Send
            </button>
          </div>
        </div>
      )}
      <button className="agent-chat-fab" onClick={() => setOpen((o) => !o)} aria-label="Open consultant chat">
        <span>{open ? "✕" : "💬"}</span>
      </button>
    </div>
  );
}
