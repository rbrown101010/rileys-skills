const {
  APP_DATA,
  AvatarMark,
  BottomTabBar,
  CollectionCard,
  Eyebrow,
  GhostIconButton,
  HeroCard,
  Icons,
  IOSList,
  IOSListRow,
  Pill,
  PrimaryButton,
  ScreenShell,
  SectionTitle,
  TopBar,
} = window;

function HomeScreen({ items, savedIds, onOpen, onSave, onTabChange }) {
  const featured = items[0];
  return (
    <ScreenShell>
      <TopBar title={APP_DATA.name} subtitle="Mobile design starter" />

      <div style={{ display: "grid", gap: 12 }}>
        <div
          style={{
            fontSize: 15,
            lineHeight: "22px",
            color: "var(--text-secondary)",
            maxWidth: 290,
          }}
        >
          A local mobile prototype with a real phone canvas, reusable primitives,
          and a browser preview you can click through.
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Pill active>iPhone scale</Pill>
          <Pill>Local preview</Pill>
          <Pill onClick={() => onTabChange("saved")}>Saved items</Pill>
        </div>
      </div>

      <HeroCard
        item={featured}
        onOpen={onOpen}
        onSave={onSave}
        saved={savedIds.includes(featured.id)}
      />

      <div style={{ display: "grid", gap: 14 }}>
        <SectionTitle action={{ label: "View all", onClick: () => onTabChange("saved") }}>
          Collections
        </SectionTitle>
        <div style={{ display: "grid", gap: 12 }}>
          {items.slice(1).map((item) => (
            <CollectionCard
              key={item.id}
              item={item}
              onOpen={onOpen}
              onSave={onSave}
              saved={savedIds.includes(item.id)}
            />
          ))}
        </div>
      </div>
    </ScreenShell>
  );
}

function DetailScreen({ item, saved, onBack, onSave }) {
  return (
    <ScreenShell>
      <TopBar
        title={item.title}
        subtitle={item.eyebrow}
        onBack={onBack}
        right={
          <GhostIconButton
            onClick={() => onSave(item.id)}
            icon={<Icons.bookmarkSolid active={saved} />}
          />
        }
      />

      <div
        style={{
          background: "linear-gradient(180deg, rgba(255,255,255,0.085), rgba(255,255,255,0.035))",
          border: "0.5px solid rgba(255,255,255,0.08)",
          borderRadius: "var(--radius-panel)",
          padding: 20,
          display: "grid",
          gap: 18,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <AvatarMark label={item.title.charAt(0)} hue={item.hue} size={56} />
          <div style={{ display: "grid", gap: 4 }}>
            <div style={{ fontSize: 15, fontWeight: 600 }}>{item.subtitle}</div>
            <div style={{ fontSize: 13, color: "var(--text-tertiary)" }}>{item.stats}</div>
          </div>
        </div>

        <div style={{ fontSize: 15, lineHeight: "22px", color: "var(--text-secondary)" }}>
          {item.note}
        </div>

        <div style={{ display: "grid", gap: 12 }}>
          {item.bullets.map((bullet) => (
            <div
              key={bullet}
              style={{
                display: "grid",
                gridTemplateColumns: "18px 1fr",
                gap: 10,
                alignItems: "start",
                color: "var(--text-secondary)",
                fontSize: 14,
                lineHeight: "20px",
              }}
            >
              <div style={{ color: "var(--accent)", paddingTop: 1 }}>●</div>
              <div>{bullet}</div>
            </div>
          ))}
        </div>
      </div>

      <PrimaryButton onClick={() => onSave(item.id)}>
        {saved ? "Remove from saved" : "Save collection"}
      </PrimaryButton>
    </ScreenShell>
  );
}

function SavedScreen({ items, savedIds, onOpen }) {
  const savedItems = items.filter((item) => savedIds.includes(item.id));
  return (
    <ScreenShell>
      <TopBar title="Saved" subtitle="Your shortlist" />

      {savedItems.length ? (
        <div style={{ display: "grid", gap: 12 }}>
          {savedItems.map((item) => (
            <CollectionCard
              key={item.id}
              item={item}
              onOpen={onOpen}
              onSave={() => {}}
              saved={true}
            />
          ))}
        </div>
      ) : (
        <div
          style={{
            borderRadius: "var(--radius-card)",
            border: "0.5px solid var(--border)",
            background: "rgba(255,255,255,0.04)",
            padding: 20,
            color: "var(--text-secondary)",
            fontSize: 14,
            lineHeight: "21px",
          }}
        >
          Save a few items from Home to populate this screen. The starter keeps at
          least one screen-to-screen flow ready for fast iteration.
        </div>
      )}
    </ScreenShell>
  );
}

function ProfileScreen() {
  return (
    <ScreenShell>
      <TopBar title="Profile" subtitle="System settings" />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: 18,
          borderRadius: "var(--radius-card)",
          background: "rgba(255,255,255,0.04)",
          border: "0.5px solid var(--border)",
        }}
      >
        <AvatarMark label="R" size={56} hue={28} />
        <div style={{ display: "grid", gap: 4 }}>
          <div style={{ fontSize: 17, fontWeight: 600 }}>Riley Brown</div>
          <div style={{ fontSize: 13, color: "var(--text-tertiary)" }}>
            Reviewing the mobile system
          </div>
        </div>
      </div>

      <IOSList header="Preferences" dark={true}>
        {APP_DATA.profileRows.map((row, index) => (
          <IOSListRow
            key={row.title}
            title={row.title}
            detail={row.detail}
            icon={row.icon}
            isLast={index === APP_DATA.profileRows.length - 1}
            dark={true}
          />
        ))}
      </IOSList>
    </ScreenShell>
  );
}

Object.assign(window, {
  HomeScreen,
  DetailScreen,
  SavedScreen,
  ProfileScreen,
});
