import { useFormContext } from 'react-hook-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import type { SimulationConfig } from '@/types/config'

export function AssumptionsTab() {
  const { register } = useFormContext<SimulationConfig>()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market Assumptions & Behaviors</CardTitle>
        <CardDescription>
          Configure base assumptions and behavioral modifiers
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="sell-pressure">Base Sell Pressure Level</Label>
            <select
              id="sell-pressure"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              {...register('assumptions.sell_pressure_level')}
            >
              <option value="low">Low (10%)</option>
              <option value="medium">Medium (25%)</option>
              <option value="high">High (50%)</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="daily-volume">Average Daily Volume (tokens)</Label>
            <Input
              id="daily-volume"
              type="number"
              placeholder="Optional"
              {...register('assumptions.avg_daily_volume_tokens', { valueAsNumber: true })}
            />
          </div>
        </div>

        <Accordion type="multiple" className="w-full">
          <AccordionItem value="cliff-shock">
            <AccordionTrigger>Cliff Shock Behavior</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="cliff-shock-enabled"
                    className="h-4 w-4"
                    {...register('behaviors.cliff_shock.enabled')}
                  />
                  <Label htmlFor="cliff-shock-enabled">
                    Enable increased selling at cliff unlock
                  </Label>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cliff-multiplier">Sell Pressure Multiplier</Label>
                  <Input
                    id="cliff-multiplier"
                    type="number"
                    step="0.1"
                    {...register('behaviors.cliff_shock.multiplier', { valueAsNumber: true })}
                  />
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="relock">
            <AccordionTrigger>Relock / Staking Delay</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="relock-enabled"
                    className="h-4 w-4"
                    {...register('behaviors.relock.enabled')}
                  />
                  <Label htmlFor="relock-enabled">
                    Enable token relocking after unlock
                  </Label>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="relock-pct">Relock Percentage</Label>
                    <Input
                      id="relock-pct"
                      type="number"
                      step="0.01"
                      {...register('behaviors.relock.relock_pct', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lock-duration">Lock Duration (months)</Label>
                    <Input
                      id="lock-duration"
                      type="number"
                      {...register('behaviors.relock.lock_duration_months', { valueAsNumber: true })}
                    />
                  </div>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  )
}
