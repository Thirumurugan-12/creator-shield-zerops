"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Bell, Command, FileText, LayoutDashboard, LogOut, Menu, Moon, Search, Settings, ShieldCheck, Sun, Users, X } from "lucide-react";
import { AuthGuard } from "./auth-guard";
import { cn } from "../lib/utils";
import { getProofs, logout } from "../lib/api";
import { Avatar, AvatarFallback, Button, DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "./ui";

export const nav = [["Dashboard", "/dashboard", LayoutDashboard], ["Proof Vault", "/vault", ShieldCheck], ["Incidents", "/incidents", AlertTriangle], ["Reports", "/reports", FileText], ["Community Intelligence", "/community", Users]] as const;
const labels: Record<string, string> = { dashboard: "Dashboard", vault: "Proof Vault", incidents: "Incidents", reports: "Reports", community: "Community Intelligence", settings: "Settings" };

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname(); const { theme, setTheme } = useTheme(); const router = useRouter(); const queryClient = useQueryClient();
  const [mobileOpen, setMobileOpen] = useState(false); const [commandOpen, setCommandOpen] = useState(false);
  const proofQuery = useQuery({ queryKey: ["shell-proofs"], queryFn: getProofs, staleTime: 2000 });
  useEffect(() => { const onKey = (event: KeyboardEvent) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setCommandOpen(true); } if (event.key === "Escape") { setCommandOpen(false); setMobileOpen(false); } }; window.addEventListener("keydown", onKey); return () => window.removeEventListener("keydown", onKey); }, []);
  async function signOut() { await logout(); queryClient.clear(); router.replace("/login"); }
  const currentLabel = labels[path?.split("/")[1] || "dashboard"] || "Workspace";
  const processingCount = proofQuery.data?.filter((proof) => proof.status === "processing").length || 0;
  return <AuthGuard><div className="min-h-screen md:flex">
    <aside className="hidden w-[248px] shrink-0 border-r bg-card/70 p-4 md:flex md:flex-col">
      <Link href="/dashboard" className="flex items-center gap-2 px-2 text-sm font-semibold"><span className="grid size-7 place-items-center rounded-md bg-primary text-primary-foreground shadow-sm"><ShieldCheck size={15} /></span><span>CreatorShield</span></Link>
      <div className="mt-8 px-2 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">Workspace</div>
      <Navigation path={path} />
      <div className="mt-auto border-t pt-4">
        <Link href="/settings" className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"><Settings size={16} />Settings</Link>
        <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")} className="mt-1 flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground">{theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}Theme: {theme || "system"}</button>
        <div className="mt-4 flex items-center gap-3 border-t px-2 pt-4"><Avatar><AvatarFallback>TC</AvatarFallback></Avatar><div className="min-w-0"><div className="truncate text-sm font-medium">Thiru</div><div className="mono truncate text-[11px] text-muted-foreground">@thiru.creates</div></div><button aria-label="Sign out" onClick={signOut} className="ml-auto text-muted-foreground hover:text-foreground"><LogOut size={14} /></button></div>
      </div>
    </aside>
    {mobileOpen && <div className="fixed inset-0 z-40 md:hidden"><button aria-label="Close navigation" className="absolute inset-0 bg-black/30" onClick={() => setMobileOpen(false)} /><aside className="relative z-10 flex h-full w-72 flex-col border-r bg-card p-4"><div className="flex items-center justify-between"><Link href="/dashboard" className="flex items-center gap-2 text-sm font-semibold"><span className="grid size-7 place-items-center rounded-md bg-primary text-primary-foreground"><ShieldCheck size={15} /></span>CreatorShield</Link><Button variant="ghost" size="icon" aria-label="Close navigation" onClick={() => setMobileOpen(false)}><X size={18} /></Button></div><Navigation path={path} onNavigate={() => setMobileOpen(false)} /></aside></div>}
    <main className="min-w-0 flex-1">
      <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background/90 px-5 backdrop-blur-md md:px-8"><div className="flex items-center gap-3"><Button variant="ghost" size="icon" className="md:hidden" aria-label="Open navigation" onClick={() => setMobileOpen(true)}><Menu size={18} /></Button><div className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex"><span>Workspace</span><span>/</span><span className="text-foreground">{currentLabel}</span></div><span className="text-sm font-medium sm:hidden">{currentLabel}</span></div><div className="flex items-center gap-2"><button aria-label="Open command menu" onClick={() => setCommandOpen(true)} className="hidden items-center gap-2 rounded-md border bg-card px-2.5 py-1.5 text-xs text-muted-foreground shadow-sm hover:bg-muted sm:flex"><Search size={13} />Search<kbd className="mono rounded border px-1 text-[10px]">⌘K</kbd></button><Button variant="ghost" size="icon" aria-label="Notifications" title="No new notifications"><Bell size={16} /></Button><div className="hidden items-center gap-2 border-l pl-3 lg:flex"><span className="text-xs text-muted-foreground">Processing jobs</span><span className="rounded-md bg-accent px-2 py-1 text-xs font-medium text-accent-foreground">{processingCount}</span></div><DropdownMenu><DropdownMenuTrigger asChild><button aria-label="Open user menu"><Avatar><AvatarFallback>TC</AvatarFallback></Avatar></button></DropdownMenuTrigger><DropdownMenuContent align="end"><DropdownMenuLabel>Thiru<br /><span className="mono text-[10px] font-normal text-muted-foreground">@thiru.creates</span></DropdownMenuLabel><DropdownMenuSeparator className="my-1 h-px bg-border" /><DropdownMenuItem onClick={() => router.push("/settings")}><Settings className="mr-2 size-4" />Settings</DropdownMenuItem><DropdownMenuItem onClick={signOut}><LogOut className="mr-2 size-4" />Sign out</DropdownMenuItem></DropdownMenuContent></DropdownMenu></div></header>
      <div className="mx-auto max-w-[1600px] p-5 md:p-8">{children}</div>
    </main>
    {commandOpen && <CommandMenu close={() => setCommandOpen(false)} />}
  </div></AuthGuard>;
}

