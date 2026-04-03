import { ref, onMounted, onUnmounted, type Ref } from 'vue'

export function useWorkbenchContextMenu(
  containerRef: Ref<HTMLElement | null>
) {
  const isMenuOpen = ref(false)
  const menuX = ref(0)
  const menuY = ref(0)

  const openMenu = (e: MouseEvent) => {
    e.preventDefault()
    isMenuOpen.value = true
    menuX.value = e.clientX
    menuY.value = e.clientY
    
    setTimeout(() => {
      containerRef.value?.focus()
    }, 0)
  }

  const closeMenu = () => {
    isMenuOpen.value = false
  }

  const handleOutsideClick = (e: MouseEvent) => {
    if (isMenuOpen.value && containerRef.value && !containerRef.value.contains(e.target as Node)) {
      closeMenu()
    }
  }

  const handleKeydown = (e: KeyboardEvent) => {
    if (isMenuOpen.value && e.key === 'Escape') {
      closeMenu()
    }
  }

  onMounted(() => {
    document.addEventListener('click', handleOutsideClick)
    document.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    document.removeEventListener('click', handleOutsideClick)
    document.removeEventListener('keydown', handleKeydown)
  })

  return {
    isMenuOpen,
    menuX,
    menuY,
    openMenu,
    closeMenu
  }
}
