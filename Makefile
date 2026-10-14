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

.PHONY: all clean run server benchmark
