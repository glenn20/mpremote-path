# %%

from board import Board, Debug
from remote_path import RemotePath

RemotePath.board = Board("/dev/ttyUSB0")
RemotePath.board.debug = Debug.EXEC
p = RemotePath("main.py")
d = RemotePath("/")

print(repr(p))
(p.stat(), p.is_dir(), p.is_file())

# %%
print(list(d.iterdir()))

# %%
list(d.glob("*.py"))

# %%
list(d.rglob("*.py"))

# %%
p.is_absolute(), p.absolute(), d.is_absolute(), d.absolute()

# %%
p.resolve(), d.resolve()

# %%
p.read_bytes()
p.read_text()

# %%
p.cat()

# %%
p2 = RemotePath("crap.txt")
p2.write_bytes(b"Hello world\n")
p2.cat()
p2.stat()
p2

# %%
