import sys
import random
import concurrent.futures
import json
import argparse

from mcstatus import JavaServer


def get_mc_status(ip, port, timeout=3):
    ret = {
        "address": "{}:{}".format(ip, port),
        "error": "",
        "description": "",
        "players": "",
        "ping": "",
    }

    try:
        server = JavaServer.lookup("{}:{}".format(ip, port), timeout=timeout)
        status = server.status()
    except Exception as exc:
        ret["error"] = str(exc)
    else:
        ret["description"] = str(status.description)
        ret["players"] = str(status.players.online)
        ret["ping"] = str(status.latency)

    return ret


def scan_one(addresses, timeout):
    ret = []
    for ip, port in addresses:
        tmp = get_mc_status(ip, port, timeout)
        ret.append(tmp)
    return ret


def scan_many(generator, max_workers, max_spawns_per_iteration=5, scan_timeout=1):
    """
    :param generator: should return (ip, port) pairs
    """
    generator_exhausted = False
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = set()
        while not generator_exhausted or len(futures) > 0:
            spawned = 0
            while not generator_exhausted and len(futures) < max_workers and spawned < max_spawns_per_iteration:
                try:
                    value = next(generator)
                except StopIteration:
                    generator_exhausted = True
                    break
                else:
                    # NOTE: Currently we only send a worker a single IP
                    # TODO: Make each worker take N IPs to test, to speed up even further...
                    args = [[value], scan_timeout]
                    future = executor.submit(scan_one, *args)
                    futures.add(future)
                    spawned += 1

            # wait for results and collect statistics
            done, not_done = concurrent.futures.wait(futures, timeout=1, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                results = future.result()
                for result in results:
                    if type(result) is not dict:
                        raise TypeError("Invalid type in result: {}".format(type(result)))

                    yield result

            futures = not_done


def main(iplist, output_json=True, max_workers=10):
    ips = []
    with open(iplist, "r") as f:
        for line in f:
            address = line.strip()
            if len(address) == 0:
                continue

            port = 25565
            if ":" in address:
                ip, port = address.split(":")
            else:
                ip = address
            ips.append((ip, port))

    random.shuffle(ips)
    g = ((x[0], x[1]) for x in ips)
    for result in scan_many(g, max_workers=max_workers):
        if not output_json:
            if result["error"] is not None:
                print("[-] Failure:")
                print("\taddress: {}".format(result["address"]))
                print("\terror:   {}".format(result["error"]))
            else:
                print("[+] Success:")
                print("\taddress:    ", result["address"])
                print("\tdescription:", result["description"])
                print("\tplayers:    ", result["players"])
                print("\tping:       ", result["ping"])
        else:
            print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", type=str, required=True, help="Input file of ip:port pairs")
    parser.add_argument("--output-format", type=str, choices=["text", "json"], default="json", help="Output format")
    parser.add_argument("--max-workers", type=int, default=10, help="Number of workers to get minecraft statuses with")
    args = parser.parse_args()

    main(args.input_file, args.output_format, args.max_workers)
