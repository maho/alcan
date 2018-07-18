export APP_P4A_SOURCE_DIR=~/workspace/p4a/
# export APP_ANDROID_JAVA_BUILD_TOOL=ant
export APP_ANDROID_ARCH=armeabi-v7a
export BUILDOZER_BUILD_DIR=.bdozer-$(APP_ANDROID_ARCH)
export BUILDOZER_BIN_DIR=./bin-$(APP_ANDROID_ARCH)

export APP_VERSION=0.7
export APP_TITLE=alcan
export APP_PACKAGE_NAME=$(APP_TITLE)
ADB=adb

APK=$(BUILDOZER_BIN_DIR)/$(APP_PACKAGE_NAME)-$(APP_VERSION)-debug.apk

SRCS=$(wildcard *.py img/*.png *.kv data/*.txt)

debug:
	make $(APK)

install: debug
	$(ADB) install -r $(APK)

log:
	$(ADB) logcat | grep -C 5 python

$(APK): $(SRCS)
	buildozer android debug

intel: 
	make APP_ANDROID_ARCH=x86 ADB=~/genymotion/tools/adb debug

irun:
	make APP_ANDROID_ARCH=x86 ADB=~/genymotion/tools/adb debug install log



