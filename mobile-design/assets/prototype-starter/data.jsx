window.APP_NAME = "__APP_NAME__";
window.APP_SLUG = "__APP_SLUG__";

window.APP_DATA = {
  name: window.APP_NAME,
  slug: window.APP_SLUG,
  tabs: [
    { id: "home", label: "Home", icon: "home" },
    { id: "saved", label: "Saved", icon: "bookmark" },
    { id: "profile", label: "Profile", icon: "user" },
  ],
  collections: [
    {
      id: "north-star",
      title: "North Star Routine",
      subtitle: "Daily focus ritual",
      note: "A guided flow for planning your day without clutter.",
      eyebrow: "Featured",
      hue: 28,
      stats: "12 min",
      bullets: [
        "Capture the important task first.",
        "Decide what stays visible on the home surface.",
        "Keep the CTA strong and singular.",
      ],
    },
    {
      id: "sound-map",
      title: "Sound Map",
      subtitle: "Explore by mood",
      note: "Editorial browsing with calm hierarchy and generous spacing.",
      eyebrow: "New",
      hue: 198,
      stats: "9 scenes",
      bullets: [
        "Group cards by tone, not by raw metadata.",
        "Let typography drive the atmosphere.",
        "Reserve accent color for active controls.",
      ],
    },
    {
      id: "quiet-circle",
      title: "Quiet Circle",
      subtitle: "Shared reflection",
      note: "An intimate community space designed around rhythm and trust.",
      eyebrow: "Community",
      hue: 330,
      stats: "248 members",
      bullets: [
        "Support short loops and visible progress.",
        "Keep profile and status surfaces lightweight.",
        "Make the next action obvious.",
      ],
    },
  ],
  profileRows: [
    { title: "Appearance", detail: "Warm dark", icon: "linear-gradient(135deg, #ffb347, #ff7b5c)" },
    { title: "Notifications", detail: "Focused", icon: "linear-gradient(135deg, #7dd3fc, #3b82f6)" },
    { title: "Connected Apps", detail: "3", icon: "linear-gradient(135deg, #a78bfa, #6366f1)" },
  ],
};
