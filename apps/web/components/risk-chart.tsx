"use client";

import { Pie, PieChart, Cell, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["hsl(var(--status-secured))", "hsl(var(--status-review))", "hsl(var(--status-high-risk))", "hsl(var(--status-critical))"];

export function RiskChart({ values }: { values: number[] }) {
  const data = [{ name: "Low suspicion", value: values[0] }, { name: "Needs review", value: values[1] }, { name: "High suspicion", value: values[2] }, { name: "Critical", value: values[3] }];
  const total = data.reduce((sum, item) => sum + item.value, 0);
  return <div className="flex items-center gap-5"><div className="relative h-36 w-36 shrink-0"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data} dataKey="value" nameKey="name" innerRadius={46} outerRadius={63} paddingAngle={3} strokeWidth={0}>{data.map((item, index) => <Cell key={item.name} fill={COLORS[index]} opacity={item.value ? 1 : 0.15} />)}</Pie><Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(var(--border))", background: "hsl(var(--popover))", fontSize: 12 }} /></PieChart></ResponsiveContainer><div className="absolute inset-0 grid place-items-center"><div className="text-center"><div className="text-xl font-semibold">{total}</div><div className="text-[10px] text-muted-foreground">signals</div></div></div></div><div className="min-w-0 flex-1 space-y-3">{data.map((item, index) => <div key={item.name} className="flex items-center justify-between gap-3 text-xs"><span className="flex items-center gap-2 text-muted-foreground"><span className="size-2 rounded-full" style={{ background: COLORS[index] }} />{item.name}</span><span className="font-medium text-foreground">{item.value}</span></div>)}</div></div>;
}
