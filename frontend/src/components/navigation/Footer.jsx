import Brand from '../ui/Brand'

export default function Footer() {
  return (
    <footer className="border-t bg-[var(--surface)] dark:border-[#26384f] dark:bg-[#07111f]">
      <div className="container-page grid gap-8 py-10 sm:grid-cols-[1fr_auto] sm:items-end">
        <div>
          <Brand />
          <p className="mt-3 max-w-md text-sm text-slate-500">A focused workspace for building career readiness with clarity.</p>
          <p className="mt-2 text-xs text-slate-500">Final-year B.Tech CSE project · Career intelligence and placement preparation</p>
        </div>
        <div className="sm:text-right"><nav aria-label="Footer navigation" className="flex flex-wrap gap-x-5 gap-y-2 text-sm font-medium"><a href="#features" className="hover:text-blue-700 dark:hover:text-blue-300">Features</a><a href="#how-it-works" className="hover:text-blue-700 dark:hover:text-blue-300">How it works</a><a href="#platform" className="hover:text-blue-700 dark:hover:text-blue-300">Product</a></nav><p className="mt-4 text-xs text-slate-500">© {new Date().getFullYear()} SkillSync. Built for better preparation.</p></div>
      </div>
    </footer>
  )
}
