"use client";
import {AlertCircle,LoaderCircle} from "lucide-react";
import {Button,Card} from "./ui";
export function LoadingState({label="Loading"}:{label?:string}){return <div role="status" aria-live="polite" className="flex items-center justify-center gap-2 py-12 text-sm text-muted-foreground"><LoaderCircle className="animate-spin" size={16}/>{label}<span className="sr-only">Please wait</span></div>}
export function ErrorState({message="Something went wrong",onRetry}:{message?:string;onRetry?:()=>void}){return <Card role="alert" className="p-8 text-center"><AlertCircle className="mx-auto mb-3 text-red-600" size={20}/><p className="text-sm font-medium">{message}</p>{onRetry&&<Button variant="outline" className="mt-4" onClick={onRetry}>Try again</Button>}</Card>}
export function EmptyState({title,description,action}:{title:string;description:string;action?:React.ReactNode}){return <Card className="p-10 text-center"><p className="font-medium">{title}</p><p className="mt-1 text-sm text-muted-foreground">{description}</p>{action&&<div className="mt-5">{action}</div>}</Card>}
