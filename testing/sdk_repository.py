'''
************************************************************************
FOR THE TIME BEING WHATEVER MODIFICATIONS ARE APPLIED TO THIS FILE
SHOULD ALSO BE APPLIED TO sdk_repository IN ANY OTHER PARTNER REPOS
************************************************************************
'''
import json
import logging
import os
import random
import string
from itertools import chain
from time import sleep
import sdk_cmd

log = logging.getLogger(__name__)

def flatmap(f, items):
    """
    lines = ["one,two", "three", "four,five"]
    f     = lambda s: s.split(",")

    >>> map(f, lines)
    [['one', 'two'], ['three'], ['four', 'five']]

    >>> flatmap(f, lines)
    ['one', 'two', 'three', 'four', 'five']
    """
    return chain.from_iterable(map(f, items))


def parse_stub_universe_url_string(stub_universe_url_string):
    """Handles newline- and comma-separated strings."""
    lines = stub_universe_url_string.split("\n")
    return list(filter(None, flatmap(lambda s: s.split(","), lines)))

def add_universe_repos():
    log.info('Adding universe repos')

    # prepare needed universe repositories
    stub_universe_urls = os.environ.get('STUB_UNIVERSE_URL', "")

    return add_stub_universe_urls(parse_stub_universe_url_string(stub_universe_urls))


def add_stub_universe_urls(stub_universe_urls: list) -> dict:
    stub_urls = {}

    if not stub_universe_urls:
        return stub_urls

    log.info('Adding stub URLs: {}'.format(stub_universe_urls))
    for idx, url in enumerate(stub_universe_urls):
        log.info('URL {}: {}'.format(idx, repr(url)))
        package_name = 'testpkg-'
        package_name += ''.join(random.choice(string.ascii_lowercase +
                                              string.digits) for _ in range(8))
        stub_urls[package_name] = url

    # clean up any duplicate repositories
    count = 5
    while count > 0:
        current_universes = sdk_cmd.run_cli('package repo list --json')
        try:
            json.loads(current_universes)
        except ValueError:
            sleep(5)
            count = count - 1
            continue
        break

    for repo in json.loads(current_universes)['repositories']:
        if repo['uri'] in stub_urls.values():
            log.info('Removing duplicate stub URL: {}'.format(repo['uri']))
            sdk_cmd.run_cli('package repo remove {}'.format(repo['name']))

    # add the needed universe repositories
    for name, url in stub_urls.items():
        log.info('Adding stub repo {} URL: {}'.format(name, url))

        count = 5
        while count > 0:
            rc, stdout, stderr = sdk_cmd.run_raw_cli('package repo add --index=0 {} {}'.format(name, url))
            if rc != 0 or stderr:
                count = count - 1
                log.info('retrying adding stub repo {} URL: {}'.format(name, url))
                continue
            else:
                break

        if rc != 0 or stderr:
            raise Exception(
                'Failed to add stub repo {} ({}): stdout=[{}], stderr=[{}]'.format(
                    name, url, stdout, stderr))

    log.info('Finished adding universe repos')

    return stub_urls


def remove_universe_repos(stub_urls):
    log.info('Removing universe repos')

    # clear out the added universe repositores at testing end
    for name, url in stub_urls.items():
        log.info('Removing stub URL: {}'.format(url))
        rc, stdout, stderr = sdk_cmd.run_raw_cli('package repo remove {}'.format(name))
        if rc != 0 or stderr:
            if stderr.endswith('is not present in the list'):
                # tried to remove something that wasn't there, move on.
                pass
            else:
                raise Exception('Failed to remove stub repo: stdout=[{}], stderr=[{}]'.format(stdout, stderr))

    log.info('Finished removing universe repos')


def universe_session():
    """Add the universe package repositories defined in $STUB_UNIVERSE_URL.

    This should generally be used as a fixture in a framework's conftest.py:

    @pytest.fixture(scope='session')
    def configure_universe():
        yield from sdk_repository.universe_session()
    """
    stub_urls = {}
    try:
        stub_urls = add_universe_repos()
        yield
    finally:
        remove_universe_repos(stub_urls)
