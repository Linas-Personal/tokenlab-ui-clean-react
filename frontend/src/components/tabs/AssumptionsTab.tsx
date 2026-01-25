import { useFormContext } from 'react-hook-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import type { SimulationConfig } from '@/types/config'

export function AssumptionsTab() {
  const { register, watch } = useFormContext<SimulationConfig>()
  const buckets = watch('buckets') || []
  const cliffShockEnabled = watch('behaviors.cliff_shock.enabled')

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
                  <p className="text-xs text-muted-foreground">
                    Multiplies sell pressure during cliff unlock (e.g., 3.0 = 3x more selling)
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Apply Cliff Shock to Buckets:</Label>
                  <div className="border rounded-md p-3 space-y-2">
                    {buckets.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No buckets defined yet</p>
                    ) : (
                      buckets.map((bucket, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id={`cliff-bucket-${index}`}
                            className="h-4 w-4"
                            value={bucket.bucket}
                            disabled={!cliffShockEnabled}
                            {...register('behaviors.cliff_shock.buckets')}
                          />
                          <Label htmlFor={`cliff-bucket-${index}`} className="font-normal">
                            {bucket.bucket}
                          </Label>
                        </div>
                      ))
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Leave empty to apply to all buckets with cliff periods
                  </p>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="price-trigger">
            <AccordionTrigger>Price Trigger / Stop Loss</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="price-trigger-enabled"
                    className="h-4 w-4"
                    {...register('behaviors.price_trigger.enabled')}
                  />
                  <Label htmlFor="price-trigger-enabled">
                    Enable price-based selling behavior
                  </Label>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="price-source">Price Source</Label>
                  <select
                    id="price-source"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    {...register('behaviors.price_trigger.source')}
                  >
                    <option value="flat">Flat (constant price)</option>
                    <option value="scenario">Scenario (uptrend/downtrend/volatile)</option>
                    <option value="csv">CSV Upload</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="price-scenario">Price Scenario</Label>
                  <select
                    id="price-scenario"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    {...register('behaviors.price_trigger.scenario')}
                  >
                    <option value="">None</option>
                    <option value="uptrend">Uptrend</option>
                    <option value="downtrend">Downtrend</option>
                    <option value="volatile">Volatile</option>
                  </select>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="take-profit">Take Profit Threshold</Label>
                    <Input
                      id="take-profit"
                      type="number"
                      step="0.01"
                      placeholder="e.g., 0.5 = +50%"
                      {...register('behaviors.price_trigger.take_profit', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="stop-loss">Stop Loss Threshold</Label>
                    <Input
                      id="stop-loss"
                      type="number"
                      step="0.01"
                      placeholder="e.g., -0.3 = -30%"
                      {...register('behaviors.price_trigger.stop_loss', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="extra-sell">Extra Sell Add-on</Label>
                    <Input
                      id="extra-sell"
                      type="number"
                      step="0.01"
                      placeholder="e.g., 0.2 = +20%"
                      {...register('behaviors.price_trigger.extra_sell_addon', { valueAsNumber: true })}
                    />
                  </div>
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
