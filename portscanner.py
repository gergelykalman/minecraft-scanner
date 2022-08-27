import socket
import select
import struct
import random
import argparse

from datetime import datetime as dt, timedelta as td

READ_SIZE = 1024
MAX_BUF_SIZE = 4*1024
POLL_INTERVAL_MS = 100
VALID_PROTOCOL_HANDLERS = ["HTTP", "CONNECT", "BANNER_GRAB"]

# NOTE: POLLERR, POLLHUP and POLLNVAL will be set by the kernel in every case, we don't need to set them


# TODO: Use this as a base
class ProtocolHandler:
    pass


class HTTPHandler(ProtocolHandler):
    def __init__(self, s, ip, port):
        self.s = s
        self.state = None

        self.outbuf = bytearray(b'GET / HTTP/1.1\r\nHost: ' + ip.encode("ascii") + b'\r\nConnection: Close\r\n\r\n')
        self.outoff = 0
        self.inbuf  = bytearray()

    def initialise(self):
        self.state = 0
        return select.POLLOUT

    def timed_out(self):
        if self.get_response() is not None:
            return True

    def get_response(self):
        if self.state == 1 and len(self.inbuf) > 0:
            return self.inbuf

    def event(self, eventmask):
        if self.state == 0:
            if eventmask & select.POLLOUT:
                sent = self.s.send(self.outbuf[self.outoff:])
                self.outoff += sent
                if self.outoff == len(self.outbuf):
                    self.state = 1
                    return False, select.POLLIN
        elif self.state == 1:
            if eventmask & select.POLLIN:
                buf = self.s.recv(READ_SIZE)
                read = len(buf)
                self.inbuf += buf
                if read == 0 or len(buf) > MAX_BUF_SIZE:
                    return True, None
        else:
            raise RuntimeError("Invalid state: {}".format(self.state))

        # valid state but no matching event, or valid state and event but not final
        return False, None


class ConnectHandler(ProtocolHandler):
    def __init__(self, s, ip, port):
        self.s = s
        self.state = None

        self.inbuf = bytearray()
        self.inoff = 0

    def initialise(self):
        self.state = 0
        return select.POLLOUT

    def timed_out(self):
        return self.get_response()

    def get_response(self):
        return True if self.state == 1 else False

    def event(self, eventmask):
        if self.state == 0:
            if eventmask & select.POLLOUT:
                self.state = 1
                return True, None
        else:
            raise RuntimeError("Invalid state: {}".format(self.state))

        # valid state but no matching event, or valid state and event but not final
        return False, None


class BannerGrabHandler(ProtocolHandler):
    def __init__(self, s, ip, port):
        self.s = s
        self.state = None

        self.inbuf = bytearray()

    def initialise(self):
        self.state = 0
        return select.POLLOUT

    def timed_out(self):
        if self.get_response() is not None:
            return True

    def get_response(self):
        if self.state == 1 and len(self.inbuf) > 0:
            return self.inbuf

    def event(self, eventmask):
        if self.state == 0:
            if eventmask & select.POLLOUT:
                self.state = 1
                return False, select.POLLIN
        if self.state == 1:
            if eventmask & select.POLLIN:
                buf = self.s.recv(READ_SIZE)
                read = len(buf)
                self.inbuf += buf
                if read == 0 or len(buf) > MAX_BUF_SIZE:
                    return True, None
        else:
            raise RuntimeError("Invalid state: {}".format(self.state))

        # valid state but no matching event, or valid state and event but not final
        return False, None


class Connection:
    def __init__(self, ip, port, poll, protocol_class, timeout):
        self.ip = ip
        self.port = port
        self.poll = poll
        self.protocol_class = protocol_class
        self.timeout = timeout
        self.state = None
        self.start = None

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(False)

        self.protocol_handler = self.protocol_class(self.s, self.ip, self.port)

        self.start = dt.now()

        try:
            self.s.connect((self.ip, self.port))
        except BlockingIOError:
            pass

        eventmask = self.protocol_handler.initialise()
        self.poll.register(self.s, eventmask)

    def __cleanup(self):
        self.poll.unregister(self.s)
        self.s.close()

    @property
    def fd(self):
        return self.s.fileno()

    def timed_out(self, now):
        delta = (now-self.start).total_seconds()
        if delta > self.timeout:
            # print("[-] Timeout {}:{}, after: {:.2f}s".format(self.ip, self.port, delta))
            ret = self.protocol_handler.timed_out()
            # cleanup AFTER we call the protocol handler
            self.__cleanup()
            if ret is True:
                # return success if the protocol handler thinks it is
                return True
            else:
                # return failure (timeout)
                return False
        # return None if timeout is not reached
        return

    def get_response(self):
        return self.protocol_handler.get_response()

    def event(self, eventmask):
        """
        :return: True if done, False if not
        """

        # check for errors
        if eventmask & (select.POLLERR | select.POLLHUP | select.POLLNVAL):
            # TODO: handle error?
            self.__cleanup()
            # finished, error
            return False, True

        done, newmask = self.protocol_handler.event(eventmask)
        if not done:
            # set new mask if we need to
            if newmask is not None:
                self.poll.modify(self.s, newmask)
        else:
            # we are done
            self.__cleanup()
            # finished, error
            return True, False
        # finished, error
        return False, False


