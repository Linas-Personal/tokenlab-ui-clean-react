import { useFormContext } from 'react-hook-form'
import { Rocket } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tier2Forms } from '@/components/forms/Tier2Forms'
import { Tier3Forms } from '@/components/forms/Tier3Forms'
import type { SimulationConfig } from '@/types/config'

export function AdvancedTab() {
  const { watch } = useFormContext<SimulationConfig>()
  const simulationMode = watch('token.simulation_mode')

  if (simulationMode === 'tier1') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Advanced Features</CardTitle>
          <CardDescription>
            Available in Tier 2 and Tier 3 modes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Rocket className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Switch to Tier 2 or Tier 3 in Token Setup to access advanced features like
              dynamic staking, pricing models, treasury strategies, and Monte Carlo simulation.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Tier2Forms />
      {simulationMode === 'tier3' && <Tier3Forms />}
    </div>
  )
}
