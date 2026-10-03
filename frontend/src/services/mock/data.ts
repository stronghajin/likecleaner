// Generates a believable fake YouTube account: liked videos and playlists.
// A fixed seed means everyone gets the same data after a reset.

export interface MockVideo {
  id: string
  title: string
  channelId: string
  channelTitle: string
  categoryName: string
  durationSeconds: number
  publishedAt: string
}

export interface MockPlaylistItem {
  id: string
  videoId: string
  /** Set only for deleted/private entries, whose video no longer exists. */
  unavailable?: 'deleted' | 'private'
}

export interface MockPlaylist {
  id: string
  title: string
  /** Auto-sorted playlists reject `position=0` with manualSortRequired (SPEC.md 6-6). */
  manualSort: boolean
  items: MockPlaylistItem[]
}

export interface MockAccount {
  videos: Record<string, MockVideo>
  /** Liked video IDs, most recently liked first. */
  likedIds: string[]
  playlists: MockPlaylist[]
}

// Small seeded random generator (mulberry32).
function createRandom(seed: number) {
  let a = seed
  const next = () => {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  return {
    next,
    int: (min: number, max: number) => min + Math.floor(next() * (max - min + 1)),
    pick: <T,>(list: readonly T[]): T => list[Math.floor(next() * list.length)],
    chance: (p: number) => next() < p,
  }
}

const ID_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'

const TITLES: Record<string, string[]> = {
  Music: [
    'Lofi beats to study and relax',
    'Live at the Rooftop Session',
    'Acoustic cover of a 90s classic',
    'Official Music Video',
    'Night drive synthwave mix',
    'Jazz piano for rainy mornings',
    '1 hour of calm guitar',
  ],
  Gaming: [
    'Speedrun world record attempt',
    'Beginner tips you wish you knew',
    'Boss fight without taking damage',
    'Building a giant castle in survival mode',
    'Ranked climb, episode',
    'Every secret in the first level',
  ],
  Education: [
    'How the internet actually works',
    'Calculus explained in 10 minutes',
    'The history of the printing press',
    'Why the sky is blue',
    'Learn Python in one video',
    'Introduction to microeconomics',
  ],
  Entertainment: [
    'Reacting to my old videos',
    'We tried every snack at the airport',
    '24 hours in a tiny cabin',
    'Behind the scenes of our biggest show',
    'Fans pick my outfit for a week',
  ],
  'Science & Technology': [
    'Unboxing the new flagship phone',
    'I built a mechanical keyboard from scratch',
    'How rockets land themselves',
    'Home lab server tour',
    'Is this budget laptop any good?',
    'Inside a chip factory',
  ],
  Comedy: [
    'When your group project goes wrong',
    'Office meetings be like',
    'Stand-up special full set',
    'Things nobody tells you about adulthood',
  ],
  'Howto & Style': [
    '15-minute pasta for busy nights',
    'Minimalist desk setup makeover',
    'How to fold a fitted sheet',
    'Easy sourdough for beginners',
    'Capsule wardrobe for every season',
  ],
  Sports: [
    'Top 10 goals of the season',
    'Full match highlights',
    'Marathon training week in my life',
    'Pro climber reacts to beginner routes',
  ],
  'News & Politics': [
    'Weekly news recap',
    'Explaining the new housing policy',
    'Election night analysis',
  ],
  'Film & Animation': [
    'Short film: The Last Train',
    'Every frame a painting breakdown',
    'Stop motion experiment',
    'Movie trailer reaction and theories',
  ],
  'People & Blogs': [
    'A quiet day in Seoul',
    'Moving into my first apartment',
    'What I eat in a week',
    'Q&A: answering your questions',
  ],
  'Travel & Events': [
    'Walking tour of Kyoto at night',
    'Cheapest way to travel Europe',
    'Train journey across the Alps',
    'Hidden beaches you have to see',
  ],
}

const CHANNELS: { title: string; category: string }[] = [
  { title: 'Lofi Harbor', category: 'Music' },
  { title: 'Rooftop Sessions', category: 'Music' },
  { title: 'Synth City', category: 'Music' },
  { title: 'Morning Jazz Club', category: 'Music' },
  { title: 'PixelRun', category: 'Gaming' },
  { title: 'Block Builders', category: 'Gaming' },
  { title: 'Respawn Daily', category: 'Gaming' },
  { title: 'Explained Simply', category: 'Education' },
  { title: 'Math in Minutes', category: 'Education' },
  { title: 'History Lane', category: 'Education' },
  { title: 'Snack Squad', category: 'Entertainment' },
  { title: 'Cabin Crew Vlogs', category: 'Entertainment' },
  { title: 'Tech Bench', category: 'Science & Technology' },
  { title: 'Orbit Lab', category: 'Science & Technology' },
  { title: 'Keyboard Garage', category: 'Science & Technology' },
  { title: 'Desk Jokes', category: 'Comedy' },
  { title: 'Stand Up Nights', category: 'Comedy' },
  { title: 'Kitchen in 15', category: 'Howto & Style' },
  { title: 'Simple Living Studio', category: 'Howto & Style' },
  { title: 'Goal Rush', category: 'Sports' },
  { title: 'Run Club', category: 'Sports' },
  { title: 'The Weekly Brief', category: 'News & Politics' },
  { title: 'Frame by Frame', category: 'Film & Animation' },
  { title: 'Seoul Diaries', category: 'People & Blogs' },
  { title: 'Slow Travel', category: 'Travel & Events' },
]

const VIDEO_POOL_SIZE = 480
const LIKED_COUNT = 320

export function generateAccount(seed = 20261002): MockAccount {
  const rnd = createRandom(seed)
  const makeId = (length: number) =>
    Array.from({ length }, () => rnd.pick(ID_CHARS.split(''))).join('')

  const durationFor = () => {
    const kind = rnd.next()
    if (kind < 0.12) return rnd.int(15, 59) // shorts
    if (kind < 0.75) return rnd.int(60, 20 * 60)
    if (kind < 0.95) return rnd.int(20 * 60, 70 * 60)
    return rnd.int(70 * 60, 3 * 3600)
  }

  const publishedFor = () => {
    const start = Date.UTC(2009, 0, 1)
    const end = Date.UTC(2026, 8, 30)
    return new Date(start + rnd.next() * (end - start)).toISOString()
  }

  const channels = CHANNELS.map((c) => ({ ...c, id: `UC${makeId(22)}` }))
  const videos: Record<string, MockVideo> = {}
  const videoIds: string[] = []
  for (let i = 0; i < VIDEO_POOL_SIZE; i++) {
    const channel = rnd.pick(channels)
    const base = rnd.pick(TITLES[channel.category])
    const title = rnd.chance(0.4) ? `${base} #${rnd.int(1, 120)}` : base
    const id = makeId(11)
    videos[id] = {
      id,
      title,
      channelId: channel.id,
      channelTitle: channel.title,
      categoryName: channel.category,
      durationSeconds: durationFor(),
      publishedAt: publishedFor(),
    }
    videoIds.push(id)
  }

  const likedIds = videoIds.slice(0, LIKED_COUNT)
  const others = videoIds.slice(LIKED_COUNT)

  let itemSeq = 0
  const entry = (videoId: string): MockPlaylistItem => ({ id: `PLI${makeId(8)}${itemSeq++}`, videoId })
  const unavailable = (kind: 'deleted' | 'private'): MockPlaylistItem => ({
    ...entry(makeId(11)),
    unavailable: kind,
  })

  /** Builds a playlist: unique videos, then extra copies of some of them, then unavailable entries. */
  const playlist = (
    title: string,
    opts: { from: string[]; unique: number; duplicates?: number; deleted?: number; private?: number; manualSort?: boolean },
  ): MockPlaylist => {
    const pool = [...opts.from].sort(() => rnd.next() - 0.5)
    const items = pool.slice(0, opts.unique).map(entry)
    for (let i = 0; i < (opts.duplicates ?? 0); i++) items.push(entry(rnd.pick(items).videoId))
    for (let i = 0; i < (opts.deleted ?? 0); i++) items.push(unavailable('deleted'))
    for (let i = 0; i < (opts.private ?? 0); i++) items.push(unavailable('private'))
    items.sort(() => rnd.next() - 0.5)
    return { id: `PL${makeId(32)}`, title, manualSort: opts.manualSort ?? true, items }
  }

  const music = videoIds.filter((id) => videos[id].categoryName === 'Music')
  const tech = videoIds.filter((id) => videos[id].categoryName === 'Science & Technology')

  const playlists: MockPlaylist[] = [
    // Shares many videos with the liked list, to test "already in playlist" skips.
    playlist('Favorites Mix', { from: likedIds.slice(0, 120), unique: 80, duplicates: 5 }),
    playlist('Workout', { from: music, unique: 32, duplicates: 8 }),
    playlist('Watch Again', { from: others, unique: 50, deleted: 6, private: 4 }),
    playlist('Study Music', { from: music, unique: 25 }),
    // Large: tests paging and the 100-item limit for Remove Duplicates (DECISIONS.md 7).
    playlist('Big Archive', { from: videoIds, unique: 280, duplicates: 130, deleted: 10, private: 5 }),
    // Not manually sorted: adding at position 0 fails once with manualSortRequired.
    playlist('Tech Talks', { from: tech, unique: 24, manualSort: false }),
    playlist('New Playlist', { from: [], unique: 0 }),
  ]

  return { videos, likedIds, playlists }
}

/** Gray placeholder thumbnail (120×90) with the channel's initials, in Black Mode colors only. */
export function thumbnailFor(channelTitle: string): string {
  const initials = channelTitle
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="120" height="90" viewBox="0 0 120 90"><rect width="120" height="90" fill="#2A2A2A"/><text x="60" y="52" font-family="system-ui,sans-serif" font-size="22" font-weight="600" fill="#A1A1A1" text-anchor="middle">${initials}</text></svg>`
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}

export function avatarFor(name: string): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><circle cx="32" cy="32" r="32" fill="#2A2A2A"/><text x="32" y="41" font-family="system-ui,sans-serif" font-size="26" font-weight="600" fill="#F5F5F5" text-anchor="middle">${name[0]}</text></svg>`
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}
