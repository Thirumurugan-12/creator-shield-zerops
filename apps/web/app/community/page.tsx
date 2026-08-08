"use client";

import Link from "next/link";
import { ArrowUpRight, Fingerprint, Info, Users } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "../../components/app-shell";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "../../components/ui";
import { EmptyState, ErrorState, LoadingState } from "../../components/async-state";
import { getIncidents } from "../../lib/api";

export default function Community() {
  const query = useQuery({ queryKey: ["community-incidents"], queryFn: getIncidents });
  const incidents = query.data || [];
  const matches = incidents.flatMap((incident) => incident.community_matches.map((match) => ({ ...match, incident }))).slice(0, 12);
  const totals = incidents.reduce((sum, incident) => sum + (incident.community_summary.related_report_count || 0), 0);

  return <AppShell><div className="flex items-end justify-between gap-4"><div><p className="text-sm text-muted-foreground">Shared abuse signals</p><h1 className="mt-1 text-2xl font-semibold">Community Intelligence</h1><p className="mt-2 max-w-2xl text-sm text-muted-foreground">Connect repeated identifiers and wording across reviewed incidents while keeping every conclusion explicitly scoped.</p></div><Users className="hidden size-8 text-muted-foreground sm:block" /></div><Card className="mt-8 border-dashed"><CardContent className="flex items-start gap-3 p-5 text-sm"><Info className="mt-0.5 size-4 shrink-0 text-muted-foreground" /><p className="text-muted-foreground">Development reports are simulated signals for the demo. They are useful for pattern discovery, not proof of wrongdoing.</p></CardContent></Card>{query.isLoading ? <LoadingState label="Loading community signals…" /> : query.isError ? <div className="mt-8"><ErrorState message="We couldn’t load community signals." onRetry={() => query.refetch()} /></div> : incidents.length === 0 ? <div className="mt-8"><EmptyState title="No shared signals yet" description="Create an incident to compare its complaint indicators with the community signal index." action={<Button asChild><Link href="/incidents/new">Create incident</Link></Button>} /></div> : <div className="mt-5 grid gap-5 lg:grid-cols-[0.8fr_1.2fr]"><Card><CardHeader><CardTitle>Signal index</CardTitle></CardHeader><CardContent className="space-y-4"><Metric label="Reviewed incidents" value={incidents.length} /><Metric label="Related simulated reports" value={totals} /><Metric label="Matched identifiers" value={matches.length} /></CardContent></Card><Card><CardHeader><CardTitle>Recent matches</CardTitle></CardHeader><CardContent className="space-y-3">{matches.length ? matches.map((match) => <div key={`${match.incident.incident_id}-${match.report_id}`} className="flex items-start justify-between gap-4 rounded-lg border p-4"><div className="flex items-start gap-3"><Fingerprint className="mt-0.5 size-4 text-muted-foreground" /><div><div className="mono text-xs text-muted-foreground">{match.identifier}</div><div className="mt-1 text-sm">{match.matched_value}</div><div className="mt-1 text-xs text-muted-foreground">Linked from {match.incident.incident_id}</div></div></div><Link href={`/incidents/${match.incident.incident_id}`} aria-label={`Open ${match.incident.incident_id}`}><ArrowUpRight className="size-4 text-muted-foreground" /></Link></div>) : <p className="text-sm text-muted-foreground">No exact matches found yet; the index will update as comparisons complete.</p>}</CardContent></Card></div>}</AppShell>;
}

function Metric({ label, value }: { label: string; value: number }) { return <div className="flex items-end justify-between border-b pb-3 last:border-0 last:pb-0"><span className="text-sm text-muted-foreground">{label}</span><span className="mono text-xl font-semibold">{value || "—"}</span></div>; }
