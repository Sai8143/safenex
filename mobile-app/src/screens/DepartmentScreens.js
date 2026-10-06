import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Linking,
  RefreshControl
} from "react-native";
import { fetchAccidentHistory, updateAccidentStatus } from "../services/api";

export function HospitalScreen() {
  return <DepartmentAlertView deptType="hospital" deptTitle="🏥 Hospital ER & Trauma Center" badgeBg="#fee2e2" badgeColor="#dc2626" btnText="Confirm ER Trauma Team Ready" btnBg="#dc2626" icon="🏥" />;
}

export function PoliceScreen() {
  return <DepartmentAlertView deptType="police" deptTitle="🚓 Police Traffic Control Unit" badgeBg="#dbeafe" badgeColor="#2563eb" btnText="Dispatch Traffic Patrol Unit" btnBg="#2563eb" icon="🚓" />;
}

export function AmbulanceScreen() {
  return <DepartmentAlertView deptType="ambulance" deptTitle="🚑 Ambulance EMS Rescue Unit" badgeBg="#fef3c7" badgeColor="#d97706" btnText="Dispatch EMS Siren Ambulance" btnBg="#d97706" icon="🚑" />;
}

function DepartmentAlertView({ deptType, deptTitle, badgeBg, badgeColor, btnText, btnBg, icon }) {
  const [accidents, setAccidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const data = await fetchAccidentHistory();
      setAccidents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openGpsNavigation = (lat, lng) => {
    const url = `https://maps.google.com/?q=${lat},${lng}`;
    Linking.openURL(url);
  };

  const handleAction = async (id) => {
    try {
      let targetStatus = "DISPATCHED";
      if (deptType === "hospital") targetStatus = "HOSPITAL_NOTIFIED";
      else if (deptType === "police") targetStatus = "POLICE_NOTIFIED";
      else if (deptType === "ambulance") targetStatus = "AMBULANCE_EN_ROUTE";

      await updateAccidentStatus(id, targetStatus);
      await loadData();
    } catch (err) {
      console.warn("Status update error:", err);
    }
  };

  const renderItem = ({ item }) => {
    const dateStr = new Date(item.timestamp).toLocaleString();
    const statusUpper = (item.status || "CONFIRMED").toUpperCase();

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={[styles.deptBadge, { backgroundColor: badgeBg }]}>
            <Text style={[styles.deptBadgeText, { color: badgeColor }]}>
              {icon} {statusUpper}
            </Text>
          </View>
          <Text style={styles.dateText}>{dateStr}</Text>
        </View>

        <Text style={styles.locationText}>
          📍 {item.location_name || "Collision Location"}
        </Text>

        <TouchableOpacity onPress={() => openGpsNavigation(item.latitude, item.longitude)}>
          <Text style={styles.gpsText}>
            🌐 GPS: {Number(item.latitude)?.toFixed(5)}, {Number(item.longitude)?.toFixed(5)} (Tap to Open Maps)
          </Text>
        </TouchableOpacity>

        <View style={styles.metaRow}>
          <Text style={styles.metaText}>Type: {(item.accident_type || "PHOTO").toUpperCase()}</Text>
          <Text style={styles.metaText}>Confidence: {Math.round((item.confidence_score || 0.8) * 100)}%</Text>
        </View>

        <TouchableOpacity style={[styles.actionBtn, { backgroundColor: btnBg }]} onPress={() => handleAction(item.id)}>
          <Text style={styles.actionBtnText}>{btnText}</Text>
        </TouchableOpacity>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={badgeColor} />
        <Text style={{ marginTop: 10, color: "#9ca3af" }}>Connecting to {deptTitle}...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{deptTitle}</Text>

      {accidents.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={styles.emptyText}>No emergency dispatches currently active.</Text>
        </View>
      ) : (
        <FlatList
          data={accidents}
          keyExtractor={(item) => item.id || Math.random().toString()}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadData(); }} tintColor={badgeColor} />
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#090d16",
    paddingTop: 50,
    paddingHorizontal: 16
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: "#ffffff",
    marginBottom: 16
  },
  centerContainer: {
    flex: 1,
    justify.content: "center",
    alignItems: "center"
  },
  emptyText: {
    color: "#6b7280",
    fontSize: 15
  },
  list: {
    paddingBottom: 20
  },
  card: {
    backgroundColor: "#131b2e",
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.08)"
  },
  cardHeader: {
    flexDirection: "row",
    justify.content: "space-between",
    alignItems: "center",
    marginBottom: 8
  },
  deptBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8
  },
  deptBadgeText: {
    fontSize: 11,
    fontWeight: "800"
  },
  dateText: {
    fontSize: 11,
    color: "#9ca3af"
  },
  locationText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#ffffff",
    marginBottom: 4
  },
  gpsText: {
    fontSize: 12,
    color: "#60a5fa",
    fontWeight: "600",
    marginBottom: 8
  },
  metaRow: {
    flexDirection: "row",
    justify.content: "space-between",
    marginBottom: 10
  },
  metaText: {
    fontSize: 11,
    color: "#9ca3af"
  },
  actionBtn: {
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center",
    justify.content: "center"
  },
  actionBtnText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "800"
  }
});