class Scanner:
    def __init__(self, total_to_scan, PORT, concurrency, protocol_handler, timeout, logfilename):
        self.total_to_scan = total_to_scan
        self.PORT = PORT
        self.concurrency = concurrency
        self.protocol_handler = protocol_handler
        self.timeout = timeout
        self.logfile = open(logfilename, "w", buffering=1024*1024)

        self.conns = {}
        # TODO: poll() is not available everywhere...
        self.poll = select.poll()

        self.submitted = 0
        self.successes = 0
        self.errors    = 0

    def genrandaddr(self):
        ipint = random.randint(0, 2**32-1)
        ip = socket.inet_ntoa(struct.pack('!L', ipint))
        return (ip, self.PORT)

    def success_handler(self, c):
        response = c.get_response()
        if type(response) in (bytearray, bytes):
            response = c.get_response()[:100]
        print("[+] Success {}:{} -> {}".format(c.ip, c.port, response), file=self.logfile)

    def handle_completion(self, fd):
        c = self.conns[fd]
        self.successes += 1
        self.success_handler(c)
        del self.conns[fd]

    def handle_error(self, fd):
        self.errors += 1
        del self.conns[fd]

    def scan(self):
        last_housekeeping = dt.now()
        generator_exhausted = False
        while len(self.conns) > 0 or not generator_exhausted:
            # spawn new workers if we need to
            while len(self.conns) < self.concurrency:
                if self.submitted >= self.total_to_scan:
                    generator_exhausted = True
                    break

                try:
                    ip, port = self.genrandaddr()
                except StopIteration:
                    generator_exhausted = True
                    break
                else:
                    try:
                        c = Connection(ip, port, self.poll, protocol_handler, timeout=self.timeout)
                    except OSError as exc:
                        if exc.errno != 101:
                            # 101 == "Network is unreachable", it's okay
                            raise
                        continue
                    else:
                        if self.conns.get(c.fd) is not None:
                            raise RuntimeError("{} fd is already in conn!".format(c.fd))
                        self.conns[c.fd] = c
                        self.submitted += 1

            for fd, event in self.poll.poll(POLL_INTERVAL_MS):
                finished, has_error = self.conns[fd].event(event)
                if finished or has_error:
                    if finished:
                        self.handle_completion(fd)
                    else:
                        self.handle_error(fd)

            now = dt.now()
            if (now - last_housekeeping).total_seconds() > 1:
                print("[?] STATUS conns: {}, submitted: {}, successes: {}, errors: {}".format(
                    len(self.conns), self.submitted, self.successes, self.errors)
                )

                # flush logfile every second, because the buffer is large
                self.logfile.flush()

                tmpconns = self.conns.copy()
                for fd, c in tmpconns.items():
                    # This returns True if the protocol handler thinks it was successful
                    ret = c.timed_out(now)
                    if ret is None:
                        # no timeout
                        continue

                    # if ret is not None, it is True for success, False for error
                    if ret:
                        self.handle_completion(fd)
                    else:
                        self.handle_error(fd)
                last_housekeeping = now


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True, help="Port to scan for")
    parser.add_argument("--total", type=int, required=True, help="Number of random IPs to scan")
    parser.add_argument("--concurrency", type=int, required=True, help="Number of simultaneous open connections")
    parser.add_argument("--timeout", type=int, required=True, help="Host timeout in seconds")
    parser.add_argument("--protocol-handler", type=str, choices=VALID_PROTOCOL_HANDLERS, required=True,
                        help="Protocol handler")
    parser.add_argument("--logfile", type=str, required=True, help="Path to log file, it will be truncated!")
    args = parser.parse_args()

    if args.protocol_handler == "HTTP":
        if args.port != 80:
            print("Port {} does not make sense with HTTP!".format(args.port))
            exit(1)
        protocol_handler = HTTPHandler
    elif args.protocol_handler == "CONNECT":
        protocol_handler = ConnectHandler
    elif args.protocol_handler == "BANNER_GRAB":
        protocol_handler = BannerGrabHandler
    else:
        raise ValueError("Invalid protocol handler: {}".format(args.protocol_handler))

    scanner = Scanner(args.total, args.port, args.concurrency, protocol_handler, args.timeout, args.logfile)
    scanner.scan()

