import { useState, useRef } from 'react'
import { useForm, FormProvider } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import { Coins, Calendar, Settings, Rocket, BarChart3, Loader2, Upload, Sparkles } from 'lucide-react'
import { submitABMSimulation } from '@/lib/abm-api'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { DEFAULT_CONFIG } from '@/lib/constants'
import { api } from '@/lib/api'
import type { SimulationConfig } from '@/types/config'
import { TokenSetupTab } from '@/components/tabs/TokenSetupTab'
import { VestingScheduleTab } from '@/components/tabs/VestingScheduleTab'
import { AssumptionsTab } from '@/components/tabs/AssumptionsTab'
import { AdvancedTab } from '@/components/tabs/AdvancedTab'
import { ResultsTab } from '@/components/tabs/ResultsTab'
import { ABMTab } from '@/components/tabs/ABMTab'
import { ABMResultsTab } from '@/components/tabs/ABMResultsTab'

function App() {
  const [activeTab, setActiveTab] = useState('token-setup')
  const [isABMSimulating, setIsABMSimulating] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const methods = useForm<SimulationConfig>({
    defaultValues: DEFAULT_CONFIG
  })

  const simulation = useMutation({
    mutationFn: (config: SimulationConfig) => api.runSimulation(config),
    onSuccess: () => {
      setActiveTab('results')
    }
  })

  const abmSimulation = useMutation({
    mutationFn: async (config: any) => {
      setIsABMSimulating(true)
      const result = await submitABMSimulation(config)
      setActiveTab('abm-results')
      return result
    },
    onSuccess: () => {
      setIsABMSimulating(false)
    },
    onError: () => {
      setIsABMSimulating(false)
    }
  })

  const onSubmit = (data: SimulationConfig) => {
    simulation.mutate(data)
  }

  const onABMSubmit = (data: any) => {
    const abmConfig = {
      token: {
        name: data.token.name,
        total_supply: data.token.total_supply,
        start_date: data.token.start_date,
        horizon_months: data.token.horizon_months
      },
      buckets: data.buckets.map((b: any) => ({
        bucket: b.bucket,
        allocation: b.allocation,
        tge_unlock_pct: b.tge_unlock_pct,
        cliff_months: b.cliff_months,
        vesting_months: b.vesting_months
      })),
      abm: data.abm,
      monte_carlo: data.monte_carlo?.enabled ? data.monte_carlo : undefined
    }
    abmSimulation.mutate(abmConfig)
  }

  const handleRunSimulation = () => {
    methods.handleSubmit(onSubmit)()
  }

  const handleRunABMSimulation = () => {
    methods.handleSubmit(onABMSubmit)()
  }

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
            <TabsList className="grid w-full grid-cols-7 mb-8">
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
              <TabsTrigger value="advanced" className="flex items-center gap-2">
                <Rocket className="h-4 w-4" />
                <span className="hidden sm:inline">Advanced</span>
              </TabsTrigger>
              <TabsTrigger value="abm" className="flex items-center gap-2">
                <Rocket className="h-4 w-4" />
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

            <TabsContent value="advanced">
              <AdvancedTab />
            </TabsContent>

            <TabsContent value="abm">
              <ABMTab />
            </TabsContent>

            <TabsContent value="results">
              <ResultsTab
                simulation={simulation.data}
                isLoading={simulation.isPending}
                onRunSimulation={handleRunSimulation}
              />
            </TabsContent>

            <TabsContent value="abm-results">
              <ABMResultsTab onRunSimulation={() => setActiveTab('abm')} />
            </TabsContent>
          </Tabs>
        </FormProvider>

        <div className="mt-8 flex justify-end gap-4">
          <Button
            size="lg"
            variant="outline"
            onClick={handleRunSimulation}
            disabled={simulation.isPending || isABMSimulating}
          >
            {simulation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running Simulation...
              </>
            ) : (
              <>
                <BarChart3 className="mr-2 h-4 w-4" />
                Run Standard Simulation
              </>
            )}
          </Button>
          <Button
            size="lg"
            onClick={handleRunABMSimulation}
            disabled={simulation.isPending || isABMSimulating}
          >
            {isABMSimulating ? (
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
