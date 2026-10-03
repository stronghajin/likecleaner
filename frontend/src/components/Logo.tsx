import { Link } from 'react-router'

export default function Logo({ size = 'md' }: { size?: 'md' | 'lg' }) {
  return (
    <Link
      to="/"
      className={`font-logo font-semibold tracking-tight text-accent ${size === 'lg' ? 'text-5xl' : 'text-2xl'}`}
    >
      LikeCleaner
    </Link>
  )
}
