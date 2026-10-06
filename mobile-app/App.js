import React, { useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import CameraScreen from "./src/screens/CameraScreen";
import SettingsScreen from "./src/screens/SettingsScreen";
import { HospitalScreen, PoliceScreen, AmbulanceScreen } from "./src/screens/DepartmentScreens";

export default function App() {
  const [activeTab, setActiveTab] = useState("camera");

  return (
    <View style={styles.container}>
      <View style={styles.screenContainer}>
        {activeTab === "camera" && <CameraScreen />}
        {activeTab === "hospital" && <HospitalScreen />}
        {activeTab === "police" && <PoliceScreen />}
        {activeTab === "ambulance" && <AmbulanceScreen />}
        {activeTab === "settings" && <SettingsScreen />}
      </View>

      {/* Bottom Tab Bar */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tabItem, activeTab === "camera" && styles.tabActive]}
          onPress={() => setActiveTab("camera")}
        >
          <Text style={[styles.tabText, activeTab === "camera" && styles.tabActiveText]}>
            📹 CCTV
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabItem, activeTab === "hospital" && styles.tabActive]}
          onPress={() => setActiveTab("hospital")}
        >
          <Text style={[styles.tabText, activeTab === "hospital" && styles.tabActiveText]}>
            🏥 Hospital
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabItem, activeTab === "police" && styles.tabActive]}
          onPress={() => setActiveTab("police")}
        >
          <Text style={[styles.tabText, activeTab === "police" && styles.tabActiveText]}>
            🚓 Police
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabItem, activeTab === "ambulance" && styles.tabActive]}
          onPress={() => setActiveTab("ambulance")}
        >
          <Text style={[styles.tabText, activeTab === "ambulance" && styles.tabActiveText]}>
            🚑 Ambulance
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabItem, activeTab === "settings" && styles.tabActive]}
          onPress={() => setActiveTab("settings")}
        >
          <Text style={[styles.tabText, activeTab === "settings" && styles.tabActiveText]}>
            ⚙️ Setup
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#090d16"
  },
  screenContainer: {
    flex: 1
  },
  tabBar: {
    flexDirection: "row",
    backgroundColor: "#0f172a",
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.08)",
    paddingVertical: 10,
    paddingHorizontal: 8,
    justifyContent: "space-around"
  },
  tabItem: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20
  },
  tabActive: {
    backgroundColor: "rgba(239, 68, 68, 0.2)",
    borderWidth: 1,
    borderColor: "rgba(239, 68, 68, 0.4)"
  },
  tabText: {
    fontSize: 12,
    color: "#9ca3af",
    fontWeight: "600"
  },
  tabActiveText: {
    color: "#ef4444",
    fontWeight: "700"
  }
});

