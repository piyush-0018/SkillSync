import { Outlet } from 'react-router-dom'
import Footer from '../components/navigation/Footer'
import Navbar from '../components/navigation/Navbar'

export default function MarketingLayout() {
  return <><Navbar /><Outlet /><Footer /></>
}
