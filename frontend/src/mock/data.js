// Mock data for development and fallback when API is unavailable

export const mockTrends = [
  {
    id: 1,
    category: 'animals',
    sub_category: 'penguins',
    name: 'Penguins',
    emoji: '🐧',
    coin_count: 47,
    total_market_cap: 285000000,
    top_coin: { symbol: 'PENGU', market_cap: 180000000, price: 0.0234 },
    acceleration_score: 92,
    trend_direction: 'up',
    velocity: 8.5,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 2,
    category: 'animals',
    sub_category: 'dogs',
    name: 'Dogs',
    emoji: '🐕',
    coin_count: 156,
    total_market_cap: 1250000000,
    top_coin: { symbol: 'BONK', market_cap: 850000000, price: 0.000012 },
    acceleration_score: 78,
    trend_direction: 'up',
    velocity: 5.2,
    created_at: '2023-12-01T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 3,
    category: 'animals',
    sub_category: 'cats',
    name: 'Cats',
    emoji: '🐱',
    coin_count: 89,
    total_market_cap: 520000000,
    top_coin: { symbol: 'MEW', market_cap: 320000000, price: 0.0089 },
    acceleration_score: 65,
    trend_direction: 'stable',
    velocity: 2.1,
    created_at: '2023-11-15T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 4,
    category: 'animals',
    sub_category: 'frogs',
    name: 'Frogs',
    emoji: '🐸',
    coin_count: 34,
    total_market_cap: 180000000,
    top_coin: { symbol: 'PEPE', market_cap: 120000000, price: 0.00000145 },
    acceleration_score: 85,
    trend_direction: 'up',
    velocity: 6.8,
    created_at: '2024-01-10T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 5,
    category: 'tech',
    sub_category: 'ai',
    name: 'AI / Artificial Intelligence',
    emoji: '🤖',
    coin_count: 78,
    total_market_cap: 890000000,
    top_coin: { symbol: 'TURBO', market_cap: 450000000, price: 0.0067 },
    acceleration_score: 88,
    trend_direction: 'up',
    velocity: 7.4,
    created_at: '2024-01-05T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 6,
    category: 'tech',
    sub_category: 'agents',
    name: 'AI Agents',
    emoji: '🦾',
    coin_count: 23,
    total_market_cap: 340000000,
    top_coin: { symbol: 'AIXBT', market_cap: 180000000, price: 0.42 },
    acceleration_score: 95,
    trend_direction: 'up',
    velocity: 12.3,
    created_at: '2024-01-20T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 7,
    category: 'memes',
    sub_category: 'wojak',
    name: 'Wojak',
    emoji: '😢',
    coin_count: 15,
    total_market_cap: 45000000,
    top_coin: { symbol: 'WOJAK', market_cap: 28000000, price: 0.00023 },
    acceleration_score: 42,
    trend_direction: 'down',
    velocity: -2.3,
    created_at: '2023-10-01T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 8,
    category: 'culture',
    sub_category: 'trump',
    name: 'Trump',
    emoji: '🇺🇸',
    coin_count: 67,
    total_market_cap: 2100000000,
    top_coin: { symbol: 'TRUMP', market_cap: 1800000000, price: 34.5 },
    acceleration_score: 72,
    trend_direction: 'stable',
    velocity: 1.5,
    created_at: '2024-01-18T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 9,
    category: 'animals',
    sub_category: 'hippos',
    name: 'Hippos',
    emoji: '🦛',
    coin_count: 12,
    total_market_cap: 95000000,
    top_coin: { symbol: 'MOODENG', market_cap: 75000000, price: 0.15 },
    acceleration_score: 68,
    trend_direction: 'up',
    velocity: 4.2,
    created_at: '2024-01-22T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 10,
    category: 'tech',
    sub_category: 'depin',
    name: 'DePIN',
    emoji: '📡',
    coin_count: 19,
    total_market_cap: 230000000,
    top_coin: { symbol: 'GRASS', market_cap: 150000000, price: 2.45 },
    acceleration_score: 55,
    trend_direction: 'stable',
    velocity: 1.8,
    created_at: '2024-01-08T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 11,
    category: 'animals',
    sub_category: 'goats',
    name: 'Goats',
    emoji: '🐐',
    coin_count: 8,
    total_market_cap: 125000000,
    top_coin: { symbol: 'GOAT', market_cap: 100000000, price: 0.78 },
    acceleration_score: 82,
    trend_direction: 'up',
    velocity: 5.9,
    created_at: '2024-01-25T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  },
  {
    id: 12,
    category: 'food',
    sub_category: 'peanuts',
    name: 'Peanuts',
    emoji: '🥜',
    coin_count: 5,
    total_market_cap: 35000000,
    top_coin: { symbol: 'PNUT', market_cap: 30000000, price: 0.045 },
    acceleration_score: 38,
    trend_direction: 'down',
    velocity: -3.1,
    created_at: '2024-01-12T10:00:00Z',
    updated_at: '2024-01-29T18:00:00Z'
  }
];

export const mockCoins = [
  // Penguin coins
  { id: 1, symbol: 'PENGU', name: 'Penguin Token', category: 'animals', sub_category: 'penguins', market_cap: 180000000, price: 0.0234, price_change_24h: 15.4, volume_24h: 45000000, created_at: '2024-01-15T10:00:00Z' },
  { id: 2, symbol: 'PENG', name: 'Peng Coin', category: 'animals', sub_category: 'penguins', market_cap: 45000000, price: 0.0089, price_change_24h: 8.2, volume_24h: 12000000, created_at: '2024-01-18T10:00:00Z' },
  { id: 3, symbol: 'WADDLE', name: 'Waddle Finance', category: 'animals', sub_category: 'penguins', market_cap: 25000000, price: 0.0045, price_change_24h: -2.3, volume_24h: 5000000, created_at: '2024-01-20T10:00:00Z' },

  // Dog coins
  { id: 4, symbol: 'BONK', name: 'Bonk', category: 'animals', sub_category: 'dogs', market_cap: 850000000, price: 0.000012, price_change_24h: 5.8, volume_24h: 120000000, created_at: '2023-12-01T10:00:00Z' },
  { id: 5, symbol: 'WIF', name: 'dogwifhat', category: 'animals', sub_category: 'dogs', market_cap: 320000000, price: 1.24, price_change_24h: 3.2, volume_24h: 85000000, created_at: '2023-12-15T10:00:00Z' },
  { id: 6, symbol: 'POPCAT', name: 'Popcat', category: 'animals', sub_category: 'dogs', market_cap: 45000000, price: 0.045, price_change_24h: -1.5, volume_24h: 8000000, created_at: '2024-01-05T10:00:00Z' },

  // Cat coins
  { id: 7, symbol: 'MEW', name: 'cat in a dogs world', category: 'animals', sub_category: 'cats', market_cap: 320000000, price: 0.0089, price_change_24h: 2.1, volume_24h: 45000000, created_at: '2023-11-15T10:00:00Z' },
  { id: 8, symbol: 'KITTY', name: 'Kitty Coin', category: 'animals', sub_category: 'cats', market_cap: 120000000, price: 0.0034, price_change_24h: 0.5, volume_24h: 18000000, created_at: '2023-12-01T10:00:00Z' },

  // AI coins
  { id: 9, symbol: 'TURBO', name: 'TurboAI', category: 'tech', sub_category: 'ai', market_cap: 450000000, price: 0.0067, price_change_24h: 12.3, volume_24h: 95000000, created_at: '2024-01-05T10:00:00Z' },
  { id: 10, symbol: 'GOATAI', name: 'Goatseus Maximus AI', category: 'tech', sub_category: 'ai', market_cap: 280000000, price: 0.45, price_change_24h: 18.5, volume_24h: 65000000, created_at: '2024-01-10T10:00:00Z' },

  // AI Agent coins
  { id: 11, symbol: 'AIXBT', name: 'AI XBT', category: 'tech', sub_category: 'agents', market_cap: 180000000, price: 0.42, price_change_24h: 25.6, volume_24h: 55000000, created_at: '2024-01-20T10:00:00Z' },
  { id: 12, symbol: 'VIRTUAL', name: 'Virtual Protocol', category: 'tech', sub_category: 'agents', market_cap: 120000000, price: 2.34, price_change_24h: 15.2, volume_24h: 35000000, created_at: '2024-01-22T10:00:00Z' },

  // Trump coins
  { id: 13, symbol: 'TRUMP', name: 'Official Trump', category: 'culture', sub_category: 'trump', market_cap: 1800000000, price: 34.5, price_change_24h: -2.5, volume_24h: 250000000, created_at: '2024-01-18T10:00:00Z' },
  { id: 14, symbol: 'MAGA', name: 'MAGA Token', category: 'culture', sub_category: 'trump', market_cap: 150000000, price: 0.85, price_change_24h: 5.8, volume_24h: 28000000, created_at: '2024-01-19T10:00:00Z' }
];

export const mockHistory = [
  // Penguin history
  { category: 'animals', sub_category: 'penguins', timestamp: '2024-01-23T00:00:00Z', market_cap: 180000000, coin_count: 35, acceleration_score: 75 },
  { category: 'animals', sub_category: 'penguins', timestamp: '2024-01-24T00:00:00Z', market_cap: 200000000, coin_count: 38, acceleration_score: 78 },
  { category: 'animals', sub_category: 'penguins', timestamp: '2024-01-25T00:00:00Z', market_cap: 225000000, coin_count: 40, acceleration_score: 82 },
  { category: 'animals', sub_category: 'penguins', timestamp: '2024-01-26T00:00:00Z', market_cap: 245000000, coin_count: 42, acceleration_score: 85 },
  { category: 'animals', sub_category: 'penguins', timestamp: '2024-01-27T00:00:00Z', market_cap: 260000000, coin_count: 44, acceleration_score: 88 },
  { category: 'animals', sub_category: 'penguins', timestamp: '2024-01-28T00:00:00Z', market_cap: 275000000, coin_count: 46, acceleration_score: 90 },
  { category: 'animals', sub_category: 'penguins', timestamp: '2024-01-29T00:00:00Z', market_cap: 285000000, coin_count: 47, acceleration_score: 92 },

  // AI Agents history
  { category: 'tech', sub_category: 'agents', timestamp: '2024-01-23T00:00:00Z', market_cap: 120000000, coin_count: 12, acceleration_score: 72 },
  { category: 'tech', sub_category: 'agents', timestamp: '2024-01-24T00:00:00Z', market_cap: 150000000, coin_count: 14, acceleration_score: 78 },
  { category: 'tech', sub_category: 'agents', timestamp: '2024-01-25T00:00:00Z', market_cap: 190000000, coin_count: 16, acceleration_score: 82 },
  { category: 'tech', sub_category: 'agents', timestamp: '2024-01-26T00:00:00Z', market_cap: 240000000, coin_count: 18, acceleration_score: 88 },
  { category: 'tech', sub_category: 'agents', timestamp: '2024-01-27T00:00:00Z', market_cap: 290000000, coin_count: 20, acceleration_score: 91 },
  { category: 'tech', sub_category: 'agents', timestamp: '2024-01-28T00:00:00Z', market_cap: 320000000, coin_count: 22, acceleration_score: 93 },
  { category: 'tech', sub_category: 'agents', timestamp: '2024-01-29T00:00:00Z', market_cap: 340000000, coin_count: 23, acceleration_score: 95 },

  // Dogs history
  { category: 'animals', sub_category: 'dogs', timestamp: '2024-01-23T00:00:00Z', market_cap: 1100000000, coin_count: 145, acceleration_score: 72 },
  { category: 'animals', sub_category: 'dogs', timestamp: '2024-01-24T00:00:00Z', market_cap: 1120000000, coin_count: 148, acceleration_score: 74 },
  { category: 'animals', sub_category: 'dogs', timestamp: '2024-01-25T00:00:00Z', market_cap: 1150000000, coin_count: 150, acceleration_score: 75 },
  { category: 'animals', sub_category: 'dogs', timestamp: '2024-01-26T00:00:00Z', market_cap: 1180000000, coin_count: 152, acceleration_score: 76 },
  { category: 'animals', sub_category: 'dogs', timestamp: '2024-01-27T00:00:00Z', market_cap: 1210000000, coin_count: 154, acceleration_score: 77 },
  { category: 'animals', sub_category: 'dogs', timestamp: '2024-01-28T00:00:00Z', market_cap: 1230000000, coin_count: 155, acceleration_score: 78 },
  { category: 'animals', sub_category: 'dogs', timestamp: '2024-01-29T00:00:00Z', market_cap: 1250000000, coin_count: 156, acceleration_score: 78 }
];

export const mockBreakoutMetas = [
  {
    cluster_id: 'cluster_001',
    suggested_name: 'Space Animals',
    coin_count: 8,
    common_terms: ['space', 'moon', 'rocket', 'astro'],
    total_market_cap: 45000000,
    avg_acceleration: 78,
    sample_coins: ['SPACEPENG', 'MOONDOG', 'ROCKETCAT'],
    detected_at: '2024-01-28T14:00:00Z'
  },
  {
    cluster_id: 'cluster_002',
    suggested_name: 'Gaming Memes',
    coin_count: 12,
    common_terms: ['game', 'play', 'level', 'boss'],
    total_market_cap: 68000000,
    avg_acceleration: 72,
    sample_coins: ['GAMEMEME', 'BOSSCAT', 'LEVELUP'],
    detected_at: '2024-01-28T16:00:00Z'
  },
  {
    cluster_id: 'cluster_003',
    suggested_name: 'Food Creatures',
    coin_count: 6,
    common_terms: ['food', 'eat', 'hungry', 'yum'],
    total_market_cap: 25000000,
    avg_acceleration: 65,
    sample_coins: ['HUNGRYPEPE', 'FOODOG', 'YUMCAT'],
    detected_at: '2024-01-29T08:00:00Z'
  }
];
