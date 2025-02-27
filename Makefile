# Makefile

SERVER = 192.168.1.251
SERVER_DIR = /home/bk/py/code/newsau

upload:
	@echo "Deploying to server $(SERVER) at $(SERVER_DIR)..."
	@rsync -av --exclude-from='exclude.conf' . bk@$(SERVER):$(SERVER_DIR)