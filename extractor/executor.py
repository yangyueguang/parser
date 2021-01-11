import os
import io
import signal
import time
import uuid
import traceback
import multiprocessing
import multiprocessing.managers


class Work(object):
    def __init__(self, target, *args, **kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.id = uuid.uuid1().hex
        self.data = None
        self.error = None
        self.results = {}

    def run(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        data = None
        error = None
        try:
            data = self.target(*self.args, **self.kwargs)
        except:
            with io.StringIO() as fp:
                traceback.print_exc(file=fp)
                error = fp.getvalue()
        finally:
            self.results[self.id] = {
                'data': data,
                'error': error
            }

    def done(self):
        r = self.results.get(self.id)
        if not r:
            self.error = '异常退出'
        else:
            self.error = r['error']
            self.data = r['data']


class Executor(object):
    def __init__(self, method='fork'):
        self.ctx = multiprocessing.get_context(method)

    def get_start_method(self):
        return self.ctx.get_start_method()

    def execute(self, workers: list):
        def manager_initializer():
            signal.signal(signal.SIGINT, on_signal)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

        def on_signal(num):
            print(f'signal={num}, work process={os.getpid()}')

        m = multiprocessing.managers.SyncManager()
        m.start(initializer=manager_initializer)
        with m:
            self.do_execute(workers, self.ctx, m)

    def do_execute(self, workers, ctx, manager):
        results = manager.dict()
        processes = []
        for w in workers:
            w.results = results
            p = ctx.Process(target=w.run, daemon=True)
            p.start()
            processes.append(p)

        def kill_processes(timeout=3):
            for p in processes:
                if p.is_alive():
                    p.terminate()
            for p in processes:
                if p.is_alive():
                    p.join(timeout=timeout)
                    if p.is_alive():
                        try:
                            os.kill(p.pid, signal.SIGKILL)
                        except:
                            ...

        def has_alive():
            for p in processes:
                if p.is_alive():
                    return True
            return False

        try:
            while has_alive():
                time.sleep(0.1)
        finally:
            kill_processes()
        for w in workers:
            w.done()


if __name__ == '__main__':
    executor = Executor()
    works = []
    args = [1, 2, 3]
    kwargs = {
        # 'a': 'a',
        # 'b': 'b'
    }
    def do_something(f, c, a):
        time.sleep(10)
        print(f'hello{a} {f} {c}')
    for i in range(3):
        works.append(Work(do_something, *args, **kwargs))
    executor.execute(works)
