# Makefile

SERVER = 8.217.116.214
SERVER_DIR = /home/sp/py/code/newsau
SSH_PORT = 7251

upload:
	@echo "Deploying to server $(SERVER) at $(SERVER_DIR)..."
	@rsync -av -e "ssh -p $(SSH_PORT)" --exclude-from='exclude.conf' . sp@$(SERVER):$(SERVER_DIR)