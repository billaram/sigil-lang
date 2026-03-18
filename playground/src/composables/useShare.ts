export function useShare() {
  function encode(source: string, input: string): string {
    const params = new URLSearchParams()
    params.set('code', btoa(unescape(encodeURIComponent(source))))
    if (input && input.trim() !== '{}' && input.trim() !== '') {
      params.set('input', btoa(unescape(encodeURIComponent(input))))
    }
    return '#' + params.toString()
  }

  function decode(): { source?: string; input?: string } {
    const hash = window.location.hash.slice(1)
    if (!hash) return {}
    try {
      const params = new URLSearchParams(hash)
      const code = params.get('code')
      const input = params.get('input')
      return {
        source: code ? decodeURIComponent(escape(atob(code))) : undefined,
        input: input ? decodeURIComponent(escape(atob(input))) : undefined,
      }
    } catch {
      return {}
    }
  }

  function share(source: string, input: string) {
    const hashStr = encode(source, input)
    window.location.hash = hashStr
    const url = window.location.href
    navigator.clipboard.writeText(url).catch(() => {
      // Fallback: user can copy from address bar
    })
    return url
  }

  return { encode, decode, share }
}
