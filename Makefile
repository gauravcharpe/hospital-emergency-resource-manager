# Hospital Emergency Resource Manager (HERM)
# Course: BCSE303L Operating Systems | Faculty: Dr. V. Ezhil Arasi | VIT
# Makefile for C Implementation

CC = clang
CFLAGS = -Wall -Wextra -O2 -Iinclude -pthread
SRC_COMMON = src/models.c src/sync.c src/banker.c src/deadlock.c src/scheduler.c src/ipc.c src/simulator.c src/benchmark.c

all: herm_cli herm_server

herm_cli: $(SRC_COMMON) src/main.c
	$(CC) $(CFLAGS) $(SRC_COMMON) src/main.c -o herm_cli

herm_server: $(SRC_COMMON) src/server.c
	$(CC) $(CFLAGS) $(SRC_COMMON) src/server.c -o herm_server

clean:
	rm -f herm_cli herm_server *.o

run: herm_cli
	./herm_cli

server: herm_server
	./herm_server

benchmark: herm_cli
	./herm_cli --benchmark

# One-time: lets the browser open http://hospital-emergency-resource-manager
# by pointing that name at this computer (127.0.0.1). Asks for your Mac password.
setup-host:
	@grep -q "hospital-emergency-resource-manager" /etc/hosts && echo "Already set up." || \
	(echo "127.0.0.1 hospital-emergency-resource-manager" | sudo tee -a /etc/hosts >/dev/null && \
	 sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder 2>/dev/null; echo "Done. Now run ./herm_server")

.PHONY: all clean run server benchmark setup-host
