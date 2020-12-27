#!/usr/bin/python

#Jeannie Chiem
#'gnyorly@gmail.com'
#ID:504666652

import csv, sys

filename = sys.argv[1]

class Inode:
    def __init__(self, inum, lc):
        self.inum = inum
        self.lc = lc
        self.ref = set()
        self.ptr = set()

class Block:
    def __init__(self, bnum):
        self.bnum = bnum
        self.ref = set()

class CSVread:
    def __init__(self):
        self.numBlocks = 0
        self.numInodes = 0
        
        self.bBitmap = set()
        self.iBitmap = set()
        self.freeInodes = set()
        self.usedInodes = dict()
        self.freeBlocks = set()
        self.usedBlocks = dict()
        self.indBlocks = dict()
        self.directories = dict()


    def read_input(self, file):
        with open(file, 'r') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in readCSV:
                if row[0] == "SUPERBLOCK":
                    self.numBlocks = int(row[1])
                    self.numInodes = int(row[2])
                elif row[0] == "BFREE":
                    self.bBitmap.add(int(row[1]))
                elif row[0] == "IFREE":
                    self.iBitmap.add(int(row[1]))
    
        with open(file, 'r') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in readCSV:
                if row[0] == "INODE":
                    inum = int(row[1])
                    offset = int(row[10])
                    if row[2] == '0':
                        self.freeInodes.add(inum)
                    else:
                        self.usedInodes[inum] = Inode(inum, int(row[6]))
                    numBlocks = int(row[11])
                    mblock = min(12, numBlocks)
                    for i in range(0, mblock):
                        bnum = int(row[i + 11], 16)
                        self.blockCheck(bnum, inum, offset, numBlocks)
                        numBlocks -= 1
                    if numBlocks > 0:
                        bnum = int(row[12 + 11], 16)
                        numBlocks = self.singInd(bnum, inum, offset, numBlocks)
                    if numBlocks > 0:
                        bnum = int(row[13 + 11], 16)
                        numBlocks = self.dubInd(bnum, inum, offset, numBlocks)
                    if numBlocks > 0:
                        bnum = int(row[14 + 11], 16)
                        numBlocks = self.tripInd(bnum, inum, offset, numBlocks)
                elif row[0] == "DIRENT":
                    parent = int(row[1])
                    offset = int(row[2])
                    iref = int(row[3])
                    name = row[6]
                    self.inodeCheck(parent, name, iref)
                    if (offset == 12 and iref != parent) or parent == 2:
                        self.directories[inum] = parent
                    if offset == 0 and parent != iref:
                        self.dirlinkError(parent, name, iref, parent)
                elif row[0] == "INDIRECT":
                    inum = int(row[1])
                    indLevel = int(row[2])
                    indoffset = int(row[3])
                    indbnum = int(row[4])
                    bref = int(row[5])
                    temp = (indbnum, bref)
                    if indbnum not in self.indBlocks:
                        self.indBlocks[indbnum] = list()
                    self.indBlocks[indbnum].append(temp)

    def invalidBlock(self, bnum, inum, offset, lvl):
        err = "INVALID "
        if lvl == 1:
            err += "INDIRECT "
        elif lvl == 2:
            err += "DOUBLE INDIRECT "
        elif lvl == 3:
            err += "TRIPLE INDIRECT "
        err += "BLOCK {} IN NODE {} OFFSET {}".format(bnum, inum, offset)
        sys.stdout.write(err + '\n')

    def inodeCheck(self, dir, name, inum):
        if inum < 0 or inum >= self.numInodes:
            self.inodeError(dir, name, inum)
        else:
            if inum in self.freeInodes:
                self.dirAlloc(dir, name, inum)

    def blockCheck(self, bnum, inum, offset, lvl = -1):
        if bnum < 0 or bnum >= self.numBlocks:
            self.invalidBlock(bnum, inum, offset, lvl)
        else:
            if bnum not in self.usedBlocks:
                self.usedBlocks[bnum] = Block(bnum)
            self.usedBlocks[bnum].ref.add((bnum, inum, offset))

    def indCheck(self, bnum, inum, offset, numBlocks, lvl, func):
        self.blockCheck(bnum, inum, offset, lvl)
        numBlocks -= 1
        for i in self.indBlocks:
            if numBlocks == 0:
                return numBlocks
            numBlocks = func(bnum, inum, offset, numBlocks, lvl)
        return numBlocks

    def doSing(self, bnum, inum, offset, numBlocks, lvl):
        self.blockCheck(bnum, inum, offset, lvl)
        return numBlocks - 1

    def singInd(self, bnum, inum, offset, numBlocks, lvl = 1):
        return self.indCheck(bnum, inum, offset, numBlocks, lvl, self.doSing)

    def doDub(self, bnum, inum, offset, numBlocks, lvl):
        return self.singInd(bnum, inum, offset, numBlocks, lvl)

    def dubInd(self, bnum, inum, offset, numBlocks, lvl = 2):
        return self.indCheck(bnum, inum, offset, numBlocks, lvl, self.doDub)

    def doTrip(self, bnum, inum, offset, numBlocks, lvl):
        return self.dubInd(bnum, inum, offset, numBlocks, lvl)

    def tripInd(self, bnum, inum, offset, numBlocks, lvl = 3):
        return self.indCheck(bnum, inum, offset, numBlocks, lvl, self.doTrip)

    def unrefBlock(self, block):
        sys.stdout.write("UNREFERENCED BLOCK {}\n".format(block))

    def blockAlloc(self, block):
        sys.stdout.write("ALLOCATED BLOCK {} ON FREELIST\n".format(block))

    def dupBlock(self, bnum, inum, offset):
        sys.stdout.write("DUPLICATE BLOCK {} IN INODE {} AT OFFSET {}\n".format(bnum, inum, offset))

    def inodeAlloc(self, inum, opt):
        if opt == 0:
            sys.stdout.write("ALLOCATED INODE {} ON FREELIST\n".format(inum))
        if opt == 1:
            sys.stdout.write("UNALLOCAED INODE {} NOT ON FREELIST\n".format(inum))

    def linkcountError(self, inum, lc, correctlc):
        sys.stdout.write("INODE {} HAS {} LINKS BUT LINKCOUNT IS {}\n".format(inum, lc, correctlc))

    def dirAlloc(self, dir, name, inum):
        sys.stdout.write("DIRECTORY INODE {} NAME {} UNALLOCATED INODE {}\n".format(dir, name, inum))

    def inodeError(self, dir, name, inum):
        sys.stdout.write("DIRECTORY INODE {} NAME {} IVALID INODE {}\n".format(dir, name, inum))

    def dirlinkError(self, inum, name, link, clink):
        sys.stdout.write("DIRECTORY INODE {} NAME {} LINK TO INODE {} SHOULD BE {}\n".format(inum, name, link, clink))

    def check(self):
        for bnum in self.usedBlocks:
            Block = self.usedBlocks[bnum]
            lc = len(Block.ref)
            if lc > 1:
                for j in Block.ref:
                    self.dupBlock(j[0], j[1], j[2])
            elif lc < 1:
                self.unrefBlock(bnum)
            if bnum in self.freeBlocks:
                self.blockAlloc(bnum)
        for inum in self.freeInodes:
            if inum not in self.iBitmap:
                self.inodeAlloc(inum, 1)
        for inum in self.usedInodes:
            if inum in self.iBitmap:
                self.inodeAlloc(inum, 0)
            inod = self.usedInodes[inum]
            lc = len(inod.ref)
            if lc != inod.lc:
                self.linkcountError(inum, inod.lc, lc)

    
def main():
    csv = CSVread()
    csv.read_input(filename)
    csv.check()

if __name__ == "__main__":
    main()

