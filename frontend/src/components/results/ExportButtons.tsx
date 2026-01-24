import { useFormContext } from 'react-hook-form'
import { Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { convertToCSV, downloadFile } from '@/lib/export'
import type { SimulationConfig } from '@/types/config'
import type { SimulationResponse } from '@/types/simulation'

interface ExportButtonsProps {
  simulation: SimulationResponse
}

export function ExportButtons({ simulation }: ExportButtonsProps) {
  const { getValues } = useFormContext<SimulationConfig>()

  const handleExportCSV = () => {
    const bucketCSV = convertToCSV(simulation.data.bucket_results)
    const globalCSV = convertToCSV(simulation.data.global_metrics)

    downloadFile(bucketCSV, 'bucket_schedule.csv', 'text/csv')
    downloadFile(globalCSV, 'global_metrics.csv', 'text/csv')
  }

  const handleExportJSON = () => {
    const config = getValues()
    const json = JSON.stringify(config, null, 2)
    downloadFile(json, 'simulation_config.json', 'application/json')
  }

  return (
    <div className="flex gap-2">
      <Button variant="outline" size="sm" onClick={handleExportCSV}>
        <Download className="mr-2 h-4 w-4" />
        Export CSV
      </Button>
      <Button variant="outline" size="sm" onClick={handleExportJSON}>
        <Download className="mr-2 h-4 w-4" />
        Export Config
      </Button>
    </div>
  )
}
