import { cn } from "../lib/utils"
import { BarChart3, Database, TrendingUp, Home, ChevronRight } from "lucide-react"

const NAV = [
    { id: "overview", label: "Overview", icon: Home },
    { id: "data", label: "Data Table", icon: Database },
    { id: "eda", label: "EDA Analysis", icon: BarChart3 },
    { id: "clv", label: "CLV Analysis", icon: TrendingUp },
]

export function Sidebar({ active, setActive }) {
    return (
        <aside className="w-56 shrink-0 flex flex-col h-screen border-r border-border bg-white py-6 sticky top-0">
            {/* Logo */}
            <div className="px-5 mb-8">
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-md">CLV</div>
                    <div>
                        <p className="text-sm font-bold text-foreground">InsureLab</p>
                        <p className="text-[10px] text-muted-foreground">Property Analytics</p>
                    </div>
                </div>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-3 space-y-1">
                {NAV.map(({ id, label, icon: Icon }) => (
                    <button key={id} onClick={() => setActive(id)}
                        className={cn(
                            "w-full flex items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                            active === id
                                ? "bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 shadow-sm"
                                : "text-muted-foreground hover:bg-gray-50 hover:text-foreground"
                        )}>
                        <span className="flex items-center gap-2.5">
                            <Icon size={16} />
                            {label}
                        </span>
                        {active === id && <ChevronRight size={14} className="opacity-60" />}
                    </button>
                ))}
            </nav>

            <div className="px-5 mt-auto">
                <p className="text-[10px] text-muted-foreground">50,000 policies • 38 columns</p>
            </div>
        </aside>
    )
}
