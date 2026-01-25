import { useFormContext, useFieldArray } from 'react-hook-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Plus, Trash2 } from 'lucide-react'
import type { SimulationConfig } from '@/types/config'

export function VestingScheduleTab() {
  const { register, control } = useFormContext<SimulationConfig>()
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'buckets'
  })

  const handleAddBucket = () => {
    append({
      bucket: `Bucket ${fields.length + 1}`,
      allocation: 0,
      tge_unlock_pct: 0,
      cliff_months: 0,
      vesting_months: 12
    })
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Vesting Schedule</CardTitle>
            <CardDescription>
              Configure unlock schedules for each bucket
            </CardDescription>
          </div>
          <Button onClick={handleAddBucket} size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Bucket
          </Button>
        </div>
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
                <th className="text-left p-2 w-16"></th>
              </tr>
            </thead>
            <tbody>
              {fields.map((field, index) => (
                <tr key={field.id} className="border-b">
                  <td className="p-2">
                    <Input {...register(`buckets.${index}.bucket`)} />
                  </td>
                  <td className="p-2">
                    <Input
                      type="number"
                      step="0.01"
                      {...register(`buckets.${index}.allocation`, { valueAsNumber: true })}
                    />
                  </td>
                  <td className="p-2">
                    <Input
                      type="number"
                      step="0.01"
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
                  <td className="p-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => remove(index)}
                      disabled={fields.length === 1}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
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
