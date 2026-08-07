import {cn} from "../../lib/utils";
export function Textarea({className,...props}:React.TextareaHTMLAttributes<HTMLTextAreaElement>){return <textarea className={cn("flex min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-50",className)} {...props}/>}
