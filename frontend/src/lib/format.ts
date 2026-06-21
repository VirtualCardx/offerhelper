export function formatCurrency(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return '--'
  }
  const amount = Number(value)
  if (Number.isNaN(amount)) {
    return '--'
  }
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    maximumFractionDigits: 2,
  }).format(amount)
}

export function formatPercent(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return '--'
  }
  const amount = Number(value)
  if (Number.isNaN(amount)) {
    return '--'
  }
  return `${(amount * 100).toFixed(1)}%`
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return '--'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '--'
  }
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}
