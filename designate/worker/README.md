# Worker Model Code

The general service looks like any other Designate RPC service. Available
RPC calls are defined in `rpcapi.py` and implemented in `service.py`. Where
this differs is that the `service.py` implementations generally spawn threads
with a directive to invoke some sort of "task".

# Tasks

Tasks are discrete units of work that are represented in the form
of *_callable_* python objects. They can optionally return a value to be
used in the caller.

For (abbreviated) example:
```python
class SendNotify(base.Task):
    """
    Send a NOTIFY packet for a zone to a target

    :return: Success/Failure delivering the notify (bool)
    """
    def __init__(self, executor, zone, target):
        super(SendNotify, self).__init__(executor)
        self.zone = zone
        self.target = target

    def __call__(self):
        host = self.target.options.get('host')
        port = int(self.target.options.get('port'))

        try:
            dnsutils.notify(self.zone.name, host, port=port)
            return True
        except Exception:
            return False
```

To invoke:

If you're ok executing it on the local thread: `SendNotify(executor, zone, target)()`
If you want to schedule it in it's own thread, allowing it to yield to others:
```python
self.executor.run(zonetasks.SendNotify(
    self.executor, zone, target
))
```

Most tasks are executed using the executor at the top-level, for example when
the worker gets a message to `create_zone`, it will say "pop a thread to create
this zone on the pool", which will eventually flow to "I need to create this
zone on N targets", which will result in a:
```python
results = self.executor.run([
    ZoneActionOnTarget(self.executor, self.context, self.zone, target)
    for target in self.pool.targets
])
```

You can find the tasks in `designate/worker/tasks`, most tasks inherit from a base
that gives basic access like other rpcapis, storage, etc.

So the one thread for doing the entire zone create will use N threads in the
pool to go and do that, and when they're finished, the task will be back down
to using one thread as it evaluates results. Then it will do something similar
when it needs to poll N nameservers.

# Execution in Threads

The core of how this works is using the
[Python ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor).
This is plugabble, someone could certainly add a different executor,
but it's a simple idea that lets you map callables (tasks) across threads.

Here's an example that shows how you can make multiple calls to a single
ThreadPoolExecutor from concurrent threads (similar to how tasks calling
subtasks would do it).

```python
import concurrent.futures

# Initialize 4 executors

# e is so that we can make two concurrent calls to another executor
e = concurrent.futures.ThreadPoolExecutor(2)

# e_one is the executor that shows that we can make multiple calls from
# different threads to one executor
e_one = concurrent.futures.ThreadPoolExecutor(2)

# e_two and e_three are just separate pools to be used to print numbers
e_two = concurrent.futures.ThreadPoolExecutor(5)
e_three = concurrent.futures.ThreadPoolExecutor(5)

def do(task):
    task()

def one():
    print '1'

def two():
    print '2'

def do_one(tup):
    """
    Call the callable len(tup[1]) times concurrently

    Since e_one only has two threads in it's pool, it will only be
    able to handle two concurrent "jobs"

    tup is (callable, list(list))

    If one were to pass in (func, [[1]]) the resulting function calls would be:
    func([1])

    If it was (func, [1, 2]) it would be
    func(1)
    func(2)
    """
    print 'mapping e_one for a list of len %d' % len(tup[1])
    e_one.map(tup[0], tup[1])

def do_a(alist):
    print 'using e_two to map a list of len %d using do()' % len(alist)
    e_two.map(do, alist)

def do_b(alist):
    print 'using e_three to map a list of len %d using do()' % len(alist)
    e_three.map(do, alist)

# init lists of five callables that will just print a number
ones = [one] * 5
twos = [two] * 5

# a list of tuples, len two that include a function to be mapped eventually, and a list of callables
ones_twos = [(do_a, [ones]), (do_b, [twos])]

# We call do_one twice concurrently on the two tuples
# This makes two concurrent calls to e_one.map, each of which make only
# _one_ call to another function that executes the lists of five callables
# in parallel.
# We do this so that we can see that two concurrent calls to e_one from
# different threads will work concurrently if there is enough room
# in the thread pool.
e.map(do_one, ones_twos)

# Example output:
# $ python threadexectest.py
# mapping e_one for a list of len 1
# mapping e_one for a list of len 1
#
# mapping e_two for a list of len 5
# mapping e_three for a list of len 5
# 1
#  2
# 2
#  1
# 2
# 1
#  2
# 1
#  2
# 1
```

# Metrics

I ran a few tests that did used the old code vs the new code. There are obviously
a ton of different variables here (number of apis/centrals, dns server used, database
setup, rabbit setup), but other tests that I've done in different random configurations
have shown similar results to these two, so I think it's a good representation of what
the differences are.

Pool Manager Test

- 8 Nameservers
- 12 `designate-pool-manager` processes
- 1 hour
- Testing actual DNS propagation

Results:
| Operation       | Number | Propagation Stats                             |
| --------------- | ------ | --------------------------------------------- |
| Creates/Imports | 5700   | Avg propagation 19s >99% propagation in 30min |
| Zone Deletes    | 4600   | Avg propagation 16s >99% propagation in 30min |
| Zone Updates    | 18057  | Avg propagation 384s ~90 propagation in 30min |

Propagation Graph: ![](http://i.imgur.com/g3kodip.png)
Notice the prop times are increasing as time went on, so a longer test would
almost certainly show even worse times.

Worker Test

- 8 Nameservers
- 12 `designate-worker` processes
- 1 hour
- Testing actual DNS propagation

Results:

| Operation       | Number | Propagation Stats                              |
| --------------- | ------ | ---------------------------------------------- |
| Creates/Imports | 6413   | Avg propagation 8s >99.99% propagation in 5min |
| Zone Deletes    | 2077   | Avg propagation 4s 100%    propagation in 5min |
| Zone Updates    | 23750  | Avg propagation 5s ~99.99% propagation in 5min |

Propagation Graph: ![](http://i.imgur.com/fM9J9l9.png)
