from pathlib import Path
import pytest

import tame.core

from test_helpers import touch

def init_cache(tmpdir):
    """
    Given the temporary directory, returns a tuple
    that encodes the MetadataCache object and a Path-ified
    version of tmpdir, after creating the root.yaml file
    """
    tmpdir = Path(tmpdir.strpath)
    touch(tmpdir / 'root.yaml')
    cache = tame.core.MetadataCache(tmpdir / 'root.yaml')
    return (tmpdir, cache)

def test_simple_cache_loading(tmpdir):
    """
    Ensures that we can do simple single-file addition
    into the cache
    """
    tmpdir, cache = init_cache(tmpdir)

    with open(str(tmpdir / 'test.yaml'), 'w') as f:
        f.write("""
        type: foo
        name: bar
        user_key: user_val
        """)
    cache.add_metadata(Path('test.yaml'))

def test_uid_collision(tmpdir):
    """
    Ensures that the cache loader throws an error
    if two metadata files are loaded with the same type/uid pair.
    """
    tmpdir, cache = init_cache(tmpdir)

    with open(str(tmpdir / 'test1.yaml'), 'w') as f:
        f.write("""
        type: foo
        uid: bar
        userkey1: userval1
        """)
    with open(str(tmpdir / 'test2.yaml'), 'w') as f:
        f.write("""
        type: foo
        uid: bar
        userkey2: userval2
        """)
    cache.add_metadata(Path('test1.yaml'))
    with pytest.raises(tame.core.InconsistentMetadataError):
        cache.add_metadata(Path('test2.yaml'))

def test_non_uid_collisions(tmpdir):
    """
    Ensures that two files without a UID set do not conflict, as do
    two metadata files that have the same UID but different type.
    """
    tmpdir, cache = init_cache(tmpdir)

    with open(str(tmpdir / 'test1.yaml'), 'w') as f:
        f.write("""
        type: foo
        uid: test
        """)
    with open(str(tmpdir / 'test2.yaml'), 'w') as f:
        f.write("""
        type: bar
        uid: test
        """)
    with open(str(tmpdir / 'test3.yaml'), 'w') as f:
        f.write("""
        type: baz
        userkey1: userval1
        """)
    with open(str(tmpdir / 'test4.yaml'), 'w') as f:
        f.write("""
        type: baz
        userkey1: userval1
        """)
    cache.add_metadata(Path('test1.yaml'))
    cache.add_metadata(Path('test2.yaml'))
    cache.add_metadata(Path('test3.yaml'))
    cache.add_metadata(Path('test4.yaml'))

def test_name_noncollision(tmpdir):
    """
    Ensures that two files do not collide if they have the same name/type
    pair, as long as they either have blank UIDs or different UIDs
    """
    tmpdir, cache = init_cache(tmpdir)

    with open(str(tmpdir / 'test1.yaml'), 'w') as f:
        f.write("""
        type: foo
        name: bar
        """)
    with open(str(tmpdir / 'test2.yaml'), 'w') as f:
        f.write("""
        type: foo
        name: bar
        """)
    with open(str(tmpdir / 'test3.yaml'), 'w') as f:
        f.write("""
        type: foo
        name: bar
        uid: baz
        """)
    cache.add_metadata(Path('test1.yaml'))
    cache.add_metadata(Path('test2.yaml'))
    cache.add_metadata(Path('test3.yaml'))

def test_cache_tree(tmpdir):
    """
    Ensures that files in nested folders are properly
    added to the cache
    """
    tmpdir, cache = init_cache(tmpdir)

    (tmpdir / 'test' / 'test1').mkdir(parents=True)
    (tmpdir / 'test' / 'test2').mkdir(parents=True)

    with open(str(tmpdir / 'test' / 'foo1.yaml'), 'w') as f:
        f.write("""
        type: foo
        name: bar
        """)
    with open(str(tmpdir / 'test' / 'test1' / 'foo2.yaml'), 'w') as f:
        f.write("""
        type: bar
        name: baz
        """)
    with open(str(tmpdir / 'test' / 'test2' / 'foo3.yaml'), 'w') as f:
        f.write("""
        type: baz
        name: foo
        """)
    cache.add_metadata(Path('test') / 'foo1.yaml')
    cache.add_metadata(Path('test') / 'test1' / 'foo2.yaml')
    cache.add_metadata(Path('test') / 'test2' / 'foo3.yaml')

def test_cache_intial_load(tmpdir):
    """
    Ensures that YAML files that already exist in directories
    and subdirectories are loaded in the initial metadata walk,
    such that we can lookup entries with locators.
    """
    t = Path(tmpdir.strpath)
    (t / 'test' / 'test1').mkdir(parents=True)
    with open(str(t / 'toplevel.yaml'), 'w') as f:
        f.write("""
        type: foo
        name: bar
        """)

    with open(str(t / 'test' / 'level1.yaml'), 'w') as f:
        f.write("""
        type: foo
        uid: baz
        """)
    with open(str(t / 'test' / 'test1' / 'inner.yaml'), 'w') as f:
        f.write("""
        type: foobar
        name: bar
        uid: testing
        """)
    tmpdir, cache = init_cache(tmpdir)
    cache.lookup_by_keyval({'type': 'foo', 'name': 'bar'})
    cache.lookup_by_keyval({'type': 'foo', 'uid': 'baz'})
    cache.lookup_by_keyval({'type': 'foobar', 'uid': 'testing'})

def test_nonexistant_keyval(tmpdir):
    """
    Ensures that a lookup against a nonexistant locator pair
    raises a proper LookupError
    """
    tmpdir, cache = init_cache(tmpdir)
    with pytest.raises(tame.core.LookupError):
        cache.lookup_by_keyval({'type': 'foo', 'name': 'bar'})

def test_keyval_name_collision(tmpdir):
    """
    Ensures that naming collisions involving non-unique type/name
    pairs is caught.
    """
    tmpdir, cache = init_cache(tmpdir)
    with open(str(tmpdir / 'meta1.yaml'), 'w') as f:
        f.write("""
        type: foo
        name: bar
        uid: uid1
        """)
    with open(str(tmpdir / 'meta2.yaml'), 'w') as f:
        f.write("""
        type: foo
        name: bar
        uid: uid2
        """)
    with open(str(tmpdir / 'meta3.yaml'), 'w') as f:
        f.write("""
        type: foo
        name: baz
        uid: uid3
        """)
    
    for i in range(1, 4):
        cache.add_metadata(Path('meta{}.yaml'.format(i)))

    cache.lookup_by_keyval({'type': 'foo', 'uid': 'uid1'})
    cache.lookup_by_keyval({'type': 'foo', 'name': 'baz'})

    with pytest.raises(tame.core.LookupError):
        cache.lookup_by_keyval({'type': 'foo', 'name': 'bar'})
