
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdbool.h>

#include <sys/stat.h>
#include <sys/param.h>
#include <sys/types.h>
#include <inttypes.h>
#include <math.h>

#define	EXT2_NDIR_BLOCKS		12
#define	EXT2_IND_BLOCK			EXT2_NDIR_BLOCKS
#define	EXT2_DIND_BLOCK			(EXT2_IND_BLOCK + 1)
#define	EXT2_TIND_BLOCK			(EXT2_DIND_BLOCK + 1)
#define	EXT2_N_BLOCKS			(EXT2_TIND_BLOCK + 1)

typedef __uint32_t	__u32;
typedef __uint16_t	__u16;
typedef unsigned char	__u8;
typedef __int32_t	__s32;
typedef __int16_t	__s16;

FILE *superb_fd;
FILE *group_fd;
FILE *bit_fd;
FILE *inode_fd;
FILE *dir_fd;
FILE *indir_fd;
int disk_fd;

struct ext2_inode {

	__u16	i_mode;		/* File mode */
	__u16	i_uid;		/* Owner Uid */
	__u32	i_size;		/* Size in bytes */
	__u32	i_atime;	/* Access time */
	__u32	i_ctime;	/* Creation time */
	__u32	i_mtime;	/* Modification time */
	__u32	i_dtime;	/* Deletion Time */
	__u16	i_gid;		/* Group Id */
	__u16	i_links_count;	/* Links count */
	__u32	i_blocks;	/* Blocks count */
	__u32	i_flags;	/* File flags */
	__u32   i_reserved1;

	__u32	i_block[EXT2_N_BLOCKS];/* Pointers to blocks */
	__u32	i_version;	/* File version (for NFS) */
	__u32	i_file_acl;	/* File ACL */
	__u32	i_dir_acl;	/* Directory ACL */
	__u32	i_faddr;	/* Fragment address */
	__u8	i_frag;		/* Fragment number */
	__u8	i_fsize;	/* Fragment size */
	__u16	i_pad1;
	__u32	i_reserved2[2];
} iNode;

typedef struct ext2_super_block {
	__u32	s_inodes_count;		/* Inodes count */
	__u32	s_blocks_count;		/* Blocks count */
	__u32	s_first_data_block;	/* First Data Block */
	__u32	s_ilog_block_size;	/* log2(Block size) */
	__s32	s_ilog_frag_size;	/* log2(Fragment size) */
	__u32	s_blocks_per_group;	/* # Blocks per group */
	__u32	s_frags_per_group;	/* # Fragments per group */
	__u32	s_inodes_per_group;	/* # Inodes per group */
	__u16	s_magic;		/* Magic signature */
} superblock;

superblock supblock;

struct ext2_dir_entry {
	__u32	inode;			/* Inode number */
	__u16	rec_len;		/* Directory entry length */
	__u8	name_len;		/* name length	*/
	__u8	file_type;		/* file type */
} dir_en;


typedef struct ext2_group_desc
{
	__u32	bg_block_bitmap;		/* Blocks bitmap block */
	__u32	bg_inode_bitmap;		/* Inodes bitmap block */
	__u32	bg_inode_table;		/* Inodes table block */
	__u16	bg_free_blocks_count;	/* Free blocks count */
	__u16	bg_free_inodes_count;	/* Free inodes count */
	__u16	bg_used_dirs_count;	/* Directories count */
	__u16	bg_pad;
	__u32	bg_reserved[3];
} group;

group *groupf;

typedef struct {
	__u32 inodes_count;  /* Inodes count */
	__u32 blocks_count;  /* Blocks count */
	__u32 first_data_block; /* First Data Block */
	__u32 block_size; /* Block size */
	__s32 frag_size; /* Fragment size */
	__u32 blocks_per_group; /* # Blocks per group */
	__u32 frags_per_group; /* # Fragments per group */
	__u32 inodes_per_group; /* # Inodes per group */
	__u32 magic;  /* Magic signature */
} infodata;

infodata ilog;

void pSuper()
{
	superb_fd = fopen("super.csv", "w");

	ssize_t sb = pread(disk_fd, supblock, sizeof(supblock), 1024);

	ilog.magic = supblock->s_magic;

	ilog.blocks_count = supblock->s_blocks_count;

	ilog.inodes_count = supblock->s_inodes_count;

	ilog.block_size = supblock->s_ilog_block_size;

	ilog.frag_size = supblock->s_ilog_frag_size;

	ilog.blocks_per_group = supblock->s_blocks_per_group;

	ilog.inodes_per_group = supblock->s_inodes_per_group;

	ilog.first_data_block = supblock->s_first_data_block;

	FILE *outf = superb_fd;
	fprintf(outf, "SUPERBLOCK,%d,%d,%d,%d,%d,%d,%d,%d\n", ilog.blocks_count, ilog.inodes_count, ilog.block_size, ilog.frag_size, 
		ilog.blocks_per_group, ilog.inodes_per_group, ilog.frags_per_group, ilog.first_data_block);

	fclose(superb_fd);
}

void pBitmap(__u32 bitmap, __u32 per, int gnum, int type) 
{
	bit_fd = fopen("bitmap.csv", "w");
	size_t s = per * gnum;
	__u8 *bitmap = malloc(ilog.block_size);

	ssize_t bp = pread(disk_fd, bitmap, ilog.block_size, bitmap * ilog.block_size);

	FILE *outf = bit_fd;
	for (size_t i = 0, k = 1; i < ilog.block_size; i++) 
	{
		__u8 bit = bitmap[i];
		for (int j = 0; j < 8; j++, k++, bit >>= 1) 
		{
			if(k > per) 
			{
				free(bitmap);
				return;
			}
			if(!(bit & 0x1u)) 
			{
				if(type == 1)
					fprintf(outf, "BFREE,%lu\n", k + s);
				if(type == 2)
					fprintf(outf, "IFREE,%lu\n", k + s);
			}
		}
	}
	fclose(bit_fd);
}

void pGroup()
{
	group_fd = fopen("group.csv", "w");

	int num_groups = supblock->s_blocks_count / supblock->s_blocks_per_group;
	groupf = malloc(num_groups * sizeof(struct group));

	ssize_t gp = pread(disk_fd, groupf, num_groups * sizeof(struct group), (ilog.first_data_block + 1) * ilog.block_size);
	FILE *outf = group_fd;

	int i;
	for (int i = 0; i < num_groups; i++) 
	{
		__u16 free_blocks_count = groupf[i].bg_free_blocks_count;

		__u16 free_inodes_count =  groupf[i].bg_free_inodes_count;
		
		__u16 block_bitmap = groupf[i].bg_block_bitmap;
		
		__u16 inode_bitmap = groupf[i].bg_inode_bitmap;

		__u16 inode_table = groupf[i].bg_inode_table;

		fprintf(outf, "GROUP,%d,%d,%d,%d,%x,%x,%x,%x\n", i, ilog.blocks_per_group, ilog.inodes_per_group,  free_blocks_count, 
			free_inodes_count, block_bitmap, inode_bitmap, inode_table);

		pBitmap(block_bitmap, ilog.blocks_per_group, i, 1);
		pBitmap(inode_bitmap, ilog.inodes_per_group, i, 2);
	}

	close(group_fd);
}


int main(int argc, char** argv)
{
	if(argc != 2)
	{
		fprintf(stderr, "ERROR: invalid argument\nusage: ./lab3a [diskname]\n");
		exit(1);
	}

	char *disk = argv[1];
	disk_fd = open(disk, O_RDONLY);
   
	pSuper();
	pGroup();
    
	close(disk_fd);

	return 0;
}