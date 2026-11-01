"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { OutreachChannel } from "@/lib/types";
import { Button, Card, ErrorBanner, PageHeader } from "@/components/ui";

export default function NewProspectPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [designation, setDesignation] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [companyWebsite, setCompanyWebsite] = useState("");
  const [industry, setIndustry] = useState("");
  const [outreachChannel, setOutreachChannel] = useState<OutreachChannel>("email");
  const [productContext, setProductContext] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const prospect = await api.createProspect({
        name,
        company,
        designation,
        linkedin_url: linkedinUrl || null,
        company_website: companyWebsite || null,
        industry: industry || null,
        outreach_channel: outreachChannel,
        product_context: productContext || null,
      });
      const run = await api.runResearch(prospect.id);
      router.push(`/executions/${run.execution_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <PageHeader
        title="Add New Prospect"
        description="Enter prospect details and start the AI research workflow."
      />

      <Card className="p-4 sm:p-6">
        <form className="space-y-4" onSubmit={handleSubmit}>
          {error && <ErrorBanner message={error} />}

          <Field label="Prospect Name" required>
            <input
              required
              minLength={2}
              className={inputClass}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jane Doe"
            />
          </Field>

          <Field label="Company" required>
            <input
              required
              minLength={2}
              className={inputClass}
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Acme Corp"
            />
          </Field>

          <Field label="Designation" required>
            <input
              required
              minLength={2}
              className={inputClass}
              value={designation}
              onChange={(e) => setDesignation(e.target.value)}
              placeholder="VP of Engineering"
            />
          </Field>

          <Field label="Industry">
            <input
              className={inputClass}
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              placeholder="SaaS"
            />
          </Field>

          <Field label="LinkedIn URL">
            <input
              type="url"
              className={inputClass}
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              placeholder="https://www.linkedin.com/in/janedoe"
            />
          </Field>

          <Field label="Company Website">
            <input
              type="url"
              className={inputClass}
              value={companyWebsite}
              onChange={(e) => setCompanyWebsite(e.target.value)}
              placeholder="https://acme.com"
            />
          </Field>

          <Field label="Preferred Outreach Channel">
            <select
              className={inputClass}
              value={outreachChannel}
              onChange={(e) => setOutreachChannel(e.target.value as OutreachChannel)}
            >
              <option value="email">Email</option>
              <option value="linkedin">LinkedIn</option>
            </select>
          </Field>

          <Field label="Product / Offering Context">
            <textarea
              className={inputClass}
              rows={3}
              value={productContext}
              onChange={(e) => setProductContext(e.target.value)}
              placeholder="AI workflow automation platform for enterprise engineering teams"
            />
          </Field>

          <Button type="submit" disabled={submitting} className="w-full">
            {submitting ? "Starting research…" : "▶ Start Research"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

const inputClass =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-accent focus:ring-1 focus:ring-accent";

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-foreground">
        {label}
        {required && <span className="text-danger"> *</span>}
      </span>
      {children}
    </label>
  );
}
