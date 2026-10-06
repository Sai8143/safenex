import { Platform } from "react-native";
import { getApiUrl } from "../config";

export async function sendAlert(photo, latitude, longitude, locationName = "Mobile GPS Reporter") {
  try {
    const baseUrl = getApiUrl();
    const formData = new FormData();

    if (Platform.OS === "web") {
      let blob;
      if (photo.blob instanceof Blob) {
        blob = photo.blob;
      } else if (photo.uri) {
        const res = await fetch(photo.uri);
        blob = await res.blob();
      } else if (photo.base64) {
        const res = await fetch(`data:image/jpeg;base64,${photo.base64}`);
        blob = await res.blob();
      }
      if (!blob) {
        throw new Error("Unable to extract image binary data on web browser.");
      }
      const file = new File([blob], "accident.jpg", { type: "image/jpeg" });
      formData.append("image", file);
    } else {
      formData.append("image", {
        uri: photo.uri,
        name: "accident.jpg",
        type: "image/jpeg",
      });
    }

    const safeLat = (latitude !== undefined && latitude !== null) ? latitude.toString() : "28.6139";
    const safeLng = (longitude !== undefined && longitude !== null) ? longitude.toString() : "77.2090";

    formData.append("latitude", safeLat);
    formData.append("longitude", safeLng);
    formData.append("location_name", locationName || "CCTV Camera Reporter");

    const response = await fetch(`${baseUrl}/alert`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let errorMsg = `Server error ${response.status}`;
      try {
        const errJson = await response.json();
        errorMsg = errJson.message || errJson.error || JSON.stringify(errJson);
      } catch (e) {
        errorMsg = await response.text();
      }
      throw new Error(errorMsg);
    }

    return await response.json();

  } catch (error) {
    console.error("❌ Failed to send alert:", error);
    throw error;
  }
}

export async function testServerConnection(url = null) {
  const baseUrl = url || getApiUrl();
  try {
    const response = await fetch(`${baseUrl}/health`, { method: "GET" });
    if (response.ok) {
      return await response.json();
    }
    return { health: "FAIL", error: `HTTP ${response.status}` };
  } catch (err) {
    return { health: "FAIL", error: err.message };
  }
}

export async function fetchAccidentHistory() {
  try {
    const baseUrl = getApiUrl();
    const response = await fetch(`${baseUrl}/api/accidents`, { method: "GET" });
    if (!response.ok) throw new Error("Failed to fetch accident logs");
    return await response.json();
  } catch (error) {
    console.error("❌ Failed to fetch history:", error);
    return [];
  }
}

export async function updateAccidentStatus(id, newStatus) {
  try {
    const baseUrl = getApiUrl();
    const response = await fetch(`${baseUrl}/api/accidents/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("❌ Failed to update accident status:", error);
    throw error;
  }
}
