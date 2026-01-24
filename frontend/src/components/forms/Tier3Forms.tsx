import { useFormContext } from 'react-hook-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import type { SimulationConfig } from '@/types/config'

export function Tier3Forms() {
  const { register } = useFormContext<SimulationConfig>()

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
                <p className="text-sm text-muted-foreground">
                  Cohort behavior profiles are predefined (high_stake, high_sell, balanced).
                  Map buckets to cohorts to customize behavior patterns.
                </p>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  )
}
