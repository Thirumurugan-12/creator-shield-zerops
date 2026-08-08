"use client";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { cn } from "../../lib/utils";

export const DropdownMenu = DropdownMenuPrimitive.Root;
export const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;
export function DropdownMenuContent({ className, sideOffset = 6, ...props }: React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>) { return <DropdownMenuPrimitive.Portal><DropdownMenuPrimitive.Content sideOffset={sideOffset} className={cn("z-50 min-w-40 rounded-lg border bg-popover p-1 text-popover-foreground shadow-lg", className)} {...props} /></DropdownMenuPrimitive.Portal>; }
export function DropdownMenuItem({ className, ...props }: React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item>) { return <DropdownMenuPrimitive.Item className={cn("relative flex cursor-default select-none items-center rounded-md px-2.5 py-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground", className)} {...props} />; }
export function DropdownMenuLabel({ className, ...props }: React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Label>) { return <DropdownMenuPrimitive.Label className={cn("px-2.5 py-1.5 text-xs font-medium text-muted-foreground", className)} {...props} />; }
export const DropdownMenuSeparator = DropdownMenuPrimitive.Separator;
