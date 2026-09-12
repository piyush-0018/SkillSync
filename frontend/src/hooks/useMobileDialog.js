import { useEffect } from 'react'

export default function useMobileDialog(ref, open, onClose) {
  useEffect(() => {
    if (!open) return undefined
    const media = window.matchMedia('(max-width: 1023px)')
    let release = () => {}

    function update() {
      release()
      release = () => {}
      const panel = ref.current
      if (!media.matches || !panel) return
      const previous = document.activeElement
      const overflow = document.body.style.overflow
      const controls = () => [...panel.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), [tabindex="0"]')]
        .filter((element) => element.getClientRects().length)
      const frame = requestAnimationFrame(() => controls()[0]?.focus())
      document.body.style.overflow = 'hidden'

      function handleKey(event) {
        if (event.key === 'Escape') { event.preventDefault(); onClose(); return }
        if (event.key !== 'Tab') return
        const elements = controls()
        const first = elements[0]
        const last = elements.at(-1)
        if (event.shiftKey && (document.activeElement === first || !panel.contains(document.activeElement))) {
          event.preventDefault()
          last?.focus()
        } else if (!event.shiftKey && (document.activeElement === last || !panel.contains(document.activeElement))) {
          event.preventDefault()
          first?.focus()
        }
      }
      document.addEventListener('keydown', handleKey)
      release = () => {
        cancelAnimationFrame(frame)
        document.removeEventListener('keydown', handleKey)
        document.body.style.overflow = overflow
        if (previous?.isConnected) previous.focus()
      }
    }

    update()
    media.addEventListener('change', update)
    return () => { media.removeEventListener('change', update); release() }
  }, [onClose, open, ref])
}
