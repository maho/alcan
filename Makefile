ARCH=armeabi-v7a
BIN_DIR=./bin-$(ARCH)

HTTP_PORT=8001

VERSION=0.12
TITLE=alcan
DISTNAME=alcan
ADB=adb

APK=$(BUILDOZER_BIN_DIR)/$(DISTNAME)-$(VERSION)-debug.apk

SRCS=$(wildcard *.py img/*.png *.kv data/*.txt)

debug:
	make $(APK)

distsrc:
	rsync -rv --delete --delete-excluded \
		--exclude ".*" \
		--exclude "__pycache__" \
		--exclude "*.rst" \
		--exclude "*.xcf" \
		--exclude "doc" \
		--exclude "front-skan" \
		--exclude "docker-compose.yml" \
		--exclude "Makefile" --exclude "Pipfile" --exclude "*.sh" --exclude "TODO.*" --exclude "req*.txt" --exclude "tags" \
		$(PWD)/ $(PWD)/.dist/
	touch .dist


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
	docker-compose run p4a apk --sdk-dir=/opt/android/android-sdk \
		--ndk-dir=/opt/android/android-ndk --ndk-version=r17c \
		--private=/home/user/hostcwd/.dist --dist-name=alcan --android-api=27 \
		--debug --arch=armeabi-v7a --bootstrap=sdl2 \
		--requirements=python3,kivy,cymunk --copy-libs --package=maho.alcan \
		--version=$(VERSION) --name="Alcan"
	mkdir -p $(BIN_DIR)
	mv *.apk $(BIN_DIR)
