import { io } from "socket.io-client";
import { generateMockTelemetry, generateMockActiveUsers, generateMockIssue, generateMockResolution, generateMockHealth } from './mockData';

// API Configuration - Use AWS API Gateway
const API_URL = import.meta.env.VITE_API_URL || 'https://dcruqmbqjc.execute-api.us-east-1.amazonaws.com/dev';
const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:8000';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.mockInterval = null;
    this.useMockData = false;
  }

  static getInstance() {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  connect(onConnect) {
    if (this.socket?.connected) {
      return;
    }

    // Try to connect to WebSocket server
    this.socket = io(WS_URL, {
      transports: ["websocket"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 3,
      timeout: 5000,
    });

    this.socket.on("connect", () => {
      console.log("WebSocket connected to server");
      this.useMockData = false;
      if (this.mockInterval) {
        clearInterval(this.mockInterval);
        this.mockInterval = null;
      }
      if (onConnect) onConnect();
    });

    this.socket.on("disconnect", () => {
      console.log("WebSocket disconnected, switching to mock data");
      this.startMockDataStream();
    });

    this.socket.on("connect_error", (error) => {
      console.log("WebSocket connection failed, using mock data with AWS API");
      this.useMockData = true;
      this.startMockDataStream();
      // Still call onConnect so UI initializes
      if (onConnect) onConnect();
    });

    // Set up event listeners
    this.setupListeners();
    
    // Fetch initial data from AWS API
    this.fetchInitialData();
  }

  async fetchInitialData() {
    try {
      console.log("Fetching initial data from AWS API...");
      const response = await fetch(`${API_URL}/health`);
      if (response.ok) {
        const healthData = await response.json();
        console.log("AWS API health data:", healthData);
        // Emit health data to listeners
        const listeners = this.listeners.get('health') || [];
        listeners.forEach((callback) => callback({
          score: healthData.health_score || 94.5,
          status: healthData.overall_status || 'Operational'
        }));
      }
    } catch (error) {
      console.log("AWS API not available, using mock data");
    }
  }

  startMockDataStream() {
    if (this.mockInterval) return;
    
    console.log("Starting mock data stream for demo...");
    
    // Emit initial health
    const healthListeners = this.listeners.get('health') || [];
    healthListeners.forEach((callback) => callback(generateMockHealth()));
    
    // Stream mock data every 2 seconds
    this.mockInterval = setInterval(() => {
      // Telemetry
      const telemetryListeners = this.listeners.get('telemetry') || [];
      telemetryListeners.forEach((callback) => callback(generateMockTelemetry()));
      
      // Active Users
      const userListeners = this.listeners.get('activeUsers') || [];
      userListeners.forEach((callback) => callback(generateMockActiveUsers()));
      
      // Occasional issues (10% chance) - only if we haven't hit the limit
      if (Math.random() > 0.9) {
        const mockIssue = generateMockIssue();
        if (mockIssue) {
          const issueListeners = this.listeners.get('issue') || [];
          issueListeners.forEach((callback) => callback(mockIssue));
        }
      }
      
      // Occasional resolutions (5% chance)
      if (Math.random() > 0.95) {
        const resolutionListeners = this.listeners.get('resolution') || [];
        resolutionListeners.forEach((callback) => callback(generateMockResolution()));
      }
    }, 2000);
  }

  setupListeners() {
    const events = [
      "telemetry",
      "activeUsers",
      "issue",
      "resolution",
      "health",
    ];

    events.forEach((event) => {
      this.socket.on(event, (data) => {
        const listeners = this.listeners.get(event) || [];
        listeners.forEach((callback) => callback(data));
      });
    });
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;

    const listeners = this.listeners.get(event);
    const index = listeners.indexOf(callback);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  }

  subscribeToRegion(region) {
    if (this.socket?.connected) {
      this.socket.emit("subscribe", { region });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
}

export { WebSocketService };
