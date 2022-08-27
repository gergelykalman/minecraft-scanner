# minecraft-scanner
A fast minecraft scanner written in Python

### Usage:
```
$ python3 scanner.py --help
usage: scanner.py [-h] --input-file INPUT_FILE [--output-format {text,json}] [--max-workers MAX_WORKERS]

options:
  -h, --help            show this help message and exit
  --input-file INPUT_FILE
                        Input file of ip:port pairs
  --output-format {text,json}
                        Output format
  --max-workers MAX_WORKERS
                        Number of workers to get minecraft statuses with
```

Output:
```bash
$ python3 scanner.py --input-file lists/ips.txt --max-workers 10
{"address": "[REDACTED]", "error": "Server did not respond with any information!", "description": "", "players": "", "ping": ""}
{"address": "[REDACTED]", "error": "", "description": "A Minecraft Server", "players": "0", "ping": "42.246"}
{"address": "[REDACTED]", "error": "", "description": "\u00a7f\u00a7d          \u00a7e\u2726  \u00a7x\u00a79\u00a7c\u00a70\u00a70\u00a7e\u00a76\u00a7lH\u00a7x\u00a7a\u00a7e\u00a70\u00a70\u00a7e\u00a73\u00a7lA\u00a7x\u00a7c\u00a71\u00a70\u00a70\u00a7e\u00a71\u00a7lL\u00a7x\u00a7d\u00a73\u00a70\u00a70\u00a7d\u00a7e\u00a7lE\u00a7x\u00a7e\u00a76\u00a70\u00a70\u00a7d\u00a7c\u00a7lA \u00a7x\u00a7e\u00a79\u00a77\u00a7c\u00a70\u00a77\u00a7lN\u00a7x\u00a7e\u00a78\u00a78\u00a79\u00a70\u00a75\u00a7le\u00a7x\u00a7e\u00a78\u00a79\u00a77\u00a70\u00a74\u00a7lt\u00a7x\u00a7e\u00a77\u00a7a\u00a75\u00a70\u00a73\u00a7lw\u00a7x\u00a7e\u00a77\u00a7b\u00a73\u00a70\u00a72\u00a7lo\u00a7x\u00a7e\u00a76\u00a7c\u00a71\u00a70\u00a71\u00a7lr\u00a7x\u00a7e\u00a76\u00a7c\u00a7f\u00a70\u00a70\u00a7lk  \u00a7a[1.17-1.19+]  \u00a7e\u2726                                   \u00a7x\u00a70\u00a70\u00a7a\u00a7e\u00a7e\u00a76\u00a7lO\u00a7x\u00a70\u00a70\u00a7b\u00a71\u00a7e\u00a76\u00a7ln\u00a7x\u00a70\u00a70\u00a7b\u00a75\u00a7e\u00a75\u00a7ll\u00a7x\u00a70\u00a70\u00a7b\u00a79\u00a7e\u00a76\u00a7ly\u00a7x\u00a70\u00a70\u00a7b\u00a7d\u00a7e\u00a76\u00a7l \u00a7x\u00a70\u00a70\u00a7c\u00a71\u00a7e\u00a76\u00a7lP\u00a7x\u00a70\u00a70\u00a7c\u00a74\u00a7e\u00a76\u00a7lr\u00a7x\u00a70\u00a70\u00a7c\u00a78\u00a7e\u00a76\u00a7le\u00a7x\u00a70\u00a70\u00a7c\u00a7c\u00a7e\u00a76\u00a7lm\u00a7x\u00a70\u00a70\u00a7d\u00a70\u00a7e\u00a76\u00a7li\u00a7x\u00a70\u00a70\u00a7d\u00a74\u00a7e\u00a76\u00a7lu\u00a7x\u00a70\u00a70\u00a7d\u00a78\u00a7e\u00a76\u00a7lm", "players": "4", "ping": "43.845"}
{"address": "[REDACTED]", "error": "", "description": "Craftserve.pl - wydajny hosting Minecraft!\nTestuj za darmo przez 24h!", "players": "0", "ping": "43.082"}
{"address": "[REDACTED]", "error": "", "description": "\"LiveOverflow Let's Play\"", "players": "13", "ping": "42.119"}
{"address": "[REDACTED]", "error": "[Errno 32] Broken pipe", "description": "", "players": "", "ping": ""}
{"address": "[REDACTED]", "error": "", "description": "\u00a7e\u00a7lBuild Server\n", "players": "0", "ping": "41.227"}
{"address": "[REDACTED]", "error": "", "description": "Nova Terraform Project", "players": "0", "ping": "42.076"}
{"address": "[REDACTED]", "error": "", "description": "A Minecraft Server", "players": "0", "ping": "41.603"}
{"address": "[REDACTED]", "error": "", "description": "\u00a74\u00a7lWartungsarbeiten\n", "players": "0", "ping": "41.373"}
...
```


### TODO
- Write a fast TCP connect scanner, so we don't have to rely on external tools to find target IPs
