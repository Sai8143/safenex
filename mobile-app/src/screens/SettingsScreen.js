import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator
} from "react-native";
import { getApiUrl, setApiUrl } from "../config";
import { testServerConnection } from "../services/api";

export default function SettingsScreen() {
  const [urlInput, setUrlInput] = useState(getApiUrl());
  const [testing, setTesting] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  const handleSaveAndTest = async () => {
    try {
      setTesting(true);
      const updatedUrl = setApiUrl(urlInput);
      setUrlInput(updatedUrl);

      const res = await testServerConnection(updatedUrl);

      if (res && res.health === "OK") {
        setStatusMessage("✅ Successfully connected to AcciSense Server!");
        Alert.alert("Connection Success", "Backend server is online and reachable!");
      } else {
        setStatusMessage(`❌ Connection Failed: ${res.error || 'Server Unreachable'}`);
        Alert.alert("Connection Error", "Failed to connect to backend server. Make sure laptop and phone are on the same Wi-Fi!");
      }
    } catch (err) {
      setStatusMessage("❌ Error: " + err.message);
    } finally {
      setTesting(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Backend Server Setup</Text>
      <Text style={styles.subtitle}>
        Specify your FastAPI server host address to communicate with the AcciSense detection engine.
      </Text>

      <View style={styles.formGroup}>
        <Text style={styles.label}>Backend Host URL / Local IP</Text>
        <TextInput
          style={styles.input}
          value={urlInput}
          onChangeText={setUrlInput}
          placeholder="http://192.168.1.10:8000"
          placeholderTextColor="#6b7280"
          autoCapitalize="none"
          autoCorrect={false}
        />
      </View>

      <View style={styles.tipBox}>
        <Text style={styles.tipTitle}>💡 Connection Tips:</Text>
        <Text style={styles.tipText}>• Android Emulator: Use <Text style={styles.bold}>http://10.0.2.2:8000</Text></Text>
        <Text style={styles.tipText}>• Physical Mobile Device: Use your PC's Wi-Fi IP (e.g. <Text style={styles.bold}>http://192.168.x.x:8000</Text>)</Text>
        <Text style={styles.tipText}>• iOS Simulator: Use <Text style={styles.bold}>http://127.0.0.1:8000</Text></Text>
      </View>

      <TouchableOpacity
        style={styles.button}
        onPress={handleSaveAndTest}
        disabled={testing}
      >
        {testing ? (
          <ActivityIndicator color="#ffffff" />
        ) : (
          <Text style={styles.buttonText}>Save & Test Connection</Text>
        )}
      </TouchableOpacity>

      {statusMessage ? (
        <Text style={styles.statusText}>{statusMessage}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#090d16",
    paddingTop: 50,
    paddingHorizontal: 20
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
    color: "#ffffff",
    marginBottom: 6
  },
  subtitle: {
    fontSize: 13,
    color: "#9ca3af",
    marginBottom: 24,
    lineHeight: 18
  },
  formGroup: {
    marginBottom: 20
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    color: "#d1d5db",
    marginBottom: 8
  },
  input: {
    backgroundColor: "#131b2e",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.12)",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: "#ffffff",
    fontSize: 15
  },
  tipBox: {
    backgroundColor: "rgba(59, 130, 246, 0.1)",
    borderWidth: 1,
    borderColor: "rgba(59, 130, 246, 0.3)",
    borderRadius: 12,
    padding: 14,
    marginBottom: 24
  },
  tipTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: "#60a5fa",
    marginBottom: 6
  },
  tipText: {
    fontSize: 12,
    color: "#93c5fd",
    marginBottom: 4
  },
  bold: {
    fontWeight: "700",
    color: "#ffffff"
  },
  button: {
    backgroundColor: "#ef4444",
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center"
  },
  buttonText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700"
  },
  statusText: {
    marginTop: 16,
    textAlign: "center",
    fontSize: 14,
    color: "#e5e7eb",
    fontWeight: "600"
  }
});
