import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

// Mock socket.io-client
vi.mock('socket.io-client', () => ({
  default: vi.fn(() => ({
    on: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn()
  }))
}))

// Mock fetch
global.fetch = vi.fn()

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Mock successful fetch response
    global.fetch.mockResolvedValue({
      json: async () => ({
        sine_wave: [
          { timestamp: '2024-01-01T00:00:00Z', value: 5.5 },
          { timestamp: '2024-01-01T00:00:01Z', value: 6.0 }
        ],
        cosine_wave: [
          { timestamp: '2024-01-01T00:00:00Z', value: 3.2 },
          { timestamp: '2024-01-01T00:00:01Z', value: 3.5 }
        ]
      })
    })
  })

  it('renders the app title', () => {
    render(<App />)
    expect(screen.getByText('Telemetry Dashboard')).toBeDefined()
  })

  it('displays status indicator', () => {
    render(<App />)
    const statusElements = screen.getAllByText(/Connected|Disconnected/)
    expect(statusElements.length).toBeGreaterThan(0)
  })

  it('shows stat cards', () => {
    render(<App />)
    expect(screen.getByText('Signals')).toBeDefined()
    expect(screen.getByText('Data Points')).toBeDefined()
    expect(screen.getByText('Time Range')).toBeDefined()
  })

  it('fetches historical data on mount', async () => {
    render(<App />)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/telemetry?hours=1')
      )
    })
  })

  it('displays chart title', () => {
    render(<App />)
    expect(screen.getByText('Live Signal Data')).toBeDefined()
  })

  it('displays active signals section', () => {
    render(<App />)
    expect(screen.getByText('Active Signals')).toBeDefined()
  })

  it('shows signals after data is loaded', async () => {
    render(<App />)

    await waitFor(() => {
      const signalCount = screen.getByText('Signals').parentElement.querySelector('.stat-value')
      expect(signalCount).toBeDefined()
    })
  })
})
