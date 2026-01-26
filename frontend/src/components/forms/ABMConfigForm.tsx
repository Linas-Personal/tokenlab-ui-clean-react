import { useFormContext, useWatch } from 'react-hook-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Slider } from '@/components/ui/slider'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Info, AlertTriangle } from 'lucide-react'
import type { AgentGranularity, PricingModelEnum, RewardSource } from '@/types/abm'

interface ABMConfigFormData {
  abm: {
    agent_granularity: AgentGranularity
    agents_per_cohort: number
    pricing_model: PricingModelEnum
    pricing_config: {
      holding_time?: number
      smoothing_factor?: number
      min_price?: number
      k?: number
      n?: number
      initial_price?: number
      alpha?: number
    }
    enable_staking: boolean
    staking_config: {
      base_apy: number
      max_capacity_pct: number
      lockup_months: number
      reward_source: RewardSource
      apy_multiplier_at_empty: number
      apy_multiplier_at_full: number
    }
    enable_treasury: boolean
    treasury_config: {
      initial_balance_pct: number
      transaction_fee_pct: number
      hold_pct: number
      liquidity_pct: number
      buyback_pct: number
      burn_bought_tokens: boolean
    }
    initial_price: number
    seed: number | null
    store_cohort_details: boolean
  }
  monte_carlo: {
    enabled: boolean
    num_trials: number
    seed: number | null
    confidence_levels: number[]
  }
}

