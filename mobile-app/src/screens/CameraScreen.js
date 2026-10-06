import { CameraView, useCameraPermissions } from "expo-camera";
import * as Location from "expo-location";
import { useRef, useState, useEffect } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet
} from "react-native";
import { sendAlert } from "../services/api";
import { startImpactDetector, stopImpactDetector, simulateImpactEvent } from "../utils/impactDetector";

export default function CameraScreen() {
  const cameraRef = useRef(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [locationPermission, setLocationPermission] = useState(false);
  const [loading, setLoading] = useState(false);
  const [cctvActive, setCctvActive] = useState(true);
  const [coords, setCoords] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date().toISOString().replace("T", " ").substring(0, 19));

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toISOString().replace("T", " ").substring(0, 19));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchLaptopLocation = async () => {
    return new Promise(async (resolve) => {
      let lat = 17.498;
      let lng = 78.147;

      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status === "granted") {
          setLocationPermission(true);
          const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
          lat = loc.coords.latitude;
          lng = loc.coords.longitude;
          setCoords(loc.coords);
          return resolve({ lat, lng });
        }
      } catch (err) {
        console.warn("Expo location error:", err);
      }

      // Fallback to HTML5 browser navigator.geolocation for Laptop Chrome/Edge
      if (typeof navigator !== "undefined" && navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            lat = pos.coords.latitude;
            lng = pos.coords.longitude;
            setCoords({ latitude: lat, longitude: lng });
            resolve({ lat, lng });
          },
          (err) => {
            console.warn("Browser geolocation error:", err);
            resolve({ lat, lng });
          },
          { enableHighAccuracy: true, timeout: 6000 }
        );
      } else {
        resolve({ lat, lng });
      }
    });
  };

  useEffect(() => {
    fetchLaptopLocation();
  }, []);

  const handleCapture = async () => {
    try {
      setLoading(true);

      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.65,
        skipProcessing: true
      });

      // Get real laptop GPS location
      const { lat, lng } = await fetchLaptopLocation();

      const response = await sendAlert(photo, lat, lng, `Laptop Live GPS Surveillance (${lat.toFixed(4)}, ${lng.toFixed(4)})`);

      const isConfirmed = response.status === "confirmed" || response.status === "CONFIRMED";
      const statusUpper = (response.status || "NORMAL").toUpperCase();

      Alert.alert(
        isConfirmed ? "🚨 ACCIDENT CONFIRMED" : "ℹ️ CCTV FRAME ANALYZED",
        `${response.message || 'Frame analyzed'}\n\nConfidence Score: ${Math.round((response.confidence_score || 0.0) * 100)}%\nCCTV Status: ${statusUpper}`,
        [{ text: "OK" }]
      );

    } catch (error) {
      console.error(error);
      Alert.alert("Server Error", error.message || "Failed to connect to AcciSense Backend Server. Verify Backend Host IP in Settings.");
    } finally {
      setLoading(false);
    }
  };

  const toggleCCTVMonitoring = () => {
    if (!cctvActive) {
      setCctvActive(true);
      startImpactDetector(() => handleCapture());
      Alert.alert("CCTV AI Engine ON", "Continuous automated traffic monitoring enabled.");
    } else {
      setCctvActive(false);
      stopImpactDetector();
      Alert.alert("CCTV AI Engine OFF", "Automated monitoring paused.");
    }
  };

  if (!permission) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#ef4444" />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.permText}>Camera permission required for CCTV Traffic Stream.</Text>
        <TouchableOpacity style={styles.permBtn} onPress={requestPermission}>
          <Text style={styles.permBtnText}>Enable CCTV Camera Feed</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView ref={cameraRef} style={styles.camera}>

        {/* Top CCTV Surveillance Telemetry Header */}
        <View style={styles.cctvHeader}>
          <View style={styles.cctvTopRow}>
            <View style={styles.recBadge}>
              <View style={styles.recDot} />
              <Text style={styles.recText}>REC ● LIVE CCTV [CAM-01]</Text>
            </View>
            <Text style={styles.clockText}>{currentTime} UTC</Text>
          </View>

          <View style={styles.cctvMetaRow}>
            <Text style={styles.metaText}>
              📍 JUNCTION 14 ({coords ? `${coords.latitude.toFixed(3)}, ${coords.longitude.toFixed(3)}` : "17.498, 78.147"})
            </Text>
            <Text style={styles.metaText}>1080P | 30.0 FPS | 4.2 Mbps</Text>
          </View>
        </View>

        {/* CCTV Viewfinder Reticle & Target Brackets */}
        <View style={styles.viewfinderContainer}>
          <View style={styles.cornerBracketTopLeft} />
          <View style={styles.cornerBracketTopRight} />
          <View style={styles.cornerBracketBottomLeft} />
          <View style={styles.cornerBracketBottomRight} />

          <View style={styles.aiStatusPill}>
            <View style={[styles.statusDot, { backgroundColor: cctvActive ? "#10b981" : "#f59e0b" }]} />
            <Text style={styles.aiStatusText}>
              {cctvActive ? "AI VEHICLE TRACKING: ACTIVE" : "AI TRACKING: PAUSED"}
            </Text>
          </View>
        </View>

        {/* Bottom CCTV Control Panel */}
        <View style={styles.cctvControlPanel}>
          <TouchableOpacity
            style={[styles.toggleBtn, cctvActive && styles.toggleBtnActive]}
            onPress={toggleCCTVMonitoring}
          >
            <Text style={styles.btnLabelText}>
              {cctvActive ? "🟢 AI MONITORING ON" : "🔴 AI MONITORING OFF"}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.captureCctvBtn, loading && styles.disabledBtn]}
            onPress={handleCapture}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#ffffff" size="small" />
            ) : (
              <Text style={styles.captureBtnText}>📸 ANALYZE FRAME</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.simulateCrashBtn}
            onPress={() => simulateImpactEvent()}
          >
            <Text style={styles.simulateBtnText}>⚡ SIMULATE CRASH</Text>
          </TouchableOpacity>
        </View>

      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000"
  },
  camera: {
    flex: 1
  },
  centerContainer: {
    flex: 1,
    backgroundColor: "#090d16",
    justifyContent: "center",
    alignItems: "center",
    padding: 24
  },
  permText: {
    color: "#9ca3af",
    fontSize: 15,
    textAlign: "center",
    marginBottom: 20
  },
  permBtn: {
    backgroundColor: "#ef4444",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10
  },
  permBtnText: {
    color: "#fff",
    fontWeight: "700"
  },
  cctvHeader: {
    paddingTop: 45,
    paddingHorizontal: 16,
    paddingBottom: 12,
    backgroundColor: "rgba(9, 13, 22, 0.85)",
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255, 255, 255, 0.1)"
  },
  cctvTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4
  },
  recBadge: {
    flexDirection: "row",
    alignItems: "center"
  },
  recDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#ef4444",
    marginRight: 6
  },
  recText: {
    color: "#f87171",
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.5,
    fontFamily: "monospace"
  },
  clockText: {
    color: "#94a3b8",
    fontSize: 11,
    fontWeight: "600",
    fontFamily: "monospace"
  },
  cctvMetaRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  metaText: {
    color: "#cbd5e1",
    fontSize: 11,
    fontWeight: "500"
  },
  viewfinderContainer: {
    flex: 1,
    position: "relative",
    justifyContent: "center",
    alignItems: "center",
    margin: 20
  },
  cornerBracketTopLeft: {
    position: "absolute",
    top: 10,
    left: 10,
    width: 30,
    height: 30,
    borderTopWidth: 3,
    borderLeftWidth: 3,
    borderColor: "#ef4444"
  },
  cornerBracketTopRight: {
    position: "absolute",
    top: 10,
    right: 10,
    width: 30,
    height: 30,
    borderTopWidth: 3,
    borderRightWidth: 3,
    borderColor: "#ef4444"
  },
  cornerBracketBottomLeft: {
    position: "absolute",
    bottom: 10,
    left: 10,
    width: 30,
    height: 30,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
    borderColor: "#ef4444"
  },
  cornerBracketBottomRight: {
    position: "absolute",
    bottom: 10,
    right: 10,
    width: 30,
    height: 30,
    borderBottomWidth: 3,
    borderRightWidth: 3,
    borderColor: "#ef4444"
  },
  aiStatusPill: {
    backgroundColor: "rgba(15, 23, 42, 0.8)",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.15)"
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8
  },
  aiStatusText: {
    color: "#f3f4f6",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.5,
    fontFamily: "monospace"
  },
  cctvControlPanel: {
    backgroundColor: "rgba(9, 13, 22, 0.9)",
    paddingVertical: 14,
    paddingHorizontal: 16,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: "rgba(255, 255, 255, 0.1)"
  },
  toggleBtn: {
    backgroundColor: "rgba(255, 255, 255, 0.08)",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)"
  },
  toggleBtnActive: {
    backgroundColor: "rgba(16, 185, 129, 0.2)",
    borderColor: "rgba(16, 185, 129, 0.4)"
  },
  btnLabelText: {
    color: "#f3f4f6",
    fontSize: 11,
    fontWeight: "700"
  },
  captureCctvBtn: {
    backgroundColor: "#ef4444",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center"
  },
  captureBtnText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "800"
  },
  disabledBtn: {
    opacity: 0.5
  },
  simulateCrashBtn: {
    backgroundColor: "rgba(239, 68, 68, 0.2)",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#ef4444"
  },
  simulateBtnText: {
    color: "#f87171",
    fontSize: 11,
    fontWeight: "700"
  }
});
