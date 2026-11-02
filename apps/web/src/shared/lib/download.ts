/** Saves a downloaded file through a temporary link. */
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.append(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 0)
}

export function filenameFrom(contentDisposition: string | null, fallback: string): string {
  const match = contentDisposition?.match(/filename="([^"]+)"/)
  return match ? match[1] : fallback
}
