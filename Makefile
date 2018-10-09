export APP_ANDROID_ARCH=armeabi-v7a
export BUILDOZER_BIN_DIR=./bin-$(APP_ANDROID_ARCH)

HTTP_PORT=8001

export APP_VERSION=0.10
export APP_TITLE=alcan
export APP_PACKAGE_NAME=$(APP_TITLE)
ADB=adb

APK=$(BUILDOZER_BIN_DIR)/$(APP_PACKAGE_NAME)-$(APP_VERSION)-debug.apk

DOCKER_TAG=abu-usb-privs
DOCKER=docker run -it --rm --privileged \
				    -v $(PWD):/src \
				    -v /dev/bus/usb:/dev/bus/usb \
					-e APP_ANDROID_ARCH \
					-e APP_VERSION \
					-e APP_PACKAGE_NAME \
					-e BUILDOZER_BIN_DIR=/src/$(BUILDOZER_BIN_DIR) \
					mahomaho/buildozer-py3:$(DOCKER_TAG)

BDOZER_CMD=$(DOCKER) buildozer $(VERBOSE)

SRCS=$(wildcard *.py img/*.png *.kv data/*.txt)

debug:
	make $(APK)

serve:
	make $(APK)
	cd $(BUILDOZER_BIN_DIR) && python3 -m http.server $(HTTP_PORT)

install: debug
	$(ADB) install -r $(APK)

run:
	$(BDOZER_CMD) android deploy run

docker:
	$(DOCKER) /bin/bash


log:
	$(ADB) logcat | grep -C 5 python


$(APK): $(SRCS)
	$(BDOZER_CMD) android debug


# have no idea if it works with buildozer env
intel: 
	make APP_ANDROID_ARCH=x86 ADB=~/genymotion/tools/adb debug

irun:
	make APP_ANDROID_ARCH=x86 ADB=~/genymotion/tools/adb debug install log




