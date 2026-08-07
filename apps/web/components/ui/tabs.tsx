"use client";
import {createContext,useContext,useState} from "react";
import {cn} from "../../lib/utils";
type TabsContextValue={value:string;setValue:(value:string)=>void};
const TabsValueContext=createContext<TabsContextValue>({value:"",setValue:()=>{}});
export function Tabs({defaultValue,children,className}:{defaultValue:string;children:React.ReactNode;className?:string}){const [value,setValue]=useState(defaultValue);return <TabsValueContext.Provider value={{value,setValue}}><div className={className} data-tabs-value={value}>{children}</div></TabsValueContext.Provider>}
export function TabsList({children,className}:{children:React.ReactNode;className?:string}){return <div role="tablist" className={cn("inline-flex items-center gap-1 border-b",className)}>{children}</div>}
export function TabsTrigger({value,children}:{value:string;children:React.ReactNode}){const context=useContext(TabsValueContext);return <button type="button" role="tab" aria-selected={context.value===value} onClick={()=>context.setValue(value)} className={cn("border-b-2 border-transparent px-3 py-2 text-sm text-muted-foreground hover:text-foreground",context.value===value&&"border-foreground font-medium text-foreground")}>{children}</button>}
export function TabsContent({value,children,className}:{value:string;children:React.ReactNode;className?:string}){const context=useContext(TabsValueContext);return context.value===value?<div role="tabpanel" className={className}>{children}</div>:null}
