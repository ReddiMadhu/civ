import { useState } from "react"
import { DataProvider, useData } from "./context/DataContext"
import { Sidebar } from "./components/Sidebar"
import Overview from "./pages/Overview"
import DataTablePage from "./pages/DataTablePage"
import EDA from "./pages/EDA"
import CLVPage from "./pages/CLVPage"

function LoadingOverlay() {
  const { loading, progress } = useData()
  if (!loading) return null
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background/90 backdrop-blur-sm">
      <div className="text-center space-y-4">
        <div className="h-12 w-12 rounded-xl bg-primary flex items-center justify-center text-primary-foreground font-bold text-lg mx-auto">CLV</div>
        <div>
          <p className="text-foreground font-semibold">Loading 50,000 policies…</p>
          <p className="text-muted-foreground text-sm mt-1">{progress}% complete</p>
        </div>
        <div className="w-56 h-2 bg-muted rounded-full overflow-hidden mx-auto">
          <div className="h-full bg-primary rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
        </div>
      </div>
    </div>
  )
}

function App() {
  const [active, setActive] = useState("overview")
  const pages = { overview: Overview, data: DataTablePage, eda: EDA, clv: CLVPage }
  const Page = pages[active] || Overview

  return (
    <DataProvider>
      <LoadingOverlay />
      <div className="flex h-screen overflow-hidden">
        <Sidebar active={active} setActive={setActive} />
        <main className="flex-1 overflow-y-auto p-8">
          <Page />
        </main>
      </div>
    </DataProvider>
  )
}

export default App
