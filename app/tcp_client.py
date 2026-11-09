"""Cliente de demonstração de comunicação TCP."""
import socket


def main():
    with socket.create_connection(('127.0.0.1', 9099), timeout=4) as sock:
        sock.sendall(b'STATUS\n')
        print(sock.recv(4096).decode('utf-8').strip())


if __name__ == '__main__':
    main()
