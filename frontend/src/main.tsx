import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { RecommendationProvider } from "./context/RecommendationContext";
import "./styles/global.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RecommendationProvider>
      <App />
    </RecommendationProvider>
  </React.StrictMode>
);
