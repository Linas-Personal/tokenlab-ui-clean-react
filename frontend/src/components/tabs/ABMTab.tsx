import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Info, Sparkles } from 'lucide-react'
import { ABMConfigForm } from '@/components/forms/ABMConfigForm'

export function ABMTab() {
  return (
    <div className="space-y-6">
      <Card className="border-2 border-primary/20 bg-gradient-to-br from-blue-50/50 to-indigo-50/50 dark:from-blue-950/20 dark:to-indigo-950/20">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Sparkles className="h-6 w-6 text-primary" />
            </div>
            <div>
              <CardTitle>Agent-Based Modeling (ABM)</CardTitle>
              <CardDescription>
                Simulate realistic market dynamics with individual token holder agents
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-semibold">What is Agent-Based Modeling?</p>
                  <p className="text-sm">
                    ABM creates individual token holder agents (Team members, VCs, Community members)
                    with unique characteristics like risk tolerance, price sensitivity, and staking propensity.
                    Each agent makes autonomous decisions about selling, staking, or holding tokens based on:
                  </p>
                  <ul className="text-sm list-disc list-inside ml-2 space-y-1">
                    <li>Their vesting schedule and unlock events</li>
                    <li>Current market price and price history</li>
                    <li>Individual behavioral parameters</li>
                    <li>Cliff shock effects (increased selling after cliff)</li>
                    <li>Take-profit and stop-loss triggers</li>
                  </ul>
                  <p className="text-sm mt-2">
                    <span className="font-semibold">Key Innovation:</span> Agent actions create feedback loops -
                    selling affects price, which affects future agent decisions. This creates emergent market
                    dynamics that simple models cannot capture.
                  </p>
                </div>
              </AlertDescription>
            </Alert>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="p-4 rounded-lg border bg-card">
                <div className="font-semibold mb-2">🎯 Heterogeneous Agents</div>
                <p className="text-muted-foreground">
                  Each agent has unique risk tolerance, price sensitivity, and staking propensity
                  sampled from statistical distributions.
                </p>
              </div>
              <div className="p-4 rounded-lg border bg-card">
                <div className="font-semibold mb-2">🔄 Feedback Loops</div>
                <p className="text-muted-foreground">
                  Agent selling → price drops → affects future agent decisions.
                  Creates realistic boom-bust cycles.
                </p>
              </div>
              <div className="p-4 rounded-lg border bg-card">
                <div className="font-semibold mb-2">📊 Emergent Behavior</div>
                <p className="text-muted-foreground">
                  Market dynamics emerge from individual agent interactions.
                  No need to manually specify sell pressure curves.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-lg border bg-muted/50">
              <p className="text-sm font-semibold mb-2">Performance & Scalability:</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm text-muted-foreground">
                <div>
                  <span className="font-semibold">Full Individual:</span> 1:1 agent per holder (best for &lt; 1K holders)
                </div>
                <div>
                  <span className="font-semibold">Representative Sampling:</span> ~1,000 agents (1K-10K holders)
                </div>
                <div>
                  <span className="font-semibold">Meta-Agents:</span> 50 agents per cohort (&gt; 10K holders)
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                The "Adaptive" setting automatically selects the best strategy based on estimated holder count.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <ABMConfigForm />

      <Card>
        <CardHeader>
          <CardTitle>Next Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-primary">1</span>
              </div>
              <div>
                <p className="font-semibold">Configure Token & Vesting</p>
                <p className="text-muted-foreground">
                  Set up your token basics and vesting schedules in the previous tabs
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-primary">2</span>
              </div>
              <div>
                <p className="font-semibold">Configure ABM Settings</p>
                <p className="text-muted-foreground">
                  Choose pricing model, enable staking/treasury, configure Monte Carlo if desired
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-primary">3</span>
              </div>
              <div>
                <p className="font-semibold">Run Simulation</p>
                <p className="text-muted-foreground">
                  Click "Run ABM Simulation" to start. Progress is shown in real-time via SSE streaming.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-primary">4</span>
              </div>
              <div>
                <p className="font-semibold">Analyze Results</p>
                <p className="text-muted-foreground">
                  View market dynamics, cohort behavior, staking/treasury metrics in the ABM Results tab
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
