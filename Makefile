PLUGIN_NAME = mlpfrance
PARSER_FILE = mlpfrance.py
GLOBAL_DEPENCIES = Makefile $(PARSER_FILE) plugin.py
KODI_PLUGIN_PATH = ~/.kodi/addons

all: build/plugin.video.$(PLUGIN_NAME).zip build/plugin.audio.$(PLUGIN_NAME).zip

install: build/plugin.video.$(PLUGIN_NAME) build/plugin.audio.$(PLUGIN_NAME)
	rm -rf $(KODI_PLUGIN_PATH)/plugin.video.$(PLUGIN_NAME)
	rm -rf tmp/plugin.video.$(PLUGIN_NAME).install
	cp -rf build/plugin.video.$(PLUGIN_NAME) tmp/plugin.video.$(PLUGIN_NAME).install
	mv tmp/plugin.video.$(PLUGIN_NAME).install $(KODI_PLUGIN_PATH)/plugin.video.$(PLUGIN_NAME)
	rm -rf $(KODI_PLUGIN_PATH)/plugin.audio.$(PLUGIN_NAME)
	rm -rf tmp/plugin.audio.$(PLUGIN_NAME).install
	cp -rf build/plugin.audio.$(PLUGIN_NAME) tmp/plugin.audio.$(PLUGIN_NAME).install
	mv tmp/plugin.audio.$(PLUGIN_NAME).install $(KODI_PLUGIN_PATH)/plugin.audio.$(PLUGIN_NAME)

build/plugin.video.$(PLUGIN_NAME): $(GLOBAL_DEPENCIES) addon_video.xml plugin_param_video.py
	rm -rf tmp/plugin.video.$(PLUGIN_NAME)
	rm -rf build/plugin.video.$(PLUGIN_NAME)
	mkdir -p tmp/plugin.video.$(PLUGIN_NAME)
	cp ${PARSER_FILE} plugin.py tmp/plugin.video.$(PLUGIN_NAME)
	cp addon_video.xml tmp/plugin.video.$(PLUGIN_NAME)/addon.xml
	cp plugin_param_video.py tmp/plugin.video.$(PLUGIN_NAME)/plugin_param.py
	mv tmp/plugin.video.$(PLUGIN_NAME) build/plugin.video.$(PLUGIN_NAME)

build/plugin.video.$(PLUGIN_NAME).zip: build/plugin.video.$(PLUGIN_NAME)
	rm -f tmp/plugin.video.$(PLUGIN_NAME).zip
	cd build/; zip ../tmp/plugin.video.$(PLUGIN_NAME).zip -r plugin.video.$(PLUGIN_NAME)
	mkdir -p build
	mv tmp/plugin.video.$(PLUGIN_NAME).zip build/plugin.video.$(PLUGIN_NAME).zip

build/plugin.audio.$(PLUGIN_NAME): $(GLOBAL_DEPENCIES) addon_audio.xml plugin_param_audio.py
	rm -rf tmp/plugin.audio.$(PLUGIN_NAME)
	rm -rf build/plugin.audio.$(PLUGIN_NAME)
	mkdir -p tmp/plugin.audio.$(PLUGIN_NAME)
	cp ${PARSER_FILE} plugin.py tmp/plugin.audio.$(PLUGIN_NAME)
	cp addon_audio.xml tmp/plugin.audio.$(PLUGIN_NAME)/addon.xml
	cp plugin_param_audio.py tmp/plugin.audio.$(PLUGIN_NAME)/plugin_param.py
	mv tmp/plugin.audio.$(PLUGIN_NAME) build/plugin.audio.$(PLUGIN_NAME)

build/plugin.audio.$(PLUGIN_NAME).zip: build/plugin.audio.$(PLUGIN_NAME)
	rm -f tmp/plugin.audio.$(PLUGIN_NAME).zip
	cd build/; zip ../tmp/plugin.audio.$(PLUGIN_NAME).zip -r plugin.audio.$(PLUGIN_NAME)
	mkdir -p build
	mv tmp/plugin.audio.$(PLUGIN_NAME).zip build/plugin.audio.$(PLUGIN_NAME).zip

clean:
	rm -rf tmp build
