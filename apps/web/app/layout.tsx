import "./globals.css";
import { ThemeProvider } from "../components/theme-provider";
import { Toaster } from "sonner";
import { QueryProvider } from "../components/query-provider";
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" suppressHydrationWarning><body><ThemeProvider attribute="class" defaultTheme="system" enableSystem><QueryProvider><Toaster richColors />{children}</QueryProvider></ThemeProvider></body></html>}
