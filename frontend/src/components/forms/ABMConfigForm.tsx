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
  buckets?: Array<{
    bucket: string
    allocation: number
    tge_unlock_pct: number
    cliff_months: number
    vesting_months: number
  }>
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
    enable_volume: boolean
    volume_config: {
      volume_model: 'proportional' | 'constant'
      base_daily_volume: number
      volume_multiplier: number
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
    bucket_cohort_mapping: Record<string, string>
    initial_price: number
    seed: number | null
    store_cohort_details: boolean
  }
  monte_carlo: {
    enabled: boolean
    num_trials: number
    variance_level: 'low' | 'medium' | 'high'
    seed: number | null
    confidence_levels: number[]
  }
}

export function ABMConfigForm() {
  const { register, setValue, watch, getValues } = useFormContext<ABMConfigFormData>()

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

  const enableVolume = useWatch({
    name: 'abm.enable_volume',
    defaultValue: false
  })

  const volumeModel = useWatch({
    name: 'abm.volume_config.volume_model',
    defaultValue: 'proportional'
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

  // Watch buckets for cohort mapping
  const buckets = useWatch({
    name: 'buckets' as any,
    defaultValue: []
  })

  const bucketCohortMapping = useWatch({
    name: 'abm.bucket_cohort_mapping',
    defaultValue: {}
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
                      <option value="adaptive">Adaptive - Auto-selects based on holder count (Recommended)</option>
                      <option value="full_individual">Full Individual - One agent per holder (most accurate, slowest)</option>
                      <option value="meta_agents">Meta Agents - Representative sampling (fastest, good approximation)</option>
                    </select>
                    <p className="text-xs text-muted-foreground">
                      {agentGranularity === 'adaptive' && 'Automatically chooses full individual (<1K holders), representative sampling (1K-10K), or meta-agents (>10K) for optimal performance'}
                      {agentGranularity === 'full_individual' && 'Creates one agent per token holder. Most accurate but slower for large holder counts. Best for <1,000 holders.'}
                      {agentGranularity === 'meta_agents' && 'Each agent represents multiple holders with weighted actions. Fastest option, recommended for >10,000 holders.'}
                    </p>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="agents-per-cohort">Agents Per Cohort</Label>
                      <span className="text-sm font-semibold text-primary px-2 py-1 bg-primary/10 rounded">
                        {agentsPerCohort}
                      </span>
                    </div>
                    <div className="px-2">
                      <Slider
                        id="agents-per-cohort"
                        min={10}
                        max={500}
                        step={10}
                        value={[agentsPerCohort]}
                        onValueChange={(value) => setValue('abm.agents_per_cohort', value[0])}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>10</span>
                        <span>500</span>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Number of agents to create per cohort (Team, VC, Community, etc.). More agents = better accuracy but slower simulation.
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

            <AccordionItem value="volume">
              <AccordionTrigger>Dynamic Volume (Optional)</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="enable-volume"
                      className="h-4 w-4"
                      {...register('abm.enable_volume')}
                    />
                    <Label htmlFor="enable-volume">
                      Enable dynamic transaction volume calculation
                    </Label>
                  </div>

                  {enableVolume && (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="volume-model">Volume Model</Label>
                          <select
                            id="volume-model"
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            {...register('abm.volume_config.volume_model')}
                          >
                            <option value="proportional">Proportional (scales with supply)</option>
                            <option value="constant">Constant (fixed)</option>
                          </select>
                          <p className="text-xs text-muted-foreground">
                            {volumeModel === 'proportional' && 'Volume scales with circulating supply ratio'}
                            {volumeModel === 'constant' && 'Fixed daily trading volume'}
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="base-daily-volume">Base Daily Volume (tokens)</Label>
                          <Input
                            id="base-daily-volume"
                            type="number"
                            step="1000000"
                            {...register('abm.volume_config.base_daily_volume', { valueAsNumber: true })}
                          />
                          <p className="text-xs text-muted-foreground">
                            Base transaction volume in tokens
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="volume-multiplier">Volume Multiplier</Label>
                          <Input
                            id="volume-multiplier"
                            type="number"
                            step="0.1"
                            min="0.1"
                            max="100"
                            {...register('abm.volume_config.volume_multiplier', { valueAsNumber: true })}
                          />
                          <p className="text-xs text-muted-foreground">
                            Adjustment factor (1.0 = baseline)
                          </p>
                        </div>
                      </div>

                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription className="text-xs">
                          {pricingModel === 'eoe' ? (
                            <>Dynamic volume affects EOE pricing calculations. Proportional model scales volume with circulating supply growth.</>
                          ) : (
                            <>Dynamic volume is most relevant for EOE pricing model. Currently using {pricingModel}.</>
                          )}
                        </AlertDescription>
                      </Alert>
                    </>
                  )}
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
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <Label htmlFor="num-trials">Number of Trials</Label>
                            <span className="text-sm font-semibold text-primary px-2 py-1 bg-primary/10 rounded">
                              {numTrials}
                            </span>
                          </div>
                          <div className="px-2">
                            <Slider
                              id="num-trials"
                              min={10}
                              max={500}
                              step={10}
                              value={[numTrials]}
                              onValueChange={(value) => setValue('monte_carlo.num_trials', value[0])}
                              className="w-full"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground mt-1">
                              <span>10</span>
                              <span>500</span>
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            More trials = better confidence bands but longer execution time
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="variance-level">Variance Level</Label>
                          <select
                            id="variance-level"
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            {...register('monte_carlo.variance_level')}
                          >
                            <option value="low">Low (tight distributions)</option>
                            <option value="medium">Medium (balanced)</option>
                            <option value="high">High (wide distributions)</option>
                          </select>
                          <p className="text-xs text-muted-foreground">
                            Controls variability in agent behavior sampling
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

            <AccordionItem value="cohort-behavior">
              <AccordionTrigger>Cohort Behavior Presets (Optional)</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription className="text-xs">
                      Assign simplified behavioral profiles to your allocation buckets. Each preset defines
                      agent characteristics like sell pressure, staking propensity, and risk tolerance.
                      Leave unassigned to use default profiles based on bucket names.
                    </AlertDescription>
                  </Alert>

                  <div className="space-y-3">
                    <div className="text-sm font-medium">Preset Profiles:</div>
                    <div className="grid grid-cols-3 gap-3 text-xs">
                      <div className="p-3 border rounded-md bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
                        <div className="font-semibold text-green-900 dark:text-green-100">Conservative</div>
                        <div className="text-green-700 dark:text-green-300 mt-1">
                          • Low sell pressure (10%)<br/>
                          • High staking (60%)<br/>
                          • Long hold time (12-24mo)
                        </div>
                      </div>
                      <div className="p-3 border rounded-md bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
                        <div className="font-semibold text-blue-900 dark:text-blue-100">Moderate</div>
                        <div className="text-blue-700 dark:text-blue-300 mt-1">
                          • Medium sell pressure (25%)<br/>
                          • Medium staking (40%)<br/>
                          • Medium hold time (6-12mo)
                        </div>
                      </div>
                      <div className="p-3 border rounded-md bg-orange-50 dark:bg-orange-950 border-orange-200 dark:border-orange-800">
                        <div className="font-semibold text-orange-900 dark:text-orange-100">Aggressive</div>
                        <div className="text-orange-700 dark:text-orange-300 mt-1">
                          • High sell pressure (40%)<br/>
                          • Low staking (30%)<br/>
                          • Short hold time (4-8mo)
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label className="text-sm">Bucket Assignments</Label>
                    <p className="text-xs text-muted-foreground mb-3">
                      Assign behavioral presets to your allocation buckets. These mappings override default bucket profiles.
                    </p>

                    {buckets && buckets.length > 0 ? (
                      <div className="space-y-3 border rounded-md p-4 bg-muted/50">
                        {buckets.map((bucket: any, index: number) => (
                          <div key={index} className="flex items-center gap-3">
                            <div className="flex-1 min-w-0">
                              <Label className="text-sm font-medium truncate block">
                                {bucket.bucket || `Bucket ${index + 1}`}
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                {bucket.allocation}% allocation
                              </p>
                            </div>
                            <div className="flex-1">
                              <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
                                value={bucketCohortMapping?.[bucket.bucket] || ''}
                                onChange={(e) => {
                                  const newMapping = { ...bucketCohortMapping }
                                  if (e.target.value === '') {
                                    delete newMapping[bucket.bucket]
                                  } else {
                                    newMapping[bucket.bucket] = e.target.value
                                  }
                                  setValue('abm.bucket_cohort_mapping', newMapping)
                                }}
                              >
                                <option value="">Default (auto-detect)</option>
                                <option value="conservative">Conservative</option>
                                <option value="moderate">Moderate</option>
                                <option value="aggressive">Aggressive</option>
                              </select>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <Alert className="bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800">
                        <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                        <AlertDescription className="text-xs text-amber-800 dark:text-amber-200">
                          No allocation buckets configured yet. Please add buckets in the Vesting Schedule tab to assign behavioral presets.
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
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
              <span className="text-muted-foreground">Dynamic Volume:</span>
              <span className="font-semibold">{enableVolume ? `${volumeModel}` : 'Disabled'}</span>
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
