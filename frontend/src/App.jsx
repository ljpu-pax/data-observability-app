import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import io from 'socket.io-client'
import './App.css'

const BACKEND_URL = 'http://localhost:5001'
const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1']

function App() {
  const [data, setData] = useState({})
  const [signals, setSignals] = useState([])
  const [connected, setConnected] = useState(false)
  const socketRef = useRef(null)

  // Fetch historical data on mount
  useEffect(() => {
    fetch(`${BACKEND_URL}/api/telemetry?hours=1`)
      .then(res => res.json())
      .then(historicalData => {
        setData(historicalData)
        setSignals(Object.keys(historicalData))
      })
      .catch(err => console.error('Error fetching historical data:', err))
  }, [])

  // Setup WebSocket connection for live updates
  useEffect(() => {
    socketRef.current = io(BACKEND_URL)

    socketRef.current.on('connect', () => {
      console.log('Connected to backend')
      setConnected(true)
    })

    socketRef.current.on('disconnect', () => {
      console.log('Disconnected from backend')
      setConnected(false)
    })

    socketRef.current.on('telemetry_update', (payload) => {
      const { timestamp, signals: newSignals } = payload

      setData(prevData => {
        const updatedData = { ...prevData }

        Object.entries(newSignals).forEach(([signalName, value]) => {
          if (!updatedData[signalName]) {
            updatedData[signalName] = []
          }

          updatedData[signalName] = [
            ...updatedData[signalName],
            { timestamp, value }
          ]

          // Keep only last hour of data (3600 seconds at 1 sample/sec = 3600 points)
          const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString()
          updatedData[signalName] = updatedData[signalName].filter(
            point => point.timestamp >= oneHourAgo
          )
        })

        return updatedData
      })

      setSignals(prevSignals => {
        const newSignalNames = Object.keys(newSignals)
        const uniqueSignals = [...new Set([...prevSignals, ...newSignalNames])]
        return uniqueSignals
      })
    })

    return () => {
      socketRef.current.disconnect()
    }
  }, [])

  // Transform data for recharts
  const getChartData = () => {
    if (signals.length === 0) return []

    // Get all unique timestamps
    const allTimestamps = new Set()
    signals.forEach(signal => {
      if (data[signal]) {
        data[signal].forEach(point => allTimestamps.add(point.timestamp))
      }
    })

    const sortedTimestamps = Array.from(allTimestamps).sort()

    // Create data points for each timestamp
    return sortedTimestamps.map(timestamp => {
      const dataPoint = { timestamp }
      signals.forEach(signal => {
        const point = data[signal]?.find(p => p.timestamp === timestamp)
        dataPoint[signal] = point ? point.value : null
      })
      return dataPoint
    })
  }

  const chartData = getChartData()

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Telemetry Dashboard</h1>
        <div className="status">
          <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}></span>
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </header>

      <main className="main">
        <div className="stats">
          <div className="stat-card">
            <div className="stat-label">Signals</div>
            <div className="stat-value">{signals.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Data Points</div>
            <div className="stat-value">{chartData.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Time Range</div>
            <div className="stat-value">1 Hour</div>
          </div>
        </div>

        <div className="chart-container">
          <h2>Live Signal Data</h2>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={500}>
              <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={formatTimestamp}
                  stroke="#8b949e"
                  tick={{ fill: '#8b949e' }}
                />
                <YAxis
                  stroke="#8b949e"
                  tick={{ fill: '#8b949e' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#161b22',
                    border: '1px solid #30363d',
                    borderRadius: '6px',
                    color: '#e6edf3'
                  }}
                  labelFormatter={formatTimestamp}
                />
                <Legend
                  wrapperStyle={{ color: '#e6edf3' }}
                />
                {signals.map((signal, index) => (
                  <Line
                    key={signal}
                    type="monotone"
                    dataKey={signal}
                    stroke={COLORS[index % COLORS.length]}
                    dot={false}
                    strokeWidth={2}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">
              <p>No data available. Start the producer to see live telemetry.</p>
            </div>
          )}
        </div>

        <div className="signals-list">
          <h3>Active Signals</h3>
          <div className="signals-grid">
            {signals.map((signal, index) => {
              const latestValue = data[signal]?.[data[signal].length - 1]?.value
              return (
                <div key={signal} className="signal-card">
                  <div
                    className="signal-color"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  ></div>
                  <div className="signal-info">
                    <div className="signal-name">{signal}</div>
                    <div className="signal-value">
                      {latestValue !== undefined ? latestValue.toFixed(2) : 'N/A'}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
