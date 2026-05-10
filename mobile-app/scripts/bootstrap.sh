#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a new iOS SwiftUI project from the template.
# Usage: bash bootstrap.sh "My App" "com.example.myapp" "/path/to/output"

APP_NAME="${1:?Usage: $0 <app-name> <bundle-id> <output-dir>}"
BUNDLE_ID="${2:?Usage: $0 <app-name> <bundle-id> <output-dir>}"
OUTPUT_DIR="${3:?Usage: $0 <app-name> <bundle-id> <output-dir>}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/../template"

if [ ! -d "$TEMPLATE_DIR" ]; then
  echo "Error: Template not found at $TEMPLATE_DIR" >&2
  exit 1
fi

if [ -d "$OUTPUT_DIR" ]; then
  echo "Error: Output directory already exists: $OUTPUT_DIR" >&2
  exit 1
fi

# Derive identifiers from app name
# "My App" -> "My_App" (for Swift identifiers)
SWIFT_NAME=$(echo "$APP_NAME" | sed 's/[^a-zA-Z0-9]/_/g')
# Ensure it starts with a letter (prefix with _ if it starts with a digit)
if [[ "$SWIFT_NAME" =~ ^[0-9] ]]; then
  SWIFT_NAME="_${SWIFT_NAME}"
fi
if [ -z "$SWIFT_NAME" ]; then
  echo "Error: App name '$APP_NAME' does not produce a valid Swift identifier" >&2
  exit 1
fi
# "App Name" is the template's original name
TEMPLATE_NAME="App Name"
TEMPLATE_SWIFT="App_Name"
TEMPLATE_BUNDLE_ID="com.example.App-Name"

echo "Creating project '$APP_NAME' at $OUTPUT_DIR..."
echo "  Bundle ID: $BUNDLE_ID"
echo "  Swift identifier: $SWIFT_NAME"

# Copy template
cp -R "$TEMPLATE_DIR" "$OUTPUT_DIR"

# Rename directories (order matters — deepest first)
# App Name/ -> $APP_NAME/
if [ -d "$OUTPUT_DIR/$TEMPLATE_NAME" ]; then
  mv "$OUTPUT_DIR/$TEMPLATE_NAME" "$OUTPUT_DIR/$APP_NAME"
fi
if [ -d "$OUTPUT_DIR/${TEMPLATE_NAME}Tests" ]; then
  mv "$OUTPUT_DIR/${TEMPLATE_NAME}Tests" "$OUTPUT_DIR/${APP_NAME}Tests"
fi
if [ -d "$OUTPUT_DIR/${TEMPLATE_NAME}UITests" ]; then
  mv "$OUTPUT_DIR/${TEMPLATE_NAME}UITests" "$OUTPUT_DIR/${APP_NAME}UITests"
fi
if [ -d "$OUTPUT_DIR/${TEMPLATE_NAME}.xcodeproj" ]; then
  mv "$OUTPUT_DIR/${TEMPLATE_NAME}.xcodeproj" "$OUTPUT_DIR/${APP_NAME}.xcodeproj"
fi

# Rename Swift files
if [ -f "$OUTPUT_DIR/$APP_NAME/${TEMPLATE_SWIFT}App.swift" ]; then
  mv "$OUTPUT_DIR/$APP_NAME/${TEMPLATE_SWIFT}App.swift" "$OUTPUT_DIR/$APP_NAME/${SWIFT_NAME}App.swift"
fi
if [ -f "$OUTPUT_DIR/${APP_NAME}Tests/${TEMPLATE_SWIFT}Tests.swift" ]; then
  mv "$OUTPUT_DIR/${APP_NAME}Tests/${TEMPLATE_SWIFT}Tests.swift" "$OUTPUT_DIR/${APP_NAME}Tests/${SWIFT_NAME}Tests.swift"
fi
if [ -f "$OUTPUT_DIR/${APP_NAME}UITests/${TEMPLATE_SWIFT}UITests.swift" ]; then
  mv "$OUTPUT_DIR/${APP_NAME}UITests/${TEMPLATE_SWIFT}UITests.swift" "$OUTPUT_DIR/${APP_NAME}UITests/${SWIFT_NAME}UITests.swift"
fi
if [ -f "$OUTPUT_DIR/${APP_NAME}UITests/${TEMPLATE_SWIFT}UITestsLaunchTests.swift" ]; then
  mv "$OUTPUT_DIR/${APP_NAME}UITests/${TEMPLATE_SWIFT}UITestsLaunchTests.swift" "$OUTPUT_DIR/${APP_NAME}UITests/${SWIFT_NAME}UITestsLaunchTests.swift"
fi

# Escape sed replacement special chars (& and |)
escape_sed_replacement() {
  printf '%s' "$1" | sed 's/[&|]/\\&/g'
}

SAFE_BUNDLE_ID=$(escape_sed_replacement "$BUNDLE_ID")
SAFE_SWIFT_NAME=$(escape_sed_replacement "$SWIFT_NAME")
SAFE_APP_NAME=$(escape_sed_replacement "$APP_NAME")

# Cross-platform sed in-place: macOS needs -i '', GNU/Linux needs -i
sedi() {
  if sed --version 2>/dev/null | grep -q GNU; then
    sed -i "$@"
  else
    sed -i '' "$@"
  fi
}

# Replace content in all text files
find "$OUTPUT_DIR" -type f \( -name "*.swift" -o -name "*.pbxproj" -o -name "*.plist" -o -name "*.xcworkspacedata" \) | while read -r file; do
  # Replace bundle ID first (most specific)
  sedi "s|$TEMPLATE_BUNDLE_ID|$SAFE_BUNDLE_ID|g" "$file"
  # Replace Swift identifiers
  sedi "s|$TEMPLATE_SWIFT|$SAFE_SWIFT_NAME|g" "$file"
  # Replace display name (in pbxproj, comments, etc.)
  sedi "s|$TEMPLATE_NAME|$SAFE_APP_NAME|g" "$file"
done

# Init git repo (skip commit if no git identity configured)
cd "$OUTPUT_DIR"
git init -q
git add -A
git commit -q -m "Initial project: $APP_NAME" 2>/dev/null || echo "  Note: git commit skipped (no git user.name/user.email configured)"

echo ""
echo "Project created at: $OUTPUT_DIR"
echo "  xcodeproj: $OUTPUT_DIR/$APP_NAME.xcodeproj"
echo "  scheme: $APP_NAME"
echo "  bundle ID: $BUNDLE_ID"
