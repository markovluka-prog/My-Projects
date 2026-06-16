#!/bin/bash
# Сборка Vocabulary Race в iOS (симулятор) и macOS (Mac Catalyst) .app
# Использование: ./build_apps.sh
#
# ВАЖНО (macOS): у .swiftpm-пакета executableTarget имеет path:".",
# поэтому derivedData нельзя держать ВНУТРИ пакета (иначе дубликаты ассетов).
# Строим в /tmp. Mac Catalyst под adhoc-подписью требует СНЯТИЯ App Sandbox,
# иначе процесс WebContent не стартует и экран чёрный.
set -e
cd "$(dirname "$0")"
PKG="$(pwd)"
SCHEME="Vocabulary Race"
DIST="$PKG/dist"

# Отключить debug (🐞-панель + ROUTE-калибровка) в указанном index.html:
#  - DEBUG_ENABLED = true → false
#  - вырезать HTML-блок между DEBUG:START и DEBUG:END
strip_debug() {
  local f="$1"
  [ -f "$f" ] || { echo "   ⚠ нет $f"; return; }
  /usr/bin/sed -i '' 's/const DEBUG_ENABLED = true; \/\* DEBUG:FLAG \*\//const DEBUG_ENABLED = false; \/* DEBUG:FLAG *\//' "$f"
  /usr/bin/perl -0pi -e 's/<!-- DEBUG:START.*?DEBUG:END -->//s' "$f"
}

echo "🧹 Чистка..."
rm -rf "$PKG/build" "$PKG/build-mac" /tmp/vr-ios /tmp/vr-mac
mkdir -p "$DIST"

echo "📱 Сборка iOS (симулятор)..."
xcodebuild -scheme "$SCHEME" -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath /tmp/vr-ios -configuration Release build >/dev/null
rm -rf "$DIST/Vocabulary Race (iOS Simulator).app"
cp -R "/tmp/vr-ios/Build/Products/Release-iphonesimulator/Vocabulary Race.app" \
  "$DIST/Vocabulary Race (iOS Simulator).app"
strip_debug "$DIST/Vocabulary Race (iOS Simulator).app/GameWeb/index.html"
echo "   ✓ dist/Vocabulary Race (iOS Simulator).app (debug убран)"

echo "🖥  Сборка macOS (Mac Catalyst, universal: arm64 + x86_64)..."
xcodebuild -scheme "$SCHEME" -destination 'platform=macOS,variant=Mac Catalyst' \
  -derivedDataPath /tmp/vr-mac -configuration Release \
  ARCHS="arm64 x86_64" ONLY_ACTIVE_ARCH=NO \
  CODE_SIGN_IDENTITY="-" CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=YES build >/dev/null
rm -rf "$DIST/Vocabulary Race (macOS).app"
cp -R "/tmp/vr-mac/Build/Products/Release-maccatalyst/Vocabulary Race.app" \
  "$DIST/Vocabulary Race (macOS).app"
# Путь к GameWeb в Mac Catalyst-бандле (Contents/Resources)
strip_debug "$DIST/Vocabulary Race (macOS).app/Contents/Resources/GameWeb/index.html"

echo "🔓 Снимаю App Sandbox (иначе WebContent не стартует под adhoc)..."
cat > /tmp/vr-no-sandbox.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>com.apple.security.app-sandbox</key><false/>
</dict></plist>
EOF
codesign --force --sign - --entitlements /tmp/vr-no-sandbox.plist --timestamp=none \
  "$DIST/Vocabulary Race (macOS).app"
echo "   ✓ dist/Vocabulary Race (macOS).app"

echo "✅ Готово. Приложения в: $DIST"
