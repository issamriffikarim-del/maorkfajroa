[app]
title = Fa9ir
package.name = mykivyapp
package.domain = org.issam

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,ttf,otf,mp3,wav,txt

version = 0.1.0

# Ila katst3ml kivy
requirements = python3,kivy

# Main file
entrypoint = main.py

# Android options (optional but helpful)
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.archs = arm64-v8a,armeabi-v7a

# (optional) orientation
orientation = portrait
