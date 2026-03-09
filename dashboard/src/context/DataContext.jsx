import { createContext, useContext, useState, useEffect, useCallback } from "react"
import Papa from "papaparse"

const DataContext = createContext(null)

// Compute CLV per policy: CLV = (Premium - Expenses - Loss) * RenewalFlag / (1 + 0.08)^1
function computeCLV(row) {
    const premium = parseFloat(row.DIRECTWRITTENPREMIUM_AM) || 0
    const commission = parseFloat(row.COMMISSION_EXPENSE_AM) || 0
    const admin = parseFloat(row.ADMIN_EXPENSE_AM) || 0
    const loss = parseFloat(row.NETLOSS_PAID_AM) || 0
    const renewed = row.POLICY_RENEWED_FLAG === "True" || row.POLICY_RENEWED_FLAG === true || row.POLICY_RENEWED_FLAG === "1" ? 1 : 0
    const r = 0.08
    const profit = premium - commission - admin - loss
    return parseFloat(((profit * renewed) / (1 + r)).toFixed(2))
}

export function DataProvider({ children }) {
    const [data, setData] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [progress, setProgress] = useState(0)

    useEffect(() => {
        let rows = []
        Papa.parse("/clv_data.csv", {
            download: true,
            header: true,
            dynamicTyping: false,
            skipEmptyLines: true,
            step: (result) => {
                const row = result.data
                row._clv = computeCLV(row)
                rows.push(row)
                if (rows.length % 5000 === 0) setProgress(Math.round((rows.length / 50000) * 100))
            },
            complete: () => {
                setData(rows)
                setLoading(false)
                setProgress(100)
            },
            error: (err) => {
                setError(err.message)
                setLoading(false)
            }
        })
    }, [])

    return (
        <DataContext.Provider value={{ data, loading, error, progress }}>
            {children}
        </DataContext.Provider>
    )
}

export function useData() {
    return useContext(DataContext)
}
