[app]
title = Cafe POS
package.name = cafepos
package.domain = org.cafe

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1

# Important: use Kivy 2.2.1 for Android stable builds
requirements = python3,kivy==2.2.1,kivymd,pillow

# Force kivymd to use AndroidX-compatible dependencies
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1

# App configuration
orientation = portrait
fullscreen = 0

# Permissions
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Android API & NDK
android.api = 33          # stable
android.minapi = 21       # minimum supported
android.ndk = 25b         # recommended for python-for-android

android.accept_sdk_license = True
android.archs = arm64-v8a

# Java/Kotlin compatibility for Buildozer
android.enable_androidx = True
android.allow_backup = True
android.compile_options = sourceCompatibility=1.8,targetCompatibility=1.8

# (optional but recommended)
# Increase memory for large KivyMD apps
p4a.branch = master
android.extra_args = --verbose

[buildozer]
log_level = 2
warn_on_root = 1
