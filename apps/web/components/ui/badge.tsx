import { cn } from "../../lib/utils";

const tones = {
  neutral: "border-transparent bg-muted text-muted-foreground",
  secured: "border-foreground/20 bg-foreground/5 text-foreground",
  processing: "border-muted-foreground/25 bg-muted text-foreground",
  review: "border-muted-foreground/35 bg-muted text-foreground",
  risk: "border-foreground/30 bg-foreground/10 text-foreground",
} as const;

export function Badge({ children, tone = "neutral", className }: { children: React.ReactNode; tone?: keyof typeof tones; className?: string }) {
  return <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium", tones[tone], className)}>{children}</span>;
}
