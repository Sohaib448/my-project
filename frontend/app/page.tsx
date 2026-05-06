"use client";

import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [result, setResult] = useState<string>("");
  const [confidence, setConfidence] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setResult("");
    setConfidence(null);
    setShowHeatmap(false);
  };

  const analyzeImage = async () => {
    if (!file) return alert("Upload an image first");

    setLoading(true);

    const formData = new FormData();
    formData.append("image", file);

    try {
      const res = await fetch("https://my-project-production-40cc.up.railway.app", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      setResult(data.prediction);
      setConfidence(data.confidence * 100);

      setShowHeatmap(data.prediction === "FAKE");
    } catch {
      alert("Server error");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview("");
    setResult("");
    setConfidence(null);
    setShowHeatmap(false);
  };

  return (
    <div style={styles.bg}>

      {/* FLOATING BACKGROUND ORBS */}
      <div style={styles.orb1}></div>
      <div style={styles.orb2}></div>

      {/* MAIN CARD */}
      <div style={styles.container}>

        <div style={styles.card}>

          {/* HEADER */}
          <div style={styles.header}>
            <div>
              <h1 style={styles.title}>Deepfake Detection AI</h1>
              <p style={styles.subtitle}>
                Upload an image and let AI detect manipulation in seconds
              </p>
            </div>
          </div>

          {/* UPLOAD AREA */}
          <label style={styles.uploadBox}>
            <input type="file" hidden onChange={handleFileChange} />
            <p style={{ opacity: 0.8 }}>
              Click or drop image here
            </p>
          </label>

          {/* IMAGE PREVIEW */}
          {preview && (
            <div style={styles.imageWrapper}>
              <img src={preview} style={styles.image} />

              {showHeatmap && <div style={styles.heatmap}></div>}
            </div>
          )}

          {/* ANALYZE BUTTON */}
          <button onClick={analyzeImage} style={styles.primaryBtn}>
            {loading ? "Analyzing AI Model..." : "Analyze Image"}
          </button>

          {/* LOADING ANIMATION */}
          {loading && <div style={styles.loader}></div>}

          {/* RESULT */}
          {result && (
            <div style={styles.resultBox}>

              <div
                style={{
                  ...styles.badge,
                  background:
                    result === "REAL"
                      ? "rgba(0,255,120,0.15)"
                      : "rgba(255,0,80,0.15)",
                }}
              >
                {result}
              </div>

              <p style={styles.conf}>
                Confidence: {confidence?.toFixed(2)}%
              </p>

              <button onClick={reset} style={styles.secondaryBtn}>
                Analyze Another Image
              </button>

            </div>
          )}

        </div>
      </div>
    </div>
  );
}

/* ===================== STYLES ===================== */

const styles: any = {
  bg: {
    minHeight: "100vh",
    overflow: "hidden",
    background: "radial-gradient(circle at top, #0f172a, #020617)",
    color: "white",
    fontFamily: "Inter, Arial",
  },

  orb1: {
    position: "absolute",
    width: "400px",
    height: "400px",
    background: "#2563eb",
    filter: "blur(140px)",
    opacity: 0.25,
    top: "-100px",
    left: "-100px",
  },

  orb2: {
    position: "absolute",
    width: "400px",
    height: "400px",
    background: "#7c3aed",
    filter: "blur(140px)",
    opacity: 0.25,
    bottom: "-120px",
    right: "-120px",
  },

  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minHeight: "100vh",
    position: "relative",
    zIndex: 2,
  },

  card: {
    width: "520px",
    padding: "30px",
    borderRadius: "20px",
    background: "rgba(255,255,255,0.06)",
    backdropFilter: "blur(20px)",
    border: "1px solid rgba(255,255,255,0.1)",
    boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
  },

  header: {
    marginBottom: "20px",
  },

  title: {
    fontSize: "22px",
    fontWeight: "bold",
  },

  subtitle: {
    fontSize: "13px",
    opacity: 0.7,
  },

  uploadBox: {
    display: "block",
    padding: "25px",
    borderRadius: "14px",
    border: "1px dashed rgba(255,255,255,0.2)",
    textAlign: "center",
    cursor: "pointer",
    marginTop: "20px",
    marginBottom: "20px",
    transition: "0.3s",
  },

  imageWrapper: {
    position: "relative",
  },

  image: {
    width: "100%",
    borderRadius: "14px",
  },

  heatmap: {
    position: "absolute",
    inset: 0,
    borderRadius: "14px",
    background:
      "radial-gradient(circle, rgba(255,0,0,0.4), transparent 60%)",
  },

  primaryBtn: {
    width: "100%",
    padding: "12px",
    borderRadius: "12px",
    border: "none",
    marginTop: "15px",
    background: "linear-gradient(90deg,#2563eb,#7c3aed)",
    color: "white",
    fontWeight: "bold",
    cursor: "pointer",
    transition: "0.3s",
  },

  loader: {
    marginTop: "15px",
    height: "4px",
    width: "100%",
    background:
      "linear-gradient(90deg,transparent,#2563eb,transparent)",
    animation: "loading 1.2s infinite",
  },

  resultBox: {
    marginTop: "20px",
    textAlign: "center",
  },

  badge: {
    padding: "10px 20px",
    borderRadius: "999px",
    display: "inline-block",
    fontWeight: "bold",
    marginBottom: "10px",
  },

  conf: {
    opacity: 0.8,
    fontSize: "14px",
  },

  secondaryBtn: {
    marginTop: "15px",
    padding: "10px 16px",
    borderRadius: "10px",
    border: "1px solid rgba(255,255,255,0.2)",
    background: "transparent",
    color: "white",
    cursor: "pointer",
  },
};