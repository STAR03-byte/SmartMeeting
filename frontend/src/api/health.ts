import { apiClient } from "./client";

export interface HealthChecks {
  database: boolean;
  jwt_secret: boolean;
  ffmpeg: boolean;
  storage: boolean;
}

export interface HealthDatabaseStatus {
  connected: boolean;
  backend: string;
  error?: string;
}

export interface PrivateDeploymentStatus {
  jwt_secret_configured: boolean;
  jwt_secret_uses_default: boolean;
  ffmpeg_available: boolean;
  storage_dir: string;
  storage_dir_exists: boolean;
  storage_dir_writable: boolean;
  llm_provider: string;
  llm_configured: boolean;
  whisper_allow_mock_fallback: boolean;
}

export interface PreflightStatus {
  status: "ok" | "degraded";
  checks: HealthChecks;
  database: HealthDatabaseStatus;
  private_deployment: PrivateDeploymentStatus;
}

export interface SimpleHealthStatus {
  status: string;
}

export async function getPreflightStatus(): Promise<PreflightStatus> {
  const resp = await apiClient.get<PreflightStatus>("/api/v1/health/preflight");
  return resp.data;
}

export async function getLivenessStatus(): Promise<SimpleHealthStatus> {
  const resp = await apiClient.get<SimpleHealthStatus>("/api/v1/health/live");
  return resp.data;
}

export async function getReadinessStatus(): Promise<SimpleHealthStatus> {
  const resp = await apiClient.get<SimpleHealthStatus>("/api/v1/health/ready");
  return resp.data;
}
