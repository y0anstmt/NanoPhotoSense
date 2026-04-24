export interface StreamControlResponse {
  message: string;
  sensorId: string;
  status: 'active' | 'inactive' | string;
}

export interface StreamsStatusResponse {
  streams: Record<string, boolean>;
  totalSensors: number;
  activeSensors: number;
}

export interface SpectralReading {
  id: number;
  sensorId: string;
  timestamp: string;
  peakWavelength: number;
  intensities: string;
  refractiveIndex: number;
  deltaN: number;
  riskScore: number;
}

export interface Alert {
  id: number;
  sensorId: string;
  timestamp: string;
  alertType: string;
  severity: string;
  alertMessage: string;
  acknowledged: boolean;
}

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | string;

export interface SensorRiskSummary {
  sensorId: string;
  windowMinutes: number;
  latestTimestamp: string;
  latestDeltaN: number;
  latestRiskScore: number;
  riskLevel: RiskLevel;
  deltaNTrendPerHour: number;
  meanRiskScore: number;
  readingsInWindow: number;
}

export interface LandslideRiskOverview {
  windowMinutes: number;
  sensorCount: number;
  highOrCriticalCount: number;
  sensors: SensorRiskSummary[];
}
