"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, ArrowUpRight, CheckCircle2, Clock3, Database, FileCheck2, Plus, ShieldCheck, Sparkles } from "lucide-react";
import { AppShell } from "../../components/app-shell";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, RiskChart } from "../../components/ui";
import { EmptyState, ErrorState, LoadingState } from "../../components/async-state";
import { getProofs } from "../../lib/api";

export default function Dashboard() {
  const query = useQuery({ queryKey: ["proofs"], queryFn: getProofs });
  const proofs = query.data || [];
  const secured = proofs.filter((proof) => proof.status === "secured").length;
  const processing = proofs.filter((proof) => proof.status === "processing").length;
  const failed = proofs.filter((proof) => proof.status === "failed").length;

  return (
    <AppShell>
      <div className="space-y-8">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground"><span className="size-1.5 rounded-full bg-secured" />Protection workspace</div>
            <h1 className="text-2xl font-semibold tracking-tight">Good morning, Maya.</h1>
            <p className="mt-2 text-sm text-muted-foreground">Your evidence workspace is ready for review.</p>
          </div>
          <Button asChild><Link href="/register"><Plus size={16} /> Secure a Reel</Link></Button>
        </div>

        <Card className="overflow-hidden border-primary/15 bg-gradient-to-br from-card via-card to-accent/30 shadow-panel">
          <div className="grid gap-8 p-6 lg:grid-cols-[1.2fr_0.8fr] lg:p-8">
            <div>
              <div className="flex items-center justify-between gap-4">
                <div><div className="flex items-center gap-2 text-sm font-semibold"><ShieldCheck className="size-4 text-secured" /> Creator protection status</div><p className="mt-1 text-sm text-muted-foreground">Technical evidence is available for every secured original.</p></div>
                <Badge tone="secured"><CheckCircle2 className="mr-1 size-3" /> All systems secured</Badge>
              </div>
              <div className="mt-8 grid grid-cols-2 gap-x-6 gap-y-6 sm:grid-cols-4"><Metric label="Originals secured" value={secured} /><Metric label="Under review" value={0} /><Metric label="High-risk" value={0} /><Metric label="Reports generated" value={0} /></div>
            </div>
            <div className="rounded-lg border bg-background/70 p-5">
              <div className="flex items-center justify-between"><div><div className="text-sm font-semibold">Evidence readiness</div><div className="mt-1 text-xs text-muted-foreground">Workspace completeness</div></div><span className="mono text-xl font-semibold">{secured ? "98%" : "—"}</span></div>
              <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full w-[98%] rounded-full bg-secured" /></div>
              <div className="mt-4 flex items-start gap-2 text-xs text-muted-foreground"><Sparkles className="mt-0.5 size-3.5 text-accent-foreground" />Hashes, media metadata, and processing events are linked to each proof.</div>
            </div>
          </div>
        </Card>

        {query.isError ? <ErrorState message="We couldn’t load your protection summary." onRetry={() => query.refetch()} /> : query.isLoading ? <LoadingState label="Loading protection summary…" /> : <DashboardContent proofs={proofs} processing={processing} failed={failed} secured={secured} />}
      </div>
    </AppShell>
  );
}

