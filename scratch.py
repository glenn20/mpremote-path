# %%
# pyright: reportUnusedExpression=false
from mpremote.transport_serial import SerialTransport

from src.mpremote_path import Board, Debug, RemotePath

RemotePath.board = Board(SerialTransport("/dev/ttyUSB0"))
board = RemotePath.board
board.debug = Debug.EXEC
p = RemotePath("main.py", board=board)
d = RemotePath("/", board=board)
dot = RemotePath(".")

print(repr(p))
(p.stat(), p.is_dir(), p.is_file())

# %%
p.cwd(), p.home()

# %%
print(list(d.iterdir()))
print(list(dot.iterdir()))

# %%
list(dot.glob("*.py"))

# %%
list(dot.rglob("*.py"))

# %%
p.read_bytes()
print(p.read_text())

# %%
p2 = RemotePath("crap.txt")
msg = b"Hello world\n"
p2.write_bytes(msg)
p2.stat()
msg2 = p2.read_bytes()
print(msg2)
assert msg2 == msg
p2.unlink()
"OK"

# %%
q = RemotePath("./lib/mpy")
q = q / "../.././main.py"
q, q.absolute(), q.absolute().resolve()

# %%
missing = RemotePath("missing.txt")
assert missing.exists() is False
missing.exists()

# %%
