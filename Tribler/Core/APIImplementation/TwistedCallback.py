import sys

from Tribler.dispersy.callback import Callback
from twisted.internet import reactor
from threading import Thread, RLock, Event
from twisted.internet.task import deferLater
from twisted.internet.threads import blockingCallFromThread
from types import GeneratorType
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList, \
    CancelledError
from time import time

class TwistedCallback(Callback):

    def __init__(self, name="Generic-Callback"):
        self._name = name
        self._exception = None
        self._exception_traceback = None
        self._exception_handlers = []

        self._id = 0

        self._thread = Thread(target=reactor.run, name=name, kwargs={'installSignalHandlers':0})
        self._thread.daemon = True

        self._stopping = False

        self._lock = RLock()
        self._task_lock = RLock()

        self._current_tasks = []

    def start(self, wait=True):
        self._thread.start()
        self._thread_ident = self._thread.ident

        return True

    def stop(self, timeout=10.0, exception=None):
        self._stopping = True

        def stop_generators(_):
            for g in gList:
                g.close()

        dList = []
        gList = []
        with self._task_lock:
            now = time()
            for _, scheduled, d, g in self._current_tasks:
                if g:
                    gList.append(g)

                elif scheduled < now:
                    dList.append(d)

                else:
                    d.cancel()

        d = DeferredList(dList)
        d.addCallback(stop_generators)

        if timeout:
            if self.is_current_thread:
                # logger.debug("using callback.stop from the same thread will not allow us to wait until the callback has finished")
                pass

            else:
                event = Event()
                def do_stop(_):
                    reactor.stop()
                    event.set()

                d.addCallback(do_stop)
                event.wait(timeout)
                return event.is_set()
        else:
            d.addBoth(lambda _: reactor.stop())

    def join(self, timeout=0.0):
        self._thread.join(None if timeout == 0.0 else timeout)
        return reactor.running

    @property
    def is_running(self):
        return reactor.running

    @property
    def is_finished(self):
        return not self.is_running

    def remove_deferred(self, d):
        with self._task_lock:
            for i, call in enumerate(self._current_tasks):
                if call[2] == d:
                    self._current_tasks.pop(i)
                    break

    def get_id_position(self, id_):
        with self._task_lock:
            for i, call in enumerate(self._current_tasks):
                if call[0] == id_:
                    return i

    def has_id_scheduled(self, id_):
        return self.get_id_position(id_) != None

    def handle_exception(self, failure):
        if failure.check(CancelledError) == None:
            try:
                failure.raiseException()

            except (SystemExit, KeyboardInterrupt, GeneratorExit) as exception:
                # logger.exception("fatal exception occurred [%s]", exception)
                self._call_exception_handlers(exception, True)

            except Exception, exception:
                self._call_exception_handlers(exception, False)

    def register(self, call, args=(), kargs=None, delay=0.0, priority=0, id_=u"", callback=None, callback_args=(), callback_kargs=None, include_id=False):
        with self._task_lock:
            if not id_:
                self._id += 1
                id_ = u"dispersy-#%d" % self._id

            if not self._stopping:
                d = deferLater(reactor, delay, self.wrapped_call, id_, call, args + (id_,) if include_id else args, kargs or {})
                self._current_tasks.append([id_, time() + delay, d, None])

                if callback:
                    d.addCallback(lambda *_: callback(*callback_args, **callback_kargs))
                d.addErrback(self.handle_exception)
                d.addBoth(lambda *_: self.remove_deferred(d))

            return id_

    def persistent_register(self, id_, call, args=(), kargs=None, delay=0.0, priority=0, callback=None, callback_args=(), callback_kargs=None, include_id=False):
        if not self.has_id_scheduled(id_):
            return self.register(call, args, kargs, delay, priority, id_, callback, callback_args, callback_kargs, include_id)

    def replace_register(self, id_, call, args=(), kargs=None, delay=0.0, priority=0, callback=None, callback_args=(), callback_kargs=None, include_id=False):
        with self._task_lock:
            self.unregister(id_)
            return self.register(call, args, kargs, delay, priority, id_, callback, callback_args, callback_kargs, include_id)

    def unregister(self, id_, cancel=True):
        with self._task_lock:
            cur_pos = self.get_id_position(id_)
            if cur_pos != None:
                call = self._current_tasks.pop(cur_pos)
                if cancel:
                    if call[3]:
                        call[3].close()
                    elif call[2]:
                        call[2].cancel()

    def call(self, call, args=(), kargs=None, priority=0, id_=u"", include_id=False, timeout=0.0, default=None):
        if not self._stopping:
            if self.is_current_thread:
                return self.wrapped_call(id_, call, args, kargs or {})

            def callback(result):
                container[0] = result
                event.set()

            def errback(failure):
                container[1] = failure
                event.set()

            event = Event()
            container = [default, None]

            d = deferLater(reactor, 0, self.wrapped_call, id_, call, args + (id_,) if include_id else args, kargs or {})
            d.addCallbacks(callback, errback)

            event.wait(None if timeout == 0.0 else timeout)
            if not event.is_set():
                print >> sys.stderr, "timeout %.2fs occurred during call to %s" % (timeout, call)

            if container[1]:
                container[1].raiseException()

            return container[0]

    @inlineCallbacks
    def wrapped_call(self, id_, call, args, kargs):
        result = call(*args, **kargs)

        if isinstance(result, GeneratorType):
            # we only received the generator, no actual call has been made to the
            # function yet, therefore we call it again immediately
            with self._lock:
                cur_pos = self.get_id_position(id_)
                if cur_pos != None:
                    self._current_tasks[cur_pos][3] = result
                else:
                    self._current_tasks.append([id_, 0, None, result])

            while True:
                try:
                    yield deferLater(reactor, result.next(), lambda : None)

                except StopIteration:
                    result = 0
                    break

        returnValue(result)
