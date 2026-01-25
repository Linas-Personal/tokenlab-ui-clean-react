import { useFormContext } from 'react-hook-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import type { SimulationConfig } from '@/types/config'

export function Tier3Forms() {
  const { register, watch } = useFormContext<SimulationConfig>()
  const buckets = watch('buckets') || []
  const cohortEnabled = watch('tier3.cohort_behavior.enabled')

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tier 3: Monte Carlo & Cohort Modeling</CardTitle>
        <CardDescription>
          Configure stochastic simulation and cohort-based behavior modeling
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" className="w-full">
          <AccordionItem value="monte-carlo">
            <AccordionTrigger>Monte Carlo Simulation</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="mc-enabled"
                    className="h-4 w-4"
                    {...register('tier3.monte_carlo.enabled')}
                  />
                  <Label htmlFor="mc-enabled">
                    Enable Monte Carlo simulation with multiple trials
                  </Label>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="mc-trials">Number of Trials</Label>
                    <Input
                      id="mc-trials"
                      type="number"
                      {...register('tier3.monte_carlo.num_trials', { valueAsNumber: true })}
                    />
                    <p className="text-xs text-muted-foreground">
                      Higher values increase accuracy but take longer (10-1000)
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="mc-variance">Variance Level</Label>
                    <select
                      id="mc-variance"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...register('tier3.monte_carlo.variance_level')}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="mc-seed">Random Seed (optional)</Label>
                    <Input
                      id="mc-seed"
                      type="number"
                      placeholder="Leave blank for random"
                      {...register('tier3.monte_carlo.seed', { valueAsNumber: true })}
                    />
                    <p className="text-xs text-muted-foreground">
                      Set a seed for reproducible results
                    </p>
                  </div>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="cohort">
            <AccordionTrigger>Cohort Behavior Modeling</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="cohort-enabled"
                    className="h-4 w-4"
                    {...register('tier3.cohort_behavior.enabled')}
                  />
                  <Label htmlFor="cohort-enabled">
                    Enable cohort-based behavior modeling
                  </Label>
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                  Assign each bucket to a cohort profile to model different investor behaviors.
                </p>

                <div className="space-y-3">
                  <Label>Bucket to Cohort Mapping</Label>
                  <div className="border rounded-md divide-y">
                    {buckets.map((bucket, index) => (
                      <div key={index} className="p-3 flex items-center justify-between gap-4">
                        <div className="font-medium text-sm min-w-[120px]">{bucket.bucket}</div>
                        <select
                          className="flex h-9 w-full max-w-[200px] rounded-md border border-input bg-background px-3 py-1 text-sm disabled:opacity-50"
                          {...register(`tier3.cohort_behavior.bucket_cohort_mapping.${bucket.bucket}`)}
                          disabled={!cohortEnabled}
                        >
                          <option value="">Default (balanced)</option>
                          <option value="high_stake">High Stake (70% stake, 10% sell)</option>
                          <option value="high_sell">High Sell (60% sell, 5% stake)</option>
                          <option value="balanced">Balanced (30% stake, 25% sell)</option>
                        </select>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mt-4 p-4 bg-muted/50 rounded-md">
                  <p className="text-sm font-semibold mb-2">Cohort Profiles:</p>
                  <ul className="text-xs space-y-1 text-muted-foreground">
                    <li><strong>High Stake:</strong> 70% staking probability, 10% sell pressure mean</li>
                    <li><strong>High Sell:</strong> 5% staking probability, 60% sell pressure mean</li>
                    <li><strong>Balanced:</strong> 30% staking probability, 25% sell pressure mean</li>
                  </ul>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  )
}
