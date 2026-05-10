const { IOSGlassPill } = window;

const Icons = {
  home: ({ active = false }) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path
        d="M3.5 8.75L10 3.75l6.5 5v7a1 1 0 0 1-1 1h-4.25v-4h-2.5v4H4.5a1 1 0 0 1-1-1v-7Z"
        stroke={active ? "var(--accent)" : "var(--text-tertiary)"}
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  ),
  bookmark: ({ active = false }) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path
        d="M5.25 3.75h9.5a1 1 0 0 1 1 1v11.5l-5.75-3-5.75 3V4.75a1 1 0 0 1 1-1Z"
        stroke={active ? "var(--accent)" : "var(--text-tertiary)"}
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  ),
  user: ({ active = false }) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle
        cx="10"
        cy="6.25"
        r="2.75"
        stroke={active ? "var(--accent)" : "var(--text-tertiary)"}
        strokeWidth="1.7"
      />
      <path
        d="M4.5 15.75c1.4-2.45 3.23-3.67 5.5-3.67 2.27 0 4.1 1.22 5.5 3.67"
        stroke={active ? "var(--accent)" : "var(--text-tertiary)"}
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  ),
  arrowLeft: () => (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path
        d="M10.75 4.25 6 9l4.75 4.75"
        stroke="var(--text-primary)"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),
  bookmarkSolid: ({ active = false }) => (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path
        d="M4.75 3.5h8.5a.75.75 0 0 1 .75.75V15L9 12.42 4 15V4.25a.75.75 0 0 1 .75-.75Z"
        fill={active ? "var(--accent)" : "rgba(255,255,255,0.18)"}
      />
    </svg>
  ),
};

function AvatarMark({ label, hue = 28, size = 44 }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: Math.round(size * 0.28),
        display: "grid",
        placeItems: "center",
        color: "white",
        background: `radial-gradient(circle at 30% 25%, hsl(${hue} 92% 72%), hsl(${hue} 58% 42%))`,
        boxShadow: "0 14px 24px rgba(0,0,0,0.24)",
        fontWeight: 700,
        letterSpacing: "0.02em",
      }}
    >
      <span style={{ fontSize: Math.max(14, size * 0.34) }}>{label}</span>
    </div>
  );
}

function Eyebrow({ children }) {
  return (
    <div
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: "var(--text-tertiary)",
      }}
    >
      {children}
    </div>
  );
}

function SectionTitle({ children, action }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
      }}
    >
      <h3
        style={{
          margin: 0,
          fontSize: 16,
          lineHeight: "20px",
          fontWeight: 600,
          color: "var(--text-primary)",
        }}
      >
        {children}
      </h3>
      {action ? (
        <button
          style={{
            background: "none",
            color: "var(--accent)",
            fontSize: 13,
            fontWeight: 600,
            padding: 0,
          }}
          onClick={action.onClick}
        >
          {action.label}
        </button>
      ) : null}
    </div>
  );
}

function Pill({ active = false, children, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        minHeight: 40,
        padding: "0 14px",
        borderRadius: "var(--radius-pill)",
        background: active ? "var(--accent-soft)" : "rgba(255,255,255,0.04)",
        color: active ? "var(--accent)" : "var(--text-secondary)",
        border: active ? "0.5px solid color-mix(in srgb, var(--accent) 45%, transparent)" : "0.5px solid var(--border)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 13,
        fontWeight: 600,
      }}
    >
      {children}
    </button>
  );
}

function PrimaryButton({ children, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        width: "100%",
        minHeight: 54,
        borderRadius: "var(--radius-pill)",
        background: "var(--accent)",
        color: "#111111",
        fontSize: 15,
        fontWeight: 700,
        boxShadow: "0 16px 36px color-mix(in srgb, var(--accent) 30%, transparent)",
      }}
    >
      {children}
    </button>
  );
}

function GhostIconButton({ icon, onClick }) {
  return (
    <button onClick={onClick} style={{ background: "none", padding: 0 }}>
      <IOSGlassPill
        dark={true}
        style={{
          width: 44,
          height: 44,
        }}
      >
        {icon}
      </IOSGlassPill>
    </button>
  );
}

