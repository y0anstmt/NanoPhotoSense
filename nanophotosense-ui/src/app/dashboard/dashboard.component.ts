import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { NanoPhotoSenseApiService } from '../api/nanophotosense-api.service';
import {
  Alert,
  LandslideRiskOverview,
  SensorRiskSummary,
  SpectralReading,
  StreamsStatusResponse,
} from '../api/nanophotosense-api.models';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  streamsStatus?: StreamsStatusResponse;
  riskOverview?: LandslideRiskOverview;
  latestReadings: SpectralReading[] = [];
  unacknowledgedAlerts: Alert[] = [];

  selectedSensorId = '';
  selectedSensorReadings: SpectralReading[] = [];

  loading = false;
  errorMessage = '';

  constructor(private readonly api: NanoPhotoSenseApiService) {
    void this.refreshAll();
  }

  get sensorIds(): string[] {
    const fromStreams = this.streamsStatus ? Object.keys(this.streamsStatus.streams) : [];
    const fromRisk = this.riskOverview?.sensors?.map((s) => s.sensorId) ?? [];

    const set = new Set<string>([...fromStreams, ...fromRisk]);
    return Array.from(set).sort();
  }

  get selectedLatestReading(): SpectralReading | undefined {
    return this.selectedSensorReadings[0];
  }

  get selectedSensorRisk(): SensorRiskSummary | undefined {
    return this.riskOverview?.sensors?.find((sensor) => sensor.sensorId === this.selectedSensorId);
  }

  async refreshAll(): Promise<void> {
    this.loading = true;
    this.errorMessage = '';

    const results = await Promise.allSettled([
      firstValueFrom(this.api.getStreamsStatus()),
      firstValueFrom(this.api.getLandslideRiskOverview(60)),
      firstValueFrom(this.api.getAlerts({ acknowledged: false, size: 50 })),
      firstValueFrom(this.api.getLatestReadings(10)),
    ]);

    const [streamsStatus, riskOverview, alerts, latestReadings] = results;

    if (streamsStatus.status === 'fulfilled') {
      this.streamsStatus = streamsStatus.value;
    }

    if (riskOverview.status === 'fulfilled') {
      this.riskOverview = riskOverview.value;
    }

    if (alerts.status === 'fulfilled') {
      this.unacknowledgedAlerts = alerts.value;
    }

    if (latestReadings.status === 'fulfilled') {
      this.latestReadings = latestReadings.value;
    }

    const anyRejected = results.find((result) => result.status === 'rejected');
    if (anyRejected) {
      this.errorMessage =
        'Nu pot încărca complet datele din backend. Verifică dacă Quarkus rulează pe http://localhost:8080.';
    }

    if (!this.selectedSensorId) {
      this.selectedSensorId = this.sensorIds[0] ?? '';
    }

    await this.refreshSelectedSensor();
    this.loading = false;
  }

  async refreshSelectedSensor(): Promise<void> {
    if (!this.selectedSensorId) {
      this.selectedSensorReadings = [];
      return;
    }

    try {
      const readings = await firstValueFrom(
        this.api.getReadingsBySensor(this.selectedSensorId, 0, 20)
      );
      this.selectedSensorReadings = readings;
    } catch {
      this.selectedSensorReadings = [];
    }
  }

  async toggleStream(sensorId: string): Promise<void> {
    if (!this.streamsStatus) {
      return;
    }

    const isActive = !!this.streamsStatus.streams[sensorId];

    try {
      if (isActive) {
        await firstValueFrom(this.api.stopStream(sensorId));
      } else {
        await firstValueFrom(this.api.startStream(sensorId));
      }

      this.streamsStatus = await firstValueFrom(this.api.getStreamsStatus());
    } catch {
      this.errorMessage = 'Nu am putut porni/opri stream-ul pentru senzor.';
    }
  }

  async acknowledgeAlert(alertId: number): Promise<void> {
    try {
      await firstValueFrom(this.api.acknowledgeAlert(alertId));
      this.unacknowledgedAlerts = await firstValueFrom(
        this.api.getAlerts({ acknowledged: false, size: 50 })
      );
    } catch {
      this.errorMessage = 'Nu am putut confirma (acknowledge) alerta.';
    }
  }

  formatRiskLevel(riskLevel: string | undefined): string {
    return riskLevel ?? 'UNKNOWN';
  }

  parseIntensities(reading: SpectralReading | undefined): number[] {
    if (!reading?.intensities) {
      return [];
    }

    try {
      const parsed = JSON.parse(reading.intensities);
      if (!Array.isArray(parsed)) {
        return [];
      }

      const values = parsed
        .map((value) => Number(value))
        .filter((value) => Number.isFinite(value));

      return this.downsample(values, 200);
    } catch {
      return [];
    }
  }

  private downsample(values: number[], maxPoints: number): number[] {
    if (values.length <= maxPoints) {
      return values;
    }

    const step = Math.ceil(values.length / maxPoints);
    const sampled: number[] = [];

    for (let index = 0; index < values.length; index += step) {
      sampled.push(values[index]);
    }

    return sampled;
  }

  intensityPolylinePoints(values: number[], width = 400, height = 120, padding = 8): string {
    if (values.length < 2) {
      return '';
    }

    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = Math.max(1e-9, max - min);

    const innerWidth = width - padding * 2;
    const innerHeight = height - padding * 2;

    return values
      .map((value, index) => {
        const x = padding + (innerWidth * index) / (values.length - 1);
        const normalized = (value - min) / range;
        const y = padding + (1 - normalized) * innerHeight;
        return `${x.toFixed(2)},${y.toFixed(2)}`;
      })
      .join(' ');
  }
}
