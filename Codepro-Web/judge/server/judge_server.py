# Dedicated Judge Server (daemon listening for submission dispatches)


def start_server(port=9999):
    print(f"[JUDGE SERVER] Listening on port {port} for incoming compile & run tasks...")

if __name__ == '__main__':
    start_server()
