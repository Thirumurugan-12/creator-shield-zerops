import {cva,type VariantProps} from "class-variance-authority";
import {cn} from "../../lib/utils";
const buttonVariants=cva("inline-flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50",{variants:{variant:{default:"bg-primary text-primary-foreground hover:opacity-90",outline:"border bg-card hover:bg-muted",ghost:"hover:bg-muted",secondary:"bg-muted hover:opacity-80"}},defaultVariants:{variant:"default"}});
export function Button({className,variant,...props}:React.ButtonHTMLAttributes<HTMLButtonElement>&VariantProps<typeof buttonVariants>){return <button className={cn(buttonVariants({variant}),className)} {...props}/>}
