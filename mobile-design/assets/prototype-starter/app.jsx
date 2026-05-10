const { useEffect, useState } = React;
const {
  APP_DATA,
  BottomTabBar,
  DetailScreen,
  HomeScreen,
  IOSDevice,
  ProfileScreen,
  SavedScreen,
} = window;

const DEVICE_WIDTH = 402;
const DEVICE_HEIGHT = 874;

function useViewportScale(width, height) {
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const updateScale = () => {
      const availableWidth = window.innerWidth - 40;
      const availableHeight = window.innerHeight - 56;
      const nextScale = Math.min(availableWidth / width, availableHeight / height, 1);
      setScale(nextScale);
    };

    updateScale();
    window.addEventListener("resize", updateScale);
    return () => window.removeEventListener("resize", updateScale);
  }, [width, height]);

  return scale;
}

function MobileDesignApp() {
  const [activeTab, setActiveTab] = useState("home");
  const [selectedId, setSelectedId] = useState(null);
  const [savedIds, setSavedIds] = useState([APP_DATA.collections[0].id]);
  const scale = useViewportScale(DEVICE_WIDTH, DEVICE_HEIGHT);

  const selectedItem = APP_DATA.collections.find((item) => item.id === selectedId) || null;

  const toggleSaved = (itemId) => {
    setSavedIds((current) =>
      current.includes(itemId) ? current.filter((id) => id !== itemId) : [...current, itemId]
    );
  };

  let screen = null;
  if (selectedItem) {
    screen = (
      <DetailScreen
        item={selectedItem}
        saved={savedIds.includes(selectedItem.id)}
        onBack={() => setSelectedId(null)}
        onSave={toggleSaved}
      />
    );
  } else if (activeTab === "saved") {
    screen = <SavedScreen items={APP_DATA.collections} savedIds={savedIds} onOpen={setSelectedId} />;
  } else if (activeTab === "profile") {
    screen = <ProfileScreen />;
  } else {
    screen = (
      <HomeScreen
        items={APP_DATA.collections}
        savedIds={savedIds}
        onOpen={setSelectedId}
        onSave={toggleSaved}
        onTabChange={setActiveTab}
      />
    );
  }

  return (
    <div className="viewer-root">
      <div className="viewer-stage">
        <div
          className="viewer-device-wrap"
          style={{
            transform: `scale(${scale})`,
          }}
        >
          <IOSDevice width={DEVICE_WIDTH} height={DEVICE_HEIGHT} dark={true}>
            <div
              style={{
                height: "100%",
                position: "relative",
                background:
                  "radial-gradient(circle at top, rgba(255,192,103,0.08), transparent 28%), linear-gradient(180deg, #101012 0%, #09090b 100%)",
              }}
            >
              {screen}
              {!selectedItem ? (
                <BottomTabBar
                  tabs={APP_DATA.tabs}
                  activeTab={activeTab}
                  onTabChange={setActiveTab}
                />
              ) : null}
            </div>
          </IOSDevice>
        </div>
      </div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<MobileDesignApp />);
