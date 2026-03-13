"use client";

const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://127.0.0.1:8000';
};

const API_BASE_URL = getApiBaseUrl();

export class DashboardService {
  static async getSystemStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/system/status`);
      if (!response.ok) throw new Error('Failed to fetch system status');
      return await response.json();
    } catch (error) {
      console.error('Error fetching system status:', error);
      return null;
    }
  }

  static async getTasks() {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks`);
      if (!response.ok) throw new Error('Failed to fetch tasks');
      return await response.json();
    } catch (error) {
      console.error('Error fetching tasks:', error);
      return [];
    }
  }

  static async getAgents() {
    try {
      const response = await fetch(`${API_BASE_URL}/agents`);
      if (!response.ok) throw new Error('Failed to fetch agents');
      return await response.json();
    } catch (error) {
      console.error('Error fetching agents:', error);
      return [];
    }
  }

  static async submitTask(description: string, agentType: string = 'swarm') {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Authentication would go here if needed
          'Authorization': 'Bearer demo-token' // The backend seems to have security enabled
        },
        body: JSON.stringify({
          description,
          agent_type: agentType,
          priority: 5
        })
      });
      if (!response.ok) throw new Error('Failed to submit task');
      return await response.json();
    } catch (error) {
      console.error('Error submitting task:', error);
      return null;
    }
  }
  
  // Connect to the correct WebSocket endpoint
  static connectEvents(onMessage: (data: any) => void) {
    const wsUrl = `ws://${API_BASE_URL.replace('http://', '')}/ws`;
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => onMessage(JSON.parse(event.data));
    return ws;
  }
}
