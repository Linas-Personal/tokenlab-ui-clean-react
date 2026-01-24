import { useState, useRef } from 'react'
import { useForm, FormProvider } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import { Coins, Calendar, Settings, Rocket, BarChart3, Loader2, Upload } from 'lucide-react'
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

function App() {
  const [activeTab, setActiveTab] = useState('token-setup')
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

  const onSubmit = (data: SimulationConfig) => {
    simulation.mutate(data)
  }

  const handleRunSimulation = () => {
    methods.handleSubmit(onSubmit)()
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
            <TabsList className="grid w-full grid-cols-5 mb-8">
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
              <TabsTrigger value="results" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                <span className="hidden sm:inline">Results</span>
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

            <TabsContent value="results">
              <ResultsTab
                simulation={simulation.data}
                isLoading={simulation.isPending}
                onRunSimulation={handleRunSimulation}
              />
            </TabsContent>
          </Tabs>
        </FormProvider>

        <div className="mt-8 flex justify-end gap-4">
          <Button
            size="lg"
            onClick={handleRunSimulation}
            disabled={simulation.isPending}
          >
            {simulation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running Simulation...
              </>
            ) : (
              <>
                <BarChart3 className="mr-2 h-4 w-4" />
                Run Simulation
              </>
            )}
          </Button>
        </div>
      </main>
    </div>
  )
}

export default App
