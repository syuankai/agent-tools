import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useState, useEffect, useCallback } from "react";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { System } from "./pages/System";
import { Environment } from "./pages/Environment";
import { Security } from "./pages/Security";
import { Files } from "./pages/Files";
import { Terminal } from "./pages/Terminal";
import { DockerPage } from "./pages/Docker";
import { Processes } from "./pages/Processes";
import { ApiDocs } from "./pages/ApiDocs";
import { Downloads } from "./pages/Downloads";
import { getHealth } from "./api/client";
import "./App.css";

export default function App() {
  const [apiKey, setApiKey] = useState(() => sessionStorage.getItem("api_key") ?? "");
  const [apiOnline, setApiOnline] = useState(false);
  const [apiLoading, setApiLoading] = useState(true);
  const [version, setVersion] = useState("0.0.5");

  const checkHealth = useCallback(async () => {
    try {
      const res = (await getHealth()) as unknown as { data: { status: string; version: string }; status: number };
      if (res.status === 200 && res.data.status === "ok") {
        setApiOnline(true);
        setVersion(res.data.version);
      } else {
        setApiOnline(false);
      }
    } catch {
      setApiOnline(false);
    } finally {
      setApiLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          element={
            <Layout
              apiOnline={apiOnline}
              apiLoading={apiLoading}
              apiKey={apiKey}
              onApiKeyChange={setApiKey}
              version={version}
            />
          }
        >
          <Route path="/" element={<Dashboard onVersion={setVersion} />} />
          <Route path="/system" element={<System />} />
          <Route path="/environment" element={<Environment />} />
          <Route path="/security" element={<Security />} />
          <Route path="/files" element={<Files />} />
          <Route path="/terminal" element={<Terminal />} />
          <Route path="/docker" element={<DockerPage />} />
          <Route path="/processes" element={<Processes />} />
          <Route path="/api-docs" element={<ApiDocs />} />
          <Route path="/downloads" element={<Downloads />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
