# Makefile

SERVER = 192.168.1.251
SERVER_DIR = /home/bk/py/code/newsau
SSH_PORT = 22

upload:
	@echo "Deploying to server $(SERVER) at $(SERVER_DIR)..."
	@rsync -av -e "ssh -p $(SSH_PORT)" --exclude-from='exclude.conf' . bk@$(SERVER):$(SERVER_DIR)