Basic example of using `aioworkers_redis`.

Install aioworkers-redis to your `Python` interpreter:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
aioworkers -c config.yaml -l info -g
```

This command will run single process with two workers.

Push message to queue to start workers communication:

```bash
redis-cli lpush queue:ping 'start'
```

Run two separate processes. Use groups to select different workers to process. 

```bash
aioworkers -c config.yaml -l info +g ping
aioworkers -c config.yaml -l info +g pong
```
