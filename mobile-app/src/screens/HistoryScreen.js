import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  RefreshControl
} from "react-native";
import { fetchAccidentHistory } from "../services/api";

export default function HistoryScreen() {
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

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const getStatusStyle = (status) => {
    switch (status) {
      case "confirmed": return { bg: "#fee2e2", text: "#dc2626" };
      case "dispatched": return { bg: "#dbeafe", text: "#2563eb" };
      case "resolved": return { bg: "#d1fae5", text: "#059669" };
      default: return { bg: "#fef3c7", text: "#d97706" };
    }
  };

  const renderItem = ({ item }) => {
    const sStyle = getStatusStyle(item.status);
    const dateStr = new Date(item.timestamp).toLocaleString();

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={[styles.statusBadge, { backgroundColor: sStyle.bg }]}>
            <Text style={[styles.statusText, { color: sStyle.text }]}>
              {item.status.toUpperCase()}
            </Text>
          </View>
          <Text style={styles.dateText}>{dateStr}</Text>
        </View>

        <Text style={styles.locationText}>
          📍 {item.location_name || "GPS Location"} ({item.latitude?.toFixed(3)}, {item.longitude?.toFixed(3)})
        </Text>

        <Text style={styles.detailsText}>
          Type: {item.accident_type} | AI Confidence: {Math.round((item.confidence_score || 0.8) * 100)}%
        </Text>

        {item.details ? (
          <Text style={styles.extraText}>{item.details}</Text>
        ) : null}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#ef4444" />
        <Text style={{ marginTop: 10, color: "#9ca3af" }}>Loading incident history...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Incident Log & Status</Text>

      {accidents.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={styles.emptyText}>No emergency incidents logged yet.</Text>
        </View>
      ) : (
        <FlatList
          data={accidents}
          keyExtractor={(item) => item.id || Math.random().toString()}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#ef4444" />
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
    fontSize: 22,
    fontWeight: "800",
    color: "#ffffff",
    marginBottom: 16
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
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
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8
  },
  statusText: {
    fontSize: 11,
    fontWeight: "700"
  },
  dateText: {
    fontSize: 12,
    color: "#9ca3af"
  },
  locationText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#f3f4f6",
    marginBottom: 4
  },
  detailsText: {
    fontSize: 12,
    color: "#9ca3af"
  },
  extraText: {
    fontSize: 11,
    color: "#6b7280",
    marginTop: 6,
    fontStyle: "italic"
  }
});
