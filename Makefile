# Makefile

SERVER = 8.217.116.214
SERVER_DIR = /home/bk/py/code/newsau
SSH_PORT = 7251

upload:
	@echo "Deploying to server $(SERVER) at $(SERVER_DIR)..."
	@rsync -av -e "ssh -p $(SSH_PORT)" --exclude-from='exclude.conf' . bk@$(SERVER):$(SERVER_DIR)