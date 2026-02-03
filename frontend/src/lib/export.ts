const formatCell = (value: unknown): string => {
  if (value === null || value === undefined) {
    return ''
  }

  if (value instanceof Date) {
    return value.toISOString()
  }

  if (typeof value === 'object') {
    return JSON.stringify(value)
  }

  const text = String(value)
  if (text.includes('"') || text.includes(',') || text.includes('\n')) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

export const convertToCSV = <T extends Record<string, unknown>>(data: T[]): string => {
  if (!data.length) {
    return ''
  }

  const headers = Object.keys(data[0])
  const lines = [
    headers.join(',')
  ]

  for (const row of data) {
    const values = headers.map(header => formatCell(row[header]))
    lines.push(values.join(','))
  }

  return lines.join('\n')
}

export const downloadFile = (content: string, filename: string, type: string): void => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
