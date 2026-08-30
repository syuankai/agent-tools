export interface ApiResponse {
  status: number;
  output: string;
  exit_code?: number;
  request_id?: string;
}

export interface HelpResponse {
  version: string;
  endpoints: Record<string, string>;
  responses: Record<string, string>;
  limits?: Record<string, string>;
  command_policy?: {
    blocked_commands: string[];
    block_environment_variable: string;
    note: string;
  };
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface StatsResponse {
  status: number;
  requests: number;
  tool_calls: number;
  errors: number;
  rate_limited: number;
  uptime_seconds: number;
  statuses: Record<string, number>;
}

export interface EnvResponse {
  status: number;
  variables: Record<string, string>;
}

export interface FileEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  modified: string;
  permissions: string;
}

export interface SystemInfo {
  hostname: string;
  platform: string;
  arch: string;
  kernel: string;
  uptime: number;
  cpu_count: number;
  memory_total: number;
  memory_used: number;
  memory_free: number;
  disk_total: number;
  disk_used: number;
  disk_free: number;
}

export interface DockerInfo {
  server_version: string;
  containers_running: number;
  containers_stopped: number;
  containers_paused: number;
  images: number;
  storage_driver: string;
}

export interface ProcessInfo {
  pid: number;
  user: string;
  cpu: number;
  mem: number;
  vsz: number;
  rss: number;
  stat: string;
  start: string;
  time: string;
  command: string;
}

export interface ApiEndpoint {
  method: "GET" | "POST";
  path: string;
  description: string;
  auth: boolean;
  body?: string;
  future?: boolean;
}

export interface FileItem {
  name: string;
  is_dir: boolean;
  size: number;
  modified: string;
}

export interface CommandResult {
  status: number;
  output: string;
  exit_code?: number;
  http_status: number;
  request_id?: string;
  duration_ms: number;
}

export interface PageProps {
  apiAvailable: boolean;
}