function DashboardContent({ proofs, processing, failed, secured }: { proofs: Awaited<ReturnType<typeof getProofs>>; processing: number; failed: number; secured: number }) {
  return <>
    <div className="grid gap-5 lg:grid-cols-[1.25fr_0.75fr]">
      <Card>
        <CardHeader className="border-b"><div className="flex items-center justify-between"><div><CardTitle>Recent proofs</CardTitle><CardDescription className="mt-1">Technical records from your workspace</CardDescription></div><Link className="text-xs font-medium text-accent-foreground hover:underline" href="/vault">View vault <ArrowUpRight className="ml-1 inline size-3.5" /></Link></div></CardHeader>
        {proofs.length === 0 ? <CardContent className="py-12"><EmptyState title="Protect your first Reel" description="Register an original video to create a Creator Proof record." action={<Button asChild><Link href="/register">Secure a Reel</Link></Button>} /></CardContent> : <ProofTable proofs={proofs} />}
      </Card>
      <Card><CardHeader><CardTitle>Risk distribution</CardTitle><CardDescription>Signals connected to analysed incidents</CardDescription></CardHeader><CardContent><RiskChart values={[secured, 0, failed, 0]} /></CardContent></Card>
    </div>
    <div className="grid gap-5 lg:grid-cols-2">
      <Card><CardHeader><CardTitle>Recent activity</CardTitle><CardDescription>Processing events and evidence changes</CardDescription></CardHeader><CardContent className="space-y-5">{proofs.length === 0 ? <div className="flex items-start gap-3 rounded-lg border border-dashed p-4"><Clock3 className="mt-0.5 size-4 text-muted-foreground" /><div><p className="text-sm font-medium">Your activity timeline is clear</p><p className="mt-1 text-xs text-muted-foreground">Register an original to begin collecting technical evidence.</p></div></div> : proofs.slice(0, 4).map((proof) => <div key={proof.proof_id} className="flex items-start gap-3"><span className="mt-1 grid size-6 place-items-center rounded-full bg-green-500/10"><CheckCircle2 className="size-3.5 text-secured" /></span><div><p className="text-sm">Creator Proof generated</p><p className="mono mt-1 text-[11px] text-muted-foreground">{proof.proof_id} · {new Date(proof.created_at).toLocaleString()}</p></div></div>)}</CardContent></Card>
      <Card><CardHeader><CardTitle>Workspace signals</CardTitle><CardDescription>Operational status across your evidence pipeline</CardDescription></CardHeader><CardContent className="space-y-4"><Signal icon={Database} label="Storage used" value={formatBytes(proofs.reduce((n, p) => n + p.file_size, 0))} /><Signal icon={Clock3} label="Processing jobs" value={String(processing)} tone="processing" /><Signal icon={AlertCircle} label="Failed proof jobs" value={String(failed)} tone={failed ? "risk" : "neutral"} /></CardContent></Card>
    </div>
  </>;
}

function ProofTable({ proofs }: { proofs: Awaited<ReturnType<typeof getProofs>> }) { return <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="h-11 px-4 text-left text-xs font-medium text-muted-foreground">Proof</th><th className="h-11 px-4 text-left text-xs font-medium text-muted-foreground">Status</th><th className="h-11 px-4 text-left text-xs font-medium text-muted-foreground">Registered</th><th className="h-11 px-4 text-left text-xs font-medium text-muted-foreground">Duration</th></tr></thead><tbody>{proofs.slice(0, 5).map((proof) => <tr key={proof.proof_id} className="border-b last:border-0 hover:bg-muted/50"><td className="p-4"><Link href={`/proofs/${proof.proof_id}`} className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-md bg-muted"><FileCheck2 className="size-4 text-muted-foreground" /></span><span><span className="block font-medium">{proof.title}</span><span className="mono mt-1 block text-[11px] text-muted-foreground">{proof.proof_id}</span></span></Link></td><td className="p-4"><Badge tone={proof.status === "secured" ? "secured" : proof.status === "failed" ? "risk" : "processing"}>{proof.status}</Badge></td><td className="p-4 text-xs text-muted-foreground">{new Date(proof.created_at).toLocaleDateString()}</td><td className="p-4 text-xs text-muted-foreground">{proof.duration ? `${proof.duration}s` : "Pending"}</td></tr>)}</tbody></table></div>; }
function Metric({ label, value }: { label: string; value: number }) { return <div><div className="text-2xl font-semibold tracking-tight">{value || "—"}</div><div className="mt-1 text-xs text-muted-foreground">{label}</div></div>; }
function Signal({ icon: Icon, label, value, tone = "neutral" }: { icon: typeof Database; label: string; value: string; tone?: "neutral" | "processing" | "risk" }) { return <div className="flex items-center justify-between rounded-lg border p-3"><div className="flex items-center gap-3"><Icon className={tone === "processing" ? "size-4 text-processing" : tone === "risk" ? "size-4 text-high-risk" : "size-4 text-muted-foreground"} /><span className="text-sm">{label}</span></div><span className="mono text-xs text-muted-foreground">{value}</span></div>; }
function formatBytes(n: number) { return n < 1024 * 1024 ? `${Math.round(n / 1024)} KB` : `${(n / 1024 / 1024).toFixed(1)} MB`; }
