import { useFormContext, useWatch } from 'react-hook-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Slider } from '@/components/ui/slider'
import type { SimulationConfig } from '@/types/config'

export function Tier2Forms() {
  const { register, control, setValue } = useFormContext<SimulationConfig>()

  const bondingCurveParam = useWatch({
    control,
    name: 'tier2.pricing.bonding_curve_param',
    defaultValue: 2.0
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tier 2: Dynamic Market Features</CardTitle>
        <CardDescription>
          Configure advanced market dynamics including staking, pricing, treasury, and volume
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" className="w-full">
          <AccordionItem value="staking">
            <AccordionTrigger>Dynamic Staking</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="staking-enabled"
                    className="h-4 w-4"
                    {...register('tier2.staking.enabled')}
                  />
                  <Label htmlFor="staking-enabled">
                    Enable dynamic staking pool
                  </Label>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="staking-apy">APY</Label>
                    <Input
                      id="staking-apy"
                      type="number"
                      step="0.01"
                      {...register('tier2.staking.apy', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="staking-capacity">Max Capacity %</Label>
                    <Input
                      id="staking-capacity"
                      type="number"
                      step="0.01"
                      {...register('tier2.staking.max_capacity_pct', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="staking-lockup">Lockup Period (months)</Label>
                    <Input
                      id="staking-lockup"
                      type="number"
                      {...register('tier2.staking.lockup_months', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="staking-participation">Participation Rate</Label>
                    <Input
                      id="staking-participation"
                      type="number"
                      step="0.01"
                      {...register('tier2.staking.participation_rate', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="staking-source">Reward Source</Label>
                    <select
                      id="staking-source"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...register('tier2.staking.reward_source')}
                    >
                      <option value="treasury">Treasury</option>
                      <option value="emission">Token Emission</option>
                    </select>
                  </div>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="pricing">
            <AccordionTrigger>Dynamic Pricing</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="pricing-enabled"
                    className="h-4 w-4"
                    {...register('tier2.pricing.enabled')}
                  />
                  <Label htmlFor="pricing-enabled">
                    Enable dynamic pricing model
                  </Label>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="pricing-model">Pricing Model</Label>
                    <select
                      id="pricing-model"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...register('tier2.pricing.pricing_model')}
                    >
                      <option value="bonding_curve">Bonding Curve</option>
                      <option value="linear">Linear</option>
                      <option value="constant">Constant</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="pricing-initial">Initial Price</Label>
                    <Input
                      id="pricing-initial"
                      type="number"
                      step="0.01"
                      {...register('tier2.pricing.initial_price', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="pricing-target">Target Price (optional)</Label>
                    <Input
                      id="pricing-target"
                      type="number"
                      step="0.01"
                      placeholder="Leave blank for dynamic"
                      {...register('tier2.pricing.target_price', { valueAsNumber: true })}
                    />
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="pricing-elasticity">Price Elasticity (Bonding Curve)</Label>
                    <span className="text-sm font-medium text-primary">{bondingCurveParam?.toFixed(1) || '2.0'}</span>
                  </div>
                  <Slider
                    id="pricing-elasticity"
                    min={0.1}
                    max={5.0}
                    step={0.1}
                    value={[bondingCurveParam || 2.0]}
                    onValueChange={(value) => setValue('tier2.pricing.bonding_curve_param', value[0])}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>0.1 (Low elasticity)</span>
                    <span>5.0 (High elasticity)</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Higher elasticity = larger price swings with supply changes. Formula: P = P₀ × (S_max / S_circ)^elasticity
                  </p>
                </div>
              </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="treasury">
            <AccordionTrigger>Treasury Strategy</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="treasury-enabled"
                    className="h-4 w-4"
                    {...register('tier2.treasury.enabled')}
                  />
                  <Label htmlFor="treasury-enabled">
                    Enable treasury management
                  </Label>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="treasury-initial">Initial Balance %</Label>
                    <Input
                      id="treasury-initial"
                      type="number"
                      step="0.01"
                      {...register('tier2.treasury.initial_balance_pct', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="treasury-hold">Hold %</Label>
                    <Input
                      id="treasury-hold"
                      type="number"
                      step="0.01"
                      {...register('tier2.treasury.hold_pct', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="treasury-liquidity">Liquidity %</Label>
                    <Input
                      id="treasury-liquidity"
                      type="number"
                      step="0.01"
                      {...register('tier2.treasury.liquidity_pct', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="treasury-buyback">Buyback %</Label>
                    <Input
                      id="treasury-buyback"
                      type="number"
                      step="0.01"
                      {...register('tier2.treasury.buyback_pct', { valueAsNumber: true })}
                    />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Note: Hold % + Liquidity % + Buyback % must equal 100%
                </p>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="volume">
            <AccordionTrigger>Dynamic Volume</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="volume-enabled"
                    className="h-4 w-4"
                    {...register('tier2.volume.enabled')}
                  />
                  <Label htmlFor="volume-enabled">
                    Enable dynamic volume calculation
                  </Label>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="volume-model">Volume Model</Label>
                    <select
                      id="volume-model"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...register('tier2.volume.volume_model')}
                    >
                      <option value="proportional">Proportional to Circulating Supply</option>
                      <option value="constant">Constant</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="volume-base">Base Daily Volume</Label>
                    <Input
                      id="volume-base"
                      type="number"
                      {...register('tier2.volume.base_daily_volume', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="volume-multiplier">Volume Multiplier</Label>
                    <Input
                      id="volume-multiplier"
                      type="number"
                      step="0.1"
                      {...register('tier2.volume.volume_multiplier', { valueAsNumber: true })}
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