export function ABMConfigForm() {
  const { register, setValue, watch } = useFormContext<ABMConfigFormData>()

  const agentGranularity = useWatch({
    name: 'abm.agent_granularity',
    defaultValue: 'adaptive'
  })

  const pricingModel = useWatch({
    name: 'abm.pricing_model',
    defaultValue: 'eoe'
  })

  const enableStaking = useWatch({
    name: 'abm.enable_staking',
    defaultValue: false
  })

  const enableTreasury = useWatch({
    name: 'abm.enable_treasury',
    defaultValue: false
  })

  const monteCarloEnabled = useWatch({
    name: 'monte_carlo.enabled',
    defaultValue: false
  })

  const agentsPerCohort = useWatch({
    name: 'abm.agents_per_cohort',
    defaultValue: 50
  })

  const numTrials = useWatch({
    name: 'monte_carlo.num_trials',
    defaultValue: 100
  })

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Agent-Based Model Configuration</CardTitle>
          <CardDescription>
            Configure individual token holder agents with heterogeneous behaviors for realistic market dynamics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Accordion type="multiple" className="w-full" defaultValue={['agents', 'pricing']}>
            <AccordionItem value="agents">
              <AccordionTrigger>Agent Population</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="agent-granularity">Agent Granularity</Label>
                    <select
                      id="agent-granularity"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...register('abm.agent_granularity')}
                    >
                      <option value="adaptive">Adaptive (Recommended)</option>
                      <option value="full_individual">Full Individual (&lt; 1K holders)</option>
                      <option value="meta_agents">Meta Agents (&gt; 10K holders)</option>
                    </select>
                    <p className="text-xs text-muted-foreground">
                      {agentGranularity === 'adaptive' && 'Automatically selects strategy based on holder count'}
                      {agentGranularity === 'full_individual' && 'Creates one agent per holder (slower, most accurate)'}
                      {agentGranularity === 'meta_agents' && 'Each agent represents many holders (fastest)'}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="agents-per-cohort">
                      Agents Per Cohort: <span className="font-semibold">{agentsPerCohort}</span>
                    </Label>
                    <Slider
                      id="agents-per-cohort"
                      min={10}
                      max={500}
                      step={10}
                      value={[agentsPerCohort]}
                      onValueChange={(value) => setValue('abm.agents_per_cohort', value[0])}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground">
                      Number of agents to create per cohort (Team, VC, Community, etc.)
                    </p>
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="store-cohort-details"
                      className="h-4 w-4"
                      {...register('abm.store_cohort_details')}
                    />
                    <Label htmlFor="store-cohort-details">
                      Store cohort-level details
                    </Label>
                  </div>

                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription className="text-xs">
                      ABM creates individual agents with unique risk tolerance, price sensitivity, and staking propensity.
                      Agents make autonomous decisions based on price movements and vesting schedules.
                    </AlertDescription>
                  </Alert>
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="pricing">
              <AccordionTrigger>Dynamic Pricing Model</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="pricing-model">Pricing Model</Label>
                    <select
                      id="pricing-model"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...register('abm.pricing_model')}
                    >
                      <option value="eoe">Equation of Exchange (EOE)</option>
                      <option value="bonding_curve">Bonding Curve</option>
                      <option value="issuance_curve">Issuance Curve</option>
                      <option value="constant">Constant Price</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="initial-price">Initial Price ($)</Label>
                      <Input
                        id="initial-price"
                        type="number"
                        step="0.01"
                        {...register('abm.initial_price', { valueAsNumber: true })}
                      />
                    </div>

                    {pricingModel === 'eoe' && (
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="holding-time">Holding Time (months)</Label>
                          <Input
                            id="holding-time"
                            type="number"
                            step="0.1"
                            {...register('abm.pricing_config.holding_time', { valueAsNumber: true })}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="smoothing-factor">Smoothing Factor</Label>
                          <Input
                            id="smoothing-factor"
                            type="number"
                            step="0.01"
                            min="0"
                            max="1"
                            {...register('abm.pricing_config.smoothing_factor', { valueAsNumber: true })}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="min-price">Min Price ($)</Label>
                          <Input
                            id="min-price"
                            type="number"
                            step="0.001"
                            {...register('abm.pricing_config.min_price', { valueAsNumber: true })}
                          />
                        </div>
                      </>
                    )}

                    {pricingModel === 'bonding_curve' && (
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="k-param">K Parameter</Label>
                          <Input
                            id="k-param"
                            type="number"
                            step="0.000001"
                            {...register('abm.pricing_config.k', { valueAsNumber: true })}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="n-param">N Parameter (exponent)</Label>
                          <Input
                            id="n-param"
                            type="number"
                            step="0.1"
                            {...register('abm.pricing_config.n', { valueAsNumber: true })}
                          />
                        </div>
                      </>
                    )}

                    {pricingModel === 'issuance_curve' && (
                      <div className="space-y-2">
                        <Label htmlFor="alpha-param">Alpha Parameter</Label>
                        <Input
                          id="alpha-param"
                          type="number"
                          step="0.1"
                          {...register('abm.pricing_config.alpha', { valueAsNumber: true })}
                        />
                      </div>
                    )}
                  </div>

                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription className="text-xs">
                      {pricingModel === 'eoe' && 'P = Demand / (Supply × Velocity). Price reacts to agent selling behavior.'}
                      {pricingModel === 'bonding_curve' && 'P = k × Supply^n. Quadratic pricing common (n=2).'}
                      {pricingModel === 'issuance_curve' && 'P = P0 × (1 + S/S_max)^α. Scarcity premium.'}
                      {pricingModel === 'constant' && 'Fixed price baseline for testing.'}
                    </AlertDescription>
                  </Alert>
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="staking">
              <AccordionTrigger>Staking Pool (Optional)</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="enable-staking"
                      className="h-4 w-4"
                      {...register('abm.enable_staking')}
                    />
                    <Label htmlFor="enable-staking">
                      Enable dynamic staking pool with variable APY
                    </Label>
                  </div>

                  {enableStaking && (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="base-apy">Base APY</Label>
                          <Input
                            id="base-apy"
                            type="number"
                            step="0.01"
                            {...register('abm.staking_config.base_apy', { valueAsNumber: true })}
                          />
                          <p className="text-xs text-muted-foreground">
                            APY at 50% pool utilization (e.g., 0.15 = 15%)
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="max-capacity">Max Capacity (%)</Label>
                          <Input
                            id="max-capacity"
                            type="number"
                            step="0.01"
                            {...register('abm.staking_config.max_capacity_pct', { valueAsNumber: true })}
                          />
                          <p className="text-xs text-muted-foreground">
                            Max pool size as % of total supply
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="lockup-months">Lockup Period (months)</Label>
                          <Input
                            id="lockup-months"
                            type="number"
                            {...register('abm.staking_config.lockup_months', { valueAsNumber: true })}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="reward-source">Reward Source</Label>
                          <select
                            id="reward-source"
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            {...register('abm.staking_config.reward_source')}
                          >
                            <option value="emission">Token Emission</option>
                            <option value="treasury">Treasury</option>
                          </select>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="apy-empty">APY Multiplier (Empty Pool)</Label>
                          <Input
                            id="apy-empty"
                            type="number"
                            step="0.1"
                            {...register('abm.staking_config.apy_multiplier_at_empty', { valueAsNumber: true })}
                          />
                          <p className="text-xs text-muted-foreground">
                            1.5 = 150% of base APY when pool is empty
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="apy-full">APY Multiplier (Full Pool)</Label>
                          <Input
                            id="apy-full"
                            type="number"
                            step="0.1"
                            {...register('abm.staking_config.apy_multiplier_at_full', { valueAsNumber: true })}
                          />
                          <p className="text-xs text-muted-foreground">
                            0.5 = 50% of base APY when pool is full
                          </p>
                        </div>
                      </div>

                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription className="text-xs">
                          Variable APY incentivizes early staking. When pool is empty, APY is higher. As pool fills, APY decreases.
                          Example: 15% base APY → 22.5% when empty → 7.5% when full.
                        </AlertDescription>
                      </Alert>
                    </>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="treasury">
              <AccordionTrigger>Treasury Management (Optional)</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="enable-treasury"
                      className="h-4 w-4"
                      {...register('abm.enable_treasury')}
                    />
                    <Label htmlFor="enable-treasury">
                      Enable treasury with buyback and burn
                    </Label>
                  </div>

                  {enableTreasury && (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="initial-balance">Initial Balance (%)</Label>
                          <Input
                            id="initial-balance"
                            type="number"
                            step="0.01"
                            {...register('abm.treasury_config.initial_balance_pct', { valueAsNumber: true })}
                          />
                          <p className="text-xs text-muted-foreground">
                            % of total supply allocated to treasury
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="transaction-fee">Transaction Fee (%)</Label>
                          <Input
                            id="transaction-fee"
                            type="number"
                            step="0.001"
                            {...register('abm.treasury_config.transaction_fee_pct', { valueAsNumber: true })}
                          />
                          <p className="text-xs text-muted-foreground">
                            Fee collected on each token sale
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="hold-pct">Hold %</Label>
                          <Input
                            id="hold-pct"
                            type="number"
                            step="0.01"
                            {...register('abm.treasury_config.hold_pct', { valueAsNumber: true })}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="liquidity-pct">Liquidity %</Label>
                          <Input
                            id="liquidity-pct"
                            type="number"
                            step="0.01"
                            {...register('abm.treasury_config.liquidity_pct', { valueAsNumber: true })}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="buyback-pct">Buyback %</Label>
                          <Input
                            id="buyback-pct"
                            type="number"
                            step="0.01"
                            {...register('abm.treasury_config.buyback_pct', { valueAsNumber: true })}
                          />
                        </div>

                        <div className="flex items-center space-x-2 pt-6">
                          <input
                            type="checkbox"
                            id="burn-bought-tokens"
                            className="h-4 w-4"
                            {...register('abm.treasury_config.burn_bought_tokens')}
                          />
                          <Label htmlFor="burn-bought-tokens">
                            Burn bought tokens (deflationary)
                          </Label>
                        </div>
                      </div>

                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription className="text-xs">
                          Treasury collects fees, then allocates: Hold % (reserves), Liquidity % (market depth), Buyback % (burn).
                          Percentages must sum to 1.0. Burning tokens creates deflationary pressure.
                        </AlertDescription>
                      </Alert>
                    </>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="monte-carlo">
              <AccordionTrigger>Monte Carlo Simulations (Optional)</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="enable-monte-carlo"
                      className="h-4 w-4"
                      {...register('monte_carlo.enabled')}
                    />
                    <Label htmlFor="enable-monte-carlo">
                      Enable Monte Carlo probabilistic forecasting
                    </Label>
                  </div>

                  {monteCarloEnabled && (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="num-trials">
                            Number of Trials: <span className="font-semibold">{numTrials}</span>
                          </Label>
                          <Slider
                            id="num-trials"
                            min={10}
                            max={500}
                            step={10}
                            value={[numTrials]}
                            onValueChange={(value) => setValue('monte_carlo.num_trials', value[0])}
                            className="w-full"
                          />
                          <p className="text-xs text-muted-foreground">
                            More trials = better confidence bands but longer execution time
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="mc-seed">Random Seed (optional)</Label>
                          <Input
                            id="mc-seed"
                            type="number"
                            placeholder="Leave empty for random"
                            {...register('monte_carlo.seed', { valueAsNumber: true })}
                          />
                        </div>
                      </div>

                      <Alert>
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription className="text-xs">
                          Monte Carlo runs {numTrials} simulations with different random seeds to generate confidence bands (P10, P50, P90).
                          Expected time: ~{(numTrials * 0.007).toFixed(1)}s. Results show probabilistic price trajectories.
                        </AlertDescription>
                      </Alert>
                    </>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="advanced">
              <AccordionTrigger>Advanced Settings</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="abm-seed">Random Seed (optional)</Label>
                    <Input
                      id="abm-seed"
                      type="number"
                      placeholder="Leave empty for random"
                      {...register('abm.seed', { valueAsNumber: true })}
                    />
                    <p className="text-xs text-muted-foreground">
                      Set a seed for reproducible simulations
                    </p>
                  </div>

                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription className="text-xs">
                      Random seed controls agent attribute sampling. Same seed = identical results.
                      Useful for debugging and comparing different configurations.
                    </AlertDescription>
                  </Alert>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>ABM Features Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Agent Granularity:</span>
              <span className="font-semibold">{agentGranularity}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Agents per Cohort:</span>
              <span className="font-semibold">{agentsPerCohort}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Pricing Model:</span>
              <span className="font-semibold">{pricingModel.toUpperCase()}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Initial Price:</span>
              <span className="font-semibold">${watch('abm.initial_price', 1.0)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Staking Enabled:</span>
              <span className="font-semibold">{enableStaking ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Treasury Enabled:</span>
              <span className="font-semibold">{enableTreasury ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Monte Carlo:</span>
              <span className="font-semibold">{monteCarloEnabled ? `${numTrials} trials` : 'Disabled'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Store Cohort Details:</span>
              <span className="font-semibold">{watch('abm.store_cohort_details', true) ? 'Yes' : 'No'}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
