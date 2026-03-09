import { cn } from "../lib/utils"

export function Card({ className, children, ...props }) {
    return (
        <div className={cn("rounded-xl border border-border bg-card text-card-foreground shadow-lg", className)} {...props}>
            {children}
        </div>
    )
}

export function CardHeader({ className, children }) {
    return <div className={cn("flex flex-col space-y-1 p-6", className)}>{children}</div>
}

export function CardTitle({ className, children }) {
    return <h3 className={cn("text-lg font-semibold leading-none tracking-tight", className)}>{children}</h3>
}

export function CardContent({ className, children }) {
    return <div className={cn("p-6 pt-0", className)}>{children}</div>
}

export function KPICard({ title, value, subtitle, icon: Icon, color = "blue" }) {
    const colors = {
        blue: "from-blue-500/20 to-blue-600/5 border-blue-500/30 text-blue-400",
        green: "from-emerald-500/20 to-emerald-600/5 border-emerald-500/30 text-emerald-400",
        amber: "from-amber-500/20 to-amber-600/5 border-amber-500/30 text-amber-400",
        red: "from-red-500/20 to-red-600/5 border-red-500/30 text-red-400",
        purple: "from-purple-500/20 to-purple-600/5 border-purple-500/30 text-purple-400",
    }
    return (
        <div className={cn("rounded-xl border bg-gradient-to-br p-5 shadow-lg transition-all hover:scale-[1.02]", colors[color])}>
            <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">{title}</p>
                    <p className="text-2xl font-bold text-foreground truncate">{value}</p>
                    {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
                </div>
                {Icon && (
                    <div className="rounded-lg bg-white/10 p-2.5 shrink-0">
                        <Icon size={20} className={colors[color].split(" ").at(-1)} />
                    </div>
                )}
            </div>
        </div>
    )
}

export function Badge({ children, variant = "default" }) {
    const variants = {
        default: "bg-primary/20 text-primary",
        success: "bg-emerald-500/20 text-emerald-400",
        warning: "bg-amber-500/20 text-amber-400",
        destructive: "bg-red-500/20 text-red-400",
        muted: "bg-muted text-muted-foreground",
    }
    return (
        <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium", variants[variant])}>
            {children}
        </span>
    )
}
