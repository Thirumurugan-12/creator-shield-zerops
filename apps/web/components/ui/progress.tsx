import {cn} from "../../lib/utils";
export function Progress({value=0,className}:{value?:number;className?:string}){return <div role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={value} className={cn("h-2 w-full overflow-hidden rounded-full bg-muted",className)}><div className="h-full bg-blue-600 transition-all" style={{width:`${Math.max(0,Math.min(100,value))}%`}}/></div>}
