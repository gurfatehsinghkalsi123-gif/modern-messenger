[app]

# App name
title = Modern Messenger

# Package name (no spaces, lowercase)
package.name = modernmessenger

# Your domain (reverse format, can be anything)
package.domain = org.gurfateh

# Where your main.py is
source.dir = .

# Files to include
source.include_exts = py,png,jpg,json,kv

# App version
version = 0.1

# Python & Kivy
requirements = python3,kivy

# Screen orientation
orientation = portrait

# Run in windowed mode (0 = yes)
fullscreen = 0

# Permissions (VERY IMPORTANT for networking)
android.permissions = INTERNET

# Android build settings
android.api = 33
android.minapi = 21
android.ndk = 25b

# Target modern phones
android.archs = arm64-v8a

# Logcat output (helps debugging)
android.logcat_filters = *:S python:D

# Disable unnecessary features
android.private_storage = True

# EOF