function HeroCard({ item, onOpen, onSave, saved }) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpen(item.id)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen(item.id);
        }
      }}
      style={{
        width: "100%",
        textAlign: "left",
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.085), rgba(255,255,255,0.04))",
        border: "0.5px solid rgba(255,255,255,0.08)",
        borderRadius: "var(--radius-panel)",
        padding: 18,
        boxShadow: "var(--shadow-md)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 14,
        }}
      >
        <div style={{ display: "flex", gap: 12 }}>
          <AvatarMark label={item.title.charAt(0)} hue={item.hue} size={48} />
          <div style={{ display: "grid", gap: 6 }}>
            <Eyebrow>{item.eyebrow}</Eyebrow>
            <div
              style={{
                fontSize: 21,
                lineHeight: "24px",
                fontWeight: 600,
                color: "var(--text-primary)",
              }}
            >
              {item.title}
            </div>
            <div style={{ fontSize: 14, lineHeight: "20px", color: "var(--text-secondary)" }}>
              {item.subtitle}
            </div>
          </div>
        </div>
        <GhostIconButton
          onClick={(event) => {
            event.stopPropagation();
            onSave(item.id);
          }}
          icon={<Icons.bookmarkSolid active={saved} />}
        />
      </div>
      <p
        style={{
          margin: "18px 0 0",
          fontSize: 14,
          lineHeight: "21px",
          color: "var(--text-secondary)",
        }}
      >
        {item.note}
      </p>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        marginTop: 16,
        }}
      >
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-tertiary)" }}>
          {item.stats}
        </div>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--accent)" }}>Open</div>
      </div>
    </div>
  );
}

function CollectionCard({ item, onOpen, onSave, saved }) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpen(item.id)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen(item.id);
        }
      }}
      style={{
        width: "100%",
        textAlign: "left",
        background: "rgba(255,255,255,0.04)",
        border: "0.5px solid var(--border)",
        borderRadius: "var(--radius-card)",
        padding: "16px 16px 18px",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <AvatarMark label={item.title.charAt(0)} hue={item.hue} />
          <div>
            <div style={{ color: "var(--text-primary)", fontSize: 15, fontWeight: 600 }}>
              {item.title}
            </div>
            <div style={{ color: "var(--text-tertiary)", fontSize: 13, marginTop: 4 }}>
              {item.subtitle}
            </div>
          </div>
        </div>
        <button
          onClick={(event) => {
            event.stopPropagation();
            onSave(item.id);
          }}
          style={{ background: "none", padding: 0 }}
        >
          <Icons.bookmarkSolid active={saved} />
        </button>
      </div>
      <div
        style={{
          marginTop: 14,
          fontSize: 14,
          lineHeight: "20px",
          color: "var(--text-secondary)",
        }}
      >
        {item.note}
      </div>
    </div>
  );
}

function ScreenShell({ children }) {
  return (
    <div
      className="fade-up"
      style={{
        height: "100%",
        overflow: "auto",
        padding: "64px 20px 122px",
        display: "grid",
        alignContent: "start",
        gap: 20,
        scrollbarWidth: "none",
      }}
    >
      {children}
    </div>
  );
}

function TopBar({ title, subtitle, onBack, right }) {
  return (
    <div style={{ display: "grid", gap: 14 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
        }}
      >
        {onBack ? <GhostIconButton onClick={onBack} icon={<Icons.arrowLeft />} /> : <div />}
        {right || <div />}
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        {subtitle ? <Eyebrow>{subtitle}</Eyebrow> : null}
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 34,
            lineHeight: "36px",
            color: "var(--text-primary)",
            letterSpacing: "-0.02em",
          }}
        >
          {title}
        </div>
      </div>
    </div>
  );
}

function BottomTabBar({ tabs, activeTab, onTabChange }) {
  return (
    <div
      style={{
        position: "absolute",
        left: 16,
        right: 16,
        bottom: 16,
        padding: 8,
        borderRadius: 28,
        background: "rgba(18,18,20,0.86)",
        backdropFilter: "blur(18px) saturate(140%)",
        WebkitBackdropFilter: "blur(18px) saturate(140%)",
        border: "0.5px solid rgba(255,255,255,0.08)",
        boxShadow: "0 18px 30px rgba(0,0,0,0.24)",
        display: "grid",
        gridTemplateColumns: `repeat(${tabs.length}, minmax(0, 1fr))`,
        gap: 8,
      }}
    >
      {tabs.map((tab) => {
        const active = tab.id === activeTab;
        const Icon = Icons[tab.icon];
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            style={{
              minHeight: 54,
              borderRadius: 22,
              display: "grid",
              placeItems: "center",
              gap: 4,
              background: active ? "rgba(255,255,255,0.05)" : "transparent",
            }}
          >
            <Icon active={active} />
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: active ? "var(--accent)" : "var(--text-tertiary)",
              }}
            >
              {tab.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

Object.assign(window, {
  Icons,
  AvatarMark,
  Eyebrow,
  SectionTitle,
  Pill,
  PrimaryButton,
  GhostIconButton,
  HeroCard,
  CollectionCard,
  ScreenShell,
  TopBar,
  BottomTabBar,
});
