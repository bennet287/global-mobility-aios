"use client";

import { FormEvent, useState } from "react";
import { createLead } from "../lib/api";

export type LeadForm = {
  full_name: string;
  email: string;
  phone: string;
  source: string;
  intent: string;
  target_country: string;
  notes: string;
};

const emptyLeadForm: LeadForm = {
  full_name: "",
  email: "",
  phone: "",
  source: "web_form",
  intent: "study_abroad",
  target_country: "",
  notes: "",
};

export function useLeadForm(onSuccess: () => Promise<void>) {
  const [leadForm, setLeadForm] = useState<LeadForm>(emptyLeadForm);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);

    try {
      await createLead({
        full_name: leadForm.full_name.trim(),
        email: leadForm.email.trim() || undefined,
        phone: leadForm.phone.trim() || undefined,
        source: leadForm.source.trim() || "web_form",
        intent: leadForm.intent,
        target_country: leadForm.target_country.trim() || undefined,
        notes: leadForm.notes.trim() || undefined,
      });
      setLeadForm(emptyLeadForm);
      setMessage("Lead created. The workspace has been refreshed.");
      await onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create lead. Confirm the FastAPI backend is running.");
    }
  }

  return {
    leadForm,
    setLeadForm,
    message,
    error,
    onSubmit,
  };
}
