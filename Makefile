ARCH=armeabi-v7a
BIN_DIR=./bin-$(ARCH)

HTTP_PORT=8001

VERSION=0.12
TITLE=alcan
SRCS=$(wildcard *.py img/*.png *.kv data/*.txt)
DOTDIST=$(PWD)/.dist


#
# general 
#
#

dist: $(DOTDIST)

$(DOTDIST): $(SRCS)
	rsync -rv --delete --delete-excluded \
		--exclude ".*" \
		--exclude "__pycache__" \
		--exclude "*.rst" \
		--exclude "*.xcf" \
		--exclude "doc" \
		--exclude "front-skan" \
		--exclude "docker-compose.yml" \
		--exclude "Makefile" --exclude "Pipfile" --exclude "*.sh" --exclude "TODO.*" --exclude "req*.txt" --exclude "tags" \
		$(PWD)/ $(DOTDIST)
	touch $(DOTDIST)

#
# android
#
#

DISTNAME=alcan
ADB=adb

APK=$(BUILDOZER_BIN_DIR)/$(DISTNAME)-$(VERSION)-debug.apk


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


$(APK): $(DOTDIST)
	docker-compose run p4a apk --sdk-dir=/opt/android/android-sdk \
		--ndk-dir=/opt/android/android-ndk --ndk-version=r17c \
		--private=/home/user/hostcwd/.dist --dist-name=alcan --android-api=27 \
		--debug --arch=armeabi-v7a --bootstrap=sdl2 \
		--requirements=python3,kivy,cymunk --copy-libs --package=maho.alcan \
		--version=$(VERSION) --name="Alcan"
	mkdir -p $(BIN_DIR)
	mv *.apk $(BIN_DIR)

# 
# IOS
#

KIVY_IOS_REPO=-b cymunk-py3 ssh://git@github.com/mahomahomaho/kivy-ios

xcode: .kivy-ios/alcan-ios
	open .kivy-ios/alcan-ios/alcan.xcodeproj

.kivy-ios/alcan-ios: .kivy-ios
	python3 -m virtualenv .kivy-ios/.ve
	.kivy-ios/.ve/bin/pip3 install cython==0.28.1

	bash -c "cd .kivy-ios && . .ve/bin/activate && \
			 pip3 install -r requirements.txt && \
			 ./toolchain.py build python3 && \
			./toolchain.py build kivy cymunk && \
			./toolchain.py create alcan $(DOTDIST) "

.kivy-ios:
	git clone $(KIVY_IOS_REPO) .kivy-ios


