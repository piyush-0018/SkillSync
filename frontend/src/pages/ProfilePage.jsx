import { motion } from 'framer-motion'
import { UserRound } from 'lucide-react'
import ProfileForm from '../components/profile/ProfileForm'
import PageHeader from '../components/ui/PageHeader'

export default function ProfilePage() {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .24 }} className="mx-auto max-w-3xl">
      <PageHeader icon={UserRound} kicker="Account" title="Your profile" description="Keep your identity and career direction up to date." />
      <section className="surface-panel mt-8 p-6 sm:p-8"><ProfileForm /></section>
    </motion.div>
  )
}
