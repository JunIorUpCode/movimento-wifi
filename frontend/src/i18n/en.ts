// Translations EN — WiFiSense Local
export const en = {
  // Navigation
  nav: {
    dashboard:        "Dashboard",
    history:          "History",
    calibration:      "Calibration",
    statistics:       "Statistics",
    notifications:    "Notifications",
    zones:            "Zones",
    ml:               "ML Data",
    pushNotifications:"Push Notif.",
    replay:           "Replay",
    settings:         "Settings",
  },

  // Presence status
  presence: {
    PRESENCE_MOVING:       "Movement Detected",
    PRESENCE_STILL:        "Static Presence",
    NO_PRESENCE:           "No Presence",
    FALL_SUSPECTED:        "Fall Suspected",
    PROLONGED_INACTIVITY:  "Prolonged Inactivity",
    UNKNOWN:               "Unknown",
  },

  // Dashboard
  dashboard: {
    title:            "Main Dashboard",
    signal:           "Signal",
    confidence:       "Confidence",
    status:           "Status",
    lastEvent:        "Last Event",
    monitorActive:    "Monitor Active",
    monitorStopped:   "Monitor Stopped",
    startMonitor:     "Start Monitor",
    stopMonitor:      "Stop Monitor",
    noEvents:         "No events recorded.",
  },

  // Calibration
  calibration: {
    title:            "Calibration",
    start:            "Start Calibration",
    stop:             "Stop",
    progress:         "Progress",
    baseline:         "Baseline",
    profiles:         "Profiles",
    saveProfile:      "Save Profile",
    loadProfile:      "Load Profile",
    deleteProfile:    "Delete Profile",
    instructions:     "Keep the environment empty during calibration.",
    movementDetected: "Movement detected! Wait and try again.",
    success:          "Calibration completed successfully.",
  },

  // Alerts
  alerts: {
    fallDetected:     "⚠️ Fall detected!",
    inactivity:       "Prolonged inactivity detected.",
    connectionLost:   "Connection to server lost.",
    connectionOk:     "Connected to server.",
  },

  // Common
  common: {
    save:     "Save",
    cancel:   "Cancel",
    delete:   "Delete",
    edit:     "Edit",
    confirm:  "Confirm",
    loading:  "Loading...",
    error:    "Error",
    success:  "Success",
    back:     "Back",
    close:    "Close",
    yes:      "Yes",
    no:       "No",
  },
} as const;
