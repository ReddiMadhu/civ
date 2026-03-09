import { cn } from "../../lib/utils"

export function Card({ className, children, ...props }) {
    return (
        <div className={cn("rounded-xl border border-border bg-card text-card-foreground shadow-sm", className)} {...props}>
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
        blue: "from-blue-50 to-indigo-50 border-blue-200 text-blue-600",
        green: "from-emerald-50 to-teal-50 border-emerald-200 text-emerald-600",
        amber: "from-amber-50 to-orange-50 border-amber-200 text-amber-600",
        red: "from-rose-50 to-pink-50 border-rose-200 text-rose-600",
        purple: "from-violet-50 to-purple-50 border-violet-200 text-violet-600",
    }
    return (
        <div className={cn("rounded-xl border bg-gradient-to-br p-5 shadow-sm transition-all hover:shadow-md hover:scale-[1.02]", colors[color])}>
            <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium uppercase tracking-wider mb-1 opacity-70">{title}</p>
                    <p className="text-2xl font-bold text-foreground truncate">{value}</p>
                    {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
                </div>
                {Icon && (
                    <div className={cn("rounded-lg p-2.5 shrink-0 bg-white/60 shadow-sm")}>
                        <Icon size={20} />
                    </div>
                )}
            </div>
        </div>
    )
}

export function Badge({ children, variant = "default" }) {
    const variants = {
        default: "bg-blue-100 text-blue-700",
        success: "bg-emerald-100 text-emerald-700",
        warning: "bg-amber-100 text-amber-700",
        destructive: "bg-rose-100 text-rose-700",
        muted: "bg-gray-100 text-gray-600",
    }
    return (
        <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium", variants[variant])}>
            {children}
        </span>
    )
}
