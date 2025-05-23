# Description: This script is used to initialize a fake filesystem on the unix
# port. The posix filesystem is unmounted and replaced with a LFS RAM
# filesystem. This is used to run the micropython port as a mock of a serial
# attached filesystem.
import vfs


class RAMBlockDev:
    def __init__(self, block_size, num_blocks):
        self.block_size = block_size
        self.data = bytearray(block_size * num_blocks)

    def readblocks(self, block_num, buf, offset=0):
        addr = block_num * self.block_size + offset
        buf[:] = self.data[addr : addr + len(buf)]

    def writeblocks(self, block_num, buf, offset=None):
        if offset is None:
            # do erase, then write
            for i in range(len(buf) // self.block_size):
                self.ioctl(6, block_num + i)
            offset = 0
        addr = block_num * self.block_size + offset
        for i in range(len(buf)):
            self.data[addr + i] = buf[i]

    def ioctl(self, op, arg):
        if op == 4:  # block count
            return len(self.data) // self.block_size
        if op == 5:  # block size
            return self.block_size
        if op == 6:  # block erase
            return 0


bdev = RAMBlockDev(512, 100)
vfs.VfsLfs2.mkfs(bdev)
vfs.umount("/")
vfs.mount(bdev, "/")