function Navigation({ path, onNavigate }: { path: string | null; onNavigate?: () => void }) { return <nav className="mt-3 space-y-1">{nav.map(([label, href, Icon]) => <Link onClick={onNavigate} key={href} href={href} className={cn("flex items-center gap-3 rounded-md px-3 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground", path === href && "bg-accent font-medium text-accent-foreground")}>{<Icon size={16} />}{label}</Link>)}</nav>; }

function CommandMenu({ close }: { close: () => void }) { const router = useRouter(); const [query, setQuery] = useState(""); const results = useMemo(() => nav.filter(([label]) => label.toLowerCase().includes(query.toLowerCase())), [query]); return <div className="fixed inset-0 z-50 grid place-items-start bg-black/30 p-5 pt-[14vh]" onMouseDown={(event) => { if (event.currentTarget === event.target) close(); }}><div role="dialog" aria-modal="true" aria-label="Command menu" className="w-full max-w-lg overflow-hidden rounded-xl border bg-popover shadow-panel"><div className="flex items-center gap-3 border-b px-4"><Command size={17} className="text-muted-foreground" /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search workspace" className="w-full bg-transparent py-4 text-sm outline-none" /><kbd className="mono text-[10px] text-muted-foreground">ESC</kbd></div><div className="p-2">{results.length ? results.map(([label, href, Icon]) => <button key={href} onClick={() => { close(); router.push(href); }} className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left text-sm hover:bg-muted"><Icon size={16} className="text-muted-foreground" />{label}<span className="ml-auto text-xs text-muted-foreground">Open</span></button>) : <p className="p-4 text-sm text-muted-foreground">No matching workspace destination.</p>}</div></div></div>; }
