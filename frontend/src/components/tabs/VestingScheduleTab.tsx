import { useFormContext } from 'react-hook-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { DEFAULT_CONFIG } from '@/lib/constants'
import type { SimulationConfig } from '@/types/config'

export function VestingScheduleTab() {
  const { register, watch } = useFormContext<SimulationConfig>()
  const buckets = watch('buckets') || DEFAULT_CONFIG.buckets

  return (
    <Card>
      <CardHeader>
        <CardTitle>Vesting Schedule</CardTitle>
        <CardDescription>
          Configure unlock schedules for each bucket
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Bucket</th>
                <th className="text-left p-2">Allocation</th>
                <th className="text-left p-2">TGE %</th>
                <th className="text-left p-2">Cliff (mo)</th>
                <th className="text-left p-2">Vesting (mo)</th>
              </tr>
            </thead>
            <tbody>
              {buckets.map((bucket, index) => (
                <tr key={index} className="border-b">
                  <td className="p-2">
                    <Input {...register(`buckets.${index}.bucket`)} />
                  </td>
                  <td className="p-2">
                    <Input
                      type="number"
                      {...register(`buckets.${index}.allocation`, { valueAsNumber: true })}
                    />
                  </td>
                  <td className="p-2">
                    <Input
                      type="number"
                      {...register(`buckets.${index}.tge_unlock_pct`, { valueAsNumber: true })}
                    />
                  </td>
                  <td className="p-2">
                    <Input
                      type="number"
                      {...register(`buckets.${index}.cliff_months`, { valueAsNumber: true })}
                    />
                  </td>
                  <td className="p-2">
                    <Input
                      type="number"
                      {...register(`buckets.${index}.vesting_months`, { valueAsNumber: true })}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
