def create_cacher():
    """Создать функцию с кэшем в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            cache[key] = value_func()

        return cache[key]

    cache_result.clear_cache = cache.clear

    return cache_result
