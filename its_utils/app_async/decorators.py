# -*- coding: utf-8 -*-
import functools

from .put_task import put_task


def put_task_before_call(task_fn, *task_args, **task_kwargs):
    """
    @put_task_before_call(some_func, foo='bar')
    def my_fn():
        return some_action()

    equals to:

    def my_fn():
        put_task(some_func, foo='bar')
        return some_action()
    """
    def decorator(fn_to_decorate):
        @functools.wraps(fn_to_decorate)
        def decorated(*args, **kwargs):
            put_task(task_fn, *task_args, **task_kwargs)
            return fn_to_decorate(*args, **kwargs)
        return decorated
    return decorator


def put_task_after_call(task_fn, *task_args, **task_kwargs):
    """
    @put_task_after_call(some_func, foo='bar')
    def my_fn():
        return some_action()

    equals to:

    def my_fn():
        res = some_action()
        put_task(some_func, foo='bar')
        return res
    """
    def decorator(fn_to_decorate):
        @functools.wraps(fn_to_decorate)
        def decorated(*args, **kwargs):
            return_value = fn_to_decorate(*args, **kwargs)
            put_task(task_fn, *task_args, **task_kwargs)
            return return_value
        return decorated
    return decorator


def put_task_finally(task_fn, *task_args, **task_kwargs):
    """
    @put_task_finally(some_func, foo='bar')
    def my_fn():
        return some_action()

    equals to:

    def my_fn():
        try:
            res = some_action()
        finally:
            put_task(some_func, foo='bar')
        return res
    """
    def decorator(fn_to_decorate):
        @functools.wraps(fn_to_decorate)
        def decorated(*args, **kwargs):
            try:
                return_value = fn_to_decorate(*args, **kwargs)
            finally:
                put_task(task_fn, *task_args, **task_kwargs)
            return return_value
        return decorated
    return decorator
