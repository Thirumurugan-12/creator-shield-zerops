"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { useQuery } from "@tanstack/react-query";
import { Check, Settings2 } from "lucide-react";
import { AppShell } from "../../components/app-shell";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "../../components/ui";
import { ErrorState, LoadingState } from "../../components/async-state";
import { getMe } from "../../lib/api";

export default function Settings() {
  const { theme, setTheme } = useTheme();
  const [saved, setSaved] = useState(false);
  const query = useQuery({ queryKey: ["me"], queryFn: getMe });
  useEffect(() => { setSaved(false); }, [theme]);
  if (query.isLoading) return <AppShell><LoadingState label="Loading workspace settings…" /></AppShell>;
  if (query.isError || !query.data) return <AppShell><ErrorState message="We couldn’t load your workspace settings." onRetry={() => query.refetch()} /></AppShell>;
  return <AppShell><div><p className="text-sm text-muted-foreground">Workspace controls</p><h1 className="mt-1 text-2xl font-semibold">Settings</h1><p className="mt-2 text-sm text-muted-foreground">Review your demo identity and presentation preferences.</p></div><div className="mt-8 grid gap-5 lg:grid-cols-2"><Card><CardHeader><CardTitle>Creator profile</CardTitle></CardHeader><CardContent className="space-y-4"><Row label="Display name" value={query.data.display_name} /><Row label="Instagram" value={`@${query.data.instagram_username}`} /><Row label="Email" value={query.data.email} /><Badge tone="secured"><Check className="mr-1 size-3" />Session active</Badge></CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2"><Settings2 className="size-4" />Appearance</CardTitle></CardHeader><CardContent><p className="text-sm text-muted-foreground">CreatorShield uses a strict black-and-white workspace for clear evidence review.</p><div className="mt-5 grid grid-cols-3 gap-2">{(["light", "dark", "system"] as const).map((option) => <Button key={option} variant={theme === option ? "default" : "outline"} onClick={() => { setTheme(option); setSaved(true); }}>{option[0].toUpperCase() + option.slice(1)}</Button>)}</div>{saved && <p className="mt-4 text-xs text-muted-foreground">Appearance preference saved locally.</p>}</CardContent></Card></div></AppShell>;
}

function Row({ label, value }: { label: string; value: string }) { return <div className="flex flex-col gap-1 border-b pb-3 last:border-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between"><span className="text-sm text-muted-foreground">{label}</span><span className="mono text-sm">{value}</span></div>; }
