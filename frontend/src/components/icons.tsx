import type { ReactNode, SVGProps } from 'react'

// Outline icons drawn for this app (white stroke only), shared by the cursor tail and the UI.
export const ICON_SHAPES = {
  like: (
    <path d="M7 10v11H4a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1h3Zm0 0 4-7a2 2 0 0 1 2 2.5L12.3 9H19a2 2 0 0 1 2 2.3l-1.2 7.4A2 2 0 0 1 17.8 21H7" />
  ),
  bell: (
    <g>
      <path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4l2-2Z" />
      <path d="M10 21a2 2 0 0 0 4 0" />
    </g>
  ),
  play: (
    <g>
      <rect x="2.5" y="5" width="19" height="14" rx="4" />
      <path d="m10 9 5 3-5 3V9Z" />
    </g>
  ),
  playlist: <path d="M3 6h12M3 11h12M3 16h7M17 14v6M14 17h6" />,
  external: (
    <g>
      <path d="M14 4h6v6M20 4l-9 9" />
      <path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
    </g>
  ),
} satisfies Record<string, ReactNode>

export type IconName = keyof typeof ICON_SHAPES

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName
  size?: number
}

export function Icon({ name, size = 16, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      {...rest}
    >
      {ICON_SHAPES[name]}
    </svg>
  )
}
