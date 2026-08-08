"use client";

import Link from "next/link";
import { FileText, ArrowUpRight, Download } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "../../components/app-shell";
import { Badge, Button, Card } from "../../components/ui";
import { EmptyState, ErrorState, LoadingState } from "../../components/async-state";
import { getIncidents } from "../../lib/api";

export default function Reports() {
  const query = useQuery({ queryKey: ["reports-incidents"], queryFn: getIncidents });
  const incidents = query.data || [];

  return <AppShell>
    <div className="flex items-end justify-between gap-4">
      <div><p className="text-sm text-muted-foreground">Court-ready evidence</p><h1 className="mt-1 text-2xl font-semibold">Reports</h1><p className="mt-2 text-sm text-muted-foreground">Generate a traceable evidence package for every reviewed incident.</p></div>
      <FileText className="hidden size-8 text-muted-foreground sm:block" />
    </div>
    {query.isLoading ? <LoadingState label="Loading report index…" /> : query.isError ? <div className="mt-8"><ErrorState message="We couldn’t load your reports." onRetry={() => query.refetch()} /></div> : incidents.length === 0 ? <div className="mt-8"><EmptyState title="No reports yet" description="Complete an incident comparison to generate your first evidence report." action={<Button asChild><Link href="/incidents/new">Create incident</Link></Button>} /></div> : <div className="mt-8 space-y-3">{incidents.map((incident) => <Card key={incident.incident_id} className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-start gap-3"><span className="grid size-9 place-items-center rounded-md bg-muted"><FileText className="size-4 text-muted-foreground" /></span><div><div className="mono text-xs text-muted-foreground">{incident.incident_id}</div><div className="mt-1 text-sm font-medium">{incident.suspicious_filename}</div><div className="mt-1 text-xs text-muted-foreground">{new Date(incident.created_at).toLocaleDateString()} · {incident.suspicious_username}</div></div></div><div className="flex items-center gap-3"><Badge tone={incident.suspicion_band === "high" ? "risk" : "processing"}>{incident.suspicion_band || incident.status}</Badge><Button variant="outline" size="sm" asChild><Link href={`/reports/${incident.incident_id}`}><ArrowUpRight className="size-3.5" />Preview</Link></Button><Button variant="ghost" size="icon" asChild><a href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/incidents/${incident.incident_id}/report.pdf`} aria-label={`Download ${incident.incident_id} report`}><Download className="size-4" /></a></Button></div></Card>)}</div>}
  </AppShell>;
}
