import { useMemo } from "react"
import { useData } from "../context/DataContext"
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card"
import { STATE_NAMES, fmtDollar, fmtPct } from "../lib/utils"
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
    PieChart, Pie, Cell, Legend, ScatterChart, Scatter, LineChart, Line,
} from "recharts"

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#a855f7", "#06b6d4"]
const TT_STYLE = { backgroundColor: "#1e2535", border: "1px solid #2d3a52", borderRadius: 8, color: "#e2e8f0", fontSize: 12 }

export default function EDA() {
    const { data, loading } = useData()

    const stats = useMemo(() => {
        if (!data.length) return null

        // 1. Loss ratio by state
        const stateAgg = {}
        data.forEach(r => {
            const s = r.POLICYRATEDSTATE_TP
            if (!stateAgg[s]) stateAgg[s] = { earned: 0, loss: 0, count: 0, premSum: 0 }
            stateAgg[s].earned += (+r.EARNEDPREMIUM_AM || 0)
            stateAgg[s].loss += (+r.NETLOSS_PAID_AM || 0)
            stateAgg[s].count += 1
            stateAgg[s].premSum += (+r.DIRECTWRITTENPREMIUM_AM || 0)
        })
        const lrByState = Object.entries(stateAgg).map(([k, v]) => ({
            state: STATE_NAMES[k] || k,
            lossRatio: +(v.loss / v.earned * 100).toFixed(1),
            avgPrem: +(v.premSum / v.count).toFixed(0),
            count: v.count,
        })).sort((a, b) => b.lossRatio - a.lossRatio)

        // 2. Premium distribution (buckets)
        const buckets = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
        const premDist = buckets.map((b, i) => {
            const lo = i === 0 ? 0 : buckets[i - 1]
            const cnt = data.filter(r => +r.DIRECTWRITTENPREMIUM_AM >= lo && +r.DIRECTWRITTENPREMIUM_AM < b).length
            return { range: `$${(lo / 1000).toFixed(0)}K-$${(b / 1000).toFixed(0)}K`, count: cnt }
        })
        premDist.push({ range: "$4K+", count: data.filter(r => +r.DIRECTWRITTENPREMIUM_AM >= 4000).length })

        // 3. Construction type distribution
        const constMap = { 1: "Frame", 2: "Masonry", 4: "Manufactured", 6: "Superior" }
        const constAgg = {}
        data.forEach(r => { const c = constMap[r.CONSTRUCTION_TP] || r.CONSTRUCTION_TP; constAgg[c] = (constAgg[c] || 0) + 1 })
        const constDist = Object.entries(constAgg).map(([name, value]) => ({ name, value }))

        // 4. Credit tier distribution
        const creditMap = { "INTRNL06": "Elite", "ASSIST01": "Average", "ASSIST03": "Subprime" }
        const creditAgg = {}
        data.forEach(r => { const c = creditMap[r.CREDITMODEL_CD] || r.CREDITMODEL_CD; creditAgg[c] = (creditAgg[c] || 0) + 1 })
        const creditDist = Object.entries(creditAgg).map(([name, value]) => ({ name, value }))

        // 5. Claim freq by merit point
        const meritAgg = {}
        data.forEach(r => {
            const m = +r.MERITPOINT_CT
            if (!meritAgg[m]) meritAgg[m] = { claims: 0, total: 0 }
            meritAgg[m].total++
            if (+r.CLAIMCOUNT_CT > 0) meritAgg[m].claims++
        })
        const meritFreq = Object.entries(meritAgg).map(([k, v]) => ({ merit: +k, freq: +(v.claims / v.total * 100).toFixed(1) })).sort((a, b) => a.merit - b.merit)

        // 6. Home age vs avg loss (bucketed)
        const ageBuckets = [[0, 10], [10, 20], [20, 30], [30, 40], [40, 50], [50, 60], [60, 75], [75, 100]]
        const ageLoss = ageBuckets.map(([lo, hi]) => {
            const bucket = data.filter(r => +r.HOME_AGE_YR >= lo && +r.HOME_AGE_YR < hi)
            const avgLoss = bucket.length ? bucket.reduce((s, r) => s + (+r.GROSSLOSSPAIO_AM || 0), 0) / bucket.length : 0
            return { range: `${lo}-${hi}yr`, avgLoss: +avgLoss.toFixed(0) }
        })

        // 7. Channel distribution
        const channelAgg = {}
        data.forEach(r => { channelAgg[r.AGENT_CHANNEL] = (channelAgg[r.AGENT_CHANNEL] || 0) + 1 })
        const channelDist = Object.entries(channelAgg).map(([name, value]) => ({ name, value }))

        // 8. Renewal rate by credit
        const renewByCredit = Object.entries(creditMap).map(([code, label]) => {
            const subset = data.filter(r => r.CREDITMODEL_CD === code)
            const rate = subset.length ? subset.filter(r => r.POLICY_RENEWED_FLAG === "True" || r.POLICY_RENEWED_FLAG === "1").length / subset.length * 100 : 0
            return { credit: label, renewRate: +rate.toFixed(1) }
        })

        return { lrByState, premDist, constDist, creditDist, meritFreq, ageLoss, channelDist, renewByCredit }
    }, [data])

    if (loading || !stats) {
        return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading data…</div>
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-foreground">EDA Analysis</h1>
                <p className="text-muted-foreground text-sm mt-1">Exploratory data analysis across all 50,000 policies</p>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

                {/* Loss Ratio by State */}
                <Card>
                    <CardHeader><CardTitle>Loss Ratio by State (%)</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={stats.lrByState} barSize={28}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2d3a52" />
                                <XAxis dataKey="state" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} unit="%" domain={[0, 100]} />
                                <Tooltip contentStyle={TT_STYLE} formatter={v => [v + "%", "Loss Ratio"]} />
                                <Bar dataKey="lossRatio" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Premium Distribution */}
                <Card>
                    <CardHeader><CardTitle>Premium Distribution</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={stats.premDist} barSize={28}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2d3a52" />
                                <XAxis dataKey="range" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                                <Tooltip contentStyle={TT_STYLE} formatter={v => [v.toLocaleString(), "Policies"]} />
                                <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Credit Tier Pie */}
                <Card>
                    <CardHeader><CardTitle>Credit Tier Distribution</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <PieChart>
                                <Pie data={stats.creditDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                                    {stats.creditDist.map((_, i) => <Cell key={i} fill={["#3b82f6", "#f59e0b", "#ef4444"][i]} />)}
                                </Pie>
                                <Tooltip contentStyle={TT_STYLE} />
                            </PieChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Construction Type Pie */}
                <Card>
                    <CardHeader><CardTitle>Construction Type Mix</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <PieChart>
                                <Pie data={stats.constDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                                    {stats.constDist.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                                </Pie>
                                <Tooltip contentStyle={TT_STYLE} />
                            </PieChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Claim Freq by Merit Point */}
                <Card>
                    <CardHeader><CardTitle>Claim Frequency by Merit Point</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <LineChart data={stats.meritFreq}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2d3a52" />
                                <XAxis dataKey="merit" label={{ value: "Merit Score", position: "insideBottom", offset: -2, fill: "#94a3b8", fontSize: 11 }} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} unit="%" />
                                <Tooltip contentStyle={TT_STYLE} formatter={v => [v + "%", "Claim Freq"]} />
                                <Line type="monotone" dataKey="freq" stroke="#a855f7" strokeWidth={2} dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Home Age vs Avg Gross Loss */}
                <Card>
                    <CardHeader><CardTitle>Avg Gross Loss by Home Age</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={stats.ageLoss} barSize={28}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2d3a52" />
                                <XAxis dataKey="range" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickFormatter={v => "$" + Math.round(v / 1000) + "K"} />
                                <Tooltip contentStyle={TT_STYLE} formatter={v => ["$" + v.toLocaleString(), "Avg Gross Loss"]} />
                                <Bar dataKey="avgLoss" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Renewal Rate by Credit */}
                <Card>
                    <CardHeader><CardTitle>Renewal Rate by Credit Tier</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={stats.renewByCredit} barSize={40}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2d3a52" />
                                <XAxis dataKey="credit" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} unit="%" domain={[0, 100]} />
                                <Tooltip contentStyle={TT_STYLE} formatter={v => [v + "%", "Renewal Rate"]} />
                                <Bar dataKey="renewRate" radius={[4, 4, 0, 0]}>
                                    {stats.renewByCredit.map((_, i) => <Cell key={i} fill={["#3b82f6", "#f59e0b", "#ef4444"][i]} />)}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Agent Channel Pie */}
                <Card>
                    <CardHeader><CardTitle>Agent Channel Distribution</CardTitle></CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={220}>
                            <PieChart>
                                <Pie data={stats.channelDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80}
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                                    {stats.channelDist.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                                </Pie>
                                <Legend iconType="circle" formatter={v => <span className="text-muted-foreground text-xs">{v}</span>} />
                                <Tooltip contentStyle={TT_STYLE} />
                            </PieChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
