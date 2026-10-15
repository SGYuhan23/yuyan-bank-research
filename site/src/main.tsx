import React from "react";
import { createRoot } from "react-dom/client";
import { ConfigProvider } from "antd";
import { HashRouter } from "react-router-dom";
import App from "./App";
import "./styles/app.css";
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "#187263",
          colorText: "#192b29",
          colorBorder: "#dce3e0",
          borderRadius: 8,
          fontFamily:
            'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          fontSize: 14,
          controlHeight: 38,
        },
        components: {
          Button: { primaryShadow: "none" },
          Card: { paddingLG: 24 },
        },
      }}
    >
      <HashRouter>
        <App />
      </HashRouter>
    </ConfigProvider>
  </React.StrictMode>,
);
