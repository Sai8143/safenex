/**
 * Impact / Crash Sensor Simulator & Motion Analyzer
 */

let isMonitoring = false;
let onImpactCallback = null;

export function startImpactDetector(onImpactTrigger) {
  isMonitoring = true;
  onImpactCallback = onImpactTrigger;
  console.log("⚡ Auto Impact Sensor activated");
}

export function stopImpactDetector() {
  isMonitoring = false;
  onImpactCallback = null;
  console.log("🛑 Impact Sensor deactivated");
}

export function simulateImpactEvent() {
  if (onImpactCallback) {
    console.log("🚨 Crash Impact Detected! Triggering Emergency Capture.");
    onImpactCallback();
  }
}
