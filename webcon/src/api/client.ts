import type { ApiResponse } from "./types";

const API_BASE = "";

class ApiError extends Error {
  status: number;
  output: string;

  constructor(status: number, output: string) {
    super(output);
    this.name = "ApiError";
    this.status = status;
    this.output = output;
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: string
): Promise<{ data: T; status: number; requestId?: string }> {
  const headers: Record<string, string> = {
    "Content-Type": "text/plain",
  };

  const apiKey = sessionStorage.getItem("api_key");
  if (apiKey) {
    headers["Authorization"] = `Bearer ${apiKey}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body,
  });

  const requestId =
    res.headers.get("X-Request-ID") ||
    res.headers.get("x-request-id") ||
    undefined;

  let data: T;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    data = (await res.json()) as T;
  } else {
    data = (await res.text()) as unknown as T;
  }

  return { data, status: res.status, requestId };
}

export async function getHelp() {
  return request<unknown>("GET", "/help");
}

export async function getHealth() {
  return request<unknown>("GET", "/health");
}

export async function getStats() {
  return request<unknown>("GET", "/stats");
}

export async function getEnv() {
  return request<unknown>("GET", "/env");
}

export async function getTools() {
  return request<unknown>("GET", "/tools");
}

export async function executeCommand(command: string) {
  return request<ApiResponse>("POST", "/command", command);
}

export async function executeFile(command: string) {
  return request<ApiResponse>("POST", "/file", command);
}

export async function executeFilepc(command: string) {
  return request<ApiResponse>("POST", "/filepc", command);
}

export async function executeCommandpc(command: string) {
  return request<ApiResponse>("POST", "/commandpc", command);
}

export async function executeProc(command: string) {
  return request<ApiResponse>("POST", "/proc", command);
}

export async function executeDocker(command: string) {
  return request<ApiResponse>("POST", "/docker", command);
}

export async function downloadFile(url: string) {
  return request<ApiResponse>("POST", "/getfile", url);
}

export { ApiError };
