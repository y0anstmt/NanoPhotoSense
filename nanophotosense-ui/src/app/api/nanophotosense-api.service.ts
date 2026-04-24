import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  Alert,
  LandslideRiskOverview,
  SpectralReading,
  StreamControlResponse,
  StreamsStatusResponse,
} from './nanophotosense-api.models';

@Injectable({ providedIn: 'root' })
export class NanoPhotoSenseApiService {
  private readonly baseUrl = 'http://localhost:8080';

  constructor(private readonly http: HttpClient) {}

  getStreamsStatus(): Observable<StreamsStatusResponse> {
    return this.http.get<StreamsStatusResponse>(`${this.baseUrl}/api/streams/status`);
  }

  startStream(sensorId: string): Observable<StreamControlResponse> {
    return this.http.post<StreamControlResponse>(`${this.baseUrl}/api/streams/${encodeURIComponent(sensorId)}/start`, {});
  }

  stopStream(sensorId: string): Observable<StreamControlResponse> {
    return this.http.post<StreamControlResponse>(`${this.baseUrl}/api/streams/${encodeURIComponent(sensorId)}/stop`, {});
  }

  getLatestReadings(limit = 10): Observable<SpectralReading[]> {
    const params = new HttpParams().set('limit', String(limit));
    return this.http.get<SpectralReading[]>(`${this.baseUrl}/api/spectral-readings/latest`, { params });
  }

  getReadingsBySensor(sensorId: string, page = 0, size = 20): Observable<SpectralReading[]> {
    const params = new HttpParams().set('page', String(page)).set('size', String(size));
    return this.http.get<SpectralReading[]>(
      `${this.baseUrl}/api/spectral-readings/sensor/${encodeURIComponent(sensorId)}`,
      { params }
    );
  }

  getAlerts(options?: { acknowledged?: boolean; page?: number; size?: number }): Observable<Alert[]> {
    let params = new HttpParams();
    if (options?.acknowledged !== undefined) {
      params = params.set('acknowledged', String(options.acknowledged));
    }
    if (options?.page !== undefined) {
      params = params.set('page', String(options.page));
    }
    if (options?.size !== undefined) {
      params = params.set('size', String(options.size));
    }

    return this.http.get<Alert[]>(`${this.baseUrl}/api/alerts`, { params });
  }

  acknowledgeAlert(id: number): Observable<Alert> {
    return this.http.put<Alert>(`${this.baseUrl}/api/alerts/${id}/acknowledge`, {});
  }

  getLandslideRiskOverview(windowMinutes = 60): Observable<LandslideRiskOverview> {
    const params = new HttpParams().set('windowMinutes', String(windowMinutes));
    return this.http.get<LandslideRiskOverview>(`${this.baseUrl}/api/landslide-risk/overview`, { params });
  }
}
