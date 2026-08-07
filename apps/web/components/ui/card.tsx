import {cn} from "../../lib/utils";
export function Card({children,className,...props}:React.HTMLAttributes<HTMLElement>){return <section className={cn("rounded-xl border bg-card",className)} {...props}>{children}</section>}
