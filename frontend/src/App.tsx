import { useState, useRef } from 'react'
import { useForm, FormProvider } from 'react-hook-form'
import { Coins, Calendar, Settings, BarChart3, Loader2, Upload, Sparkles } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { DEFAULT_CONFIG } from '@/lib/constants'
import type { SimulationConfig } from '@/types/config'
import type { ABMSimulationRequest } from '@/types/abm'
import { TokenSetupTab } from '@/components/tabs/TokenSetupTab'
import { VestingScheduleTab } from '@/components/tabs/VestingScheduleTab'
import { AssumptionsTab } from '@/components/tabs/AssumptionsTab'
import { ResultsTab } from '@/components/tabs/ResultsTab'
import { ABMTab } from '@/components/tabs/ABMTab'
import { ABMResultsTab } from '@/components/tabs/ABMResultsTab'
import { useABMSimulation } from '@/hooks/useABMSimulation'

function App() {
  const [activeTab, setActiveTab] = useState('token-setup')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const abmSimulation = useABMSimulation()

  const methods = useForm<SimulationConfig>({
    defaultValues: DEFAULT_CONFIG
  })

  const buildABMConfig = (data: SimulationConfig): ABMSimulationRequest => ({
    token: {
      name: data.token.name,
      total_supply: data.token.total_supply,
      start_date: data.token.start_date,
      horizon_months: data.token.horizon_months
    },
    buckets: data.buckets.map((bucket) => ({
      bucket: bucket.bucket,
      allocation: bucket.allocation,
      tge_unlock_pct: bucket.tge_unlock_pct,
      cliff_months: bucket.cliff_months,
      vesting_months: bucket.vesting_months
    })),
    abm: data.abm,
    monte_carlo: data.monte_carlo?.enabled ? data.monte_carlo : undefined
  })

  const handleRunABMSimulation = methods.handleSubmit(async (data) => {
    setActiveTab('abm-results')
    try {
      await abmSimulation.submit(buildABMConfig(data))
    } catch {
      // Error state is handled in the simulation hook and results tab.
    }
  })

  const handleImportConfig = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      const config = JSON.parse(content) as SimulationConfig
      methods.reset(config)
      setActiveTab('token-setup')
    }
    reader.readAsText(file)
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Token Vesting Simulator</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Model token unlock schedules and market dynamics
              </p>
            </div>
            <div className="flex items-center gap-3">
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                className="hidden"
                onChange={handleImportConfig}
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="mr-2 h-4 w-4" />
                Import Config
              </Button>
              <div className="text-sm text-muted-foreground">
                Powered by TokenLab
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        <FormProvider {...methods}>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-6 mb-8">
              <TabsTrigger value="token-setup" className="flex items-center gap-2">
                <Coins className="h-4 w-4" />
                <span className="hidden sm:inline">Token Setup</span>
              </TabsTrigger>
              <TabsTrigger value="vesting" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                <span className="hidden sm:inline">Vesting Schedule</span>
              </TabsTrigger>
              <TabsTrigger value="assumptions" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                <span className="hidden sm:inline">Assumptions</span>
              </TabsTrigger>
              <TabsTrigger value="abm" className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                <span className="hidden sm:inline">ABM Config</span>
              </TabsTrigger>
              <TabsTrigger value="results" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                <span className="hidden sm:inline">Results</span>
              </TabsTrigger>
              <TabsTrigger value="abm-results" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                <span className="hidden sm:inline">ABM Results</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="token-setup">
              <TokenSetupTab />
            </TabsContent>

            <TabsContent value="vesting">
              <VestingScheduleTab />
            </TabsContent>

            <TabsContent value="assumptions">
              <AssumptionsTab />
            </TabsContent>

            <TabsContent value="abm">
              <ABMTab />
            </TabsContent>

            <TabsContent value="results">
              <ResultsTab />
            </TabsContent>

            <TabsContent value="abm-results">
              <ABMResultsTab
                simulation={abmSimulation}
                onRunSimulation={() => setActiveTab('abm')}
              />
            </TabsContent>
          </Tabs>
        </FormProvider>

        <div className="mt-8 flex justify-end">
          <Button
            size="lg"
            onClick={handleRunABMSimulation}
            disabled={abmSimulation.isSubmitting || abmSimulation.isRunning}
          >
            {abmSimulation.isSubmitting || abmSimulation.isRunning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running ABM Simulation...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Run ABM Simulation
              </>
            )}
          </Button>
        </div>
      </main>
    </div>
  )
}

export default App
