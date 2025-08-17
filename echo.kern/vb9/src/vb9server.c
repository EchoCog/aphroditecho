/* VB9 9P Server
 * Exports VB9 forms as Plan 9 file services
 * Drawing is Computing. Everything is a File.
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

/* Simplified 9P message types for demo */
enum {
    Tversion = 100, Rversion,
    Tauth = 102, Rauth,
    Tattach = 104, Rattach,
    Terror = 106, Rerror,
    Tflush = 108, Rflush,
    Twalk = 110, Rwalk,
    Topen = 112, Ropen,
    Tcreate = 114, Rcreate,
    Tread = 116, Rread,
    Twrite = 118, Rwrite,
    Tclunk = 120, Rclunk,
    Tremove = 122, Rremove,
    Tstat = 124, Rstat,
    Twstat = 126, Rwstat,
};

typedef struct Qid {
    unsigned long long path;
    unsigned long vers;
    unsigned char type;
} Qid;

typedef struct VB9File {
    char *name;
    char *content;
    int length;
    Qid qid;
    int mode;
    struct VB9File *parent;
    struct VB9File *children;
    struct VB9File *sibling;
} VB9File;

/* VB9 9P Filesystem */
static VB9File *vb9_root;
static unsigned long long next_qid = 1;

/* Create a new VB9 file node */
VB9File*
vb9_mkfile(char *name, char *content, int mode)
{
    VB9File *f = calloc(1, sizeof(VB9File));
    f->name = strdup(name);
    f->content = content ? strdup(content) : strdup("");
    f->length = strlen(f->content);
    f->qid.path = next_qid++;
    f->qid.vers = 0;
    f->qid.type = (mode & 0x80000000) ? 0x80 : 0; /* QTDIR or QTFILE */
    f->mode = mode;
    return f;
}

/* Add child to directory */
void
vb9_addchild(VB9File *parent, VB9File *child)
{
    child->parent = parent;
    child->sibling = parent->children;
    parent->children = child;
}

/* Find file by name in directory */
VB9File*
vb9_findfile(VB9File *dir, char *name)
{
    VB9File *f;
    
    if(!dir || !(dir->mode & 0x80000000)) return NULL;
    
    for(f = dir->children; f; f = f->sibling) {
        if(strcmp(f->name, name) == 0)
            return f;
    }
    return NULL;
}

/* Walk path and return file */
VB9File*
vb9_walkpath(char *path)
{
    VB9File *f = vb9_root;
    char *p, *next, *pathcopy;
    
    if(!path || strcmp(path, "/") == 0)
        return vb9_root;
        
    pathcopy = strdup(path + 1); /* skip leading / */
    
    for(p = pathcopy; p && *p; p = next) {
        next = strchr(p, '/');
        if(next) *next++ = 0;
        
        f = vb9_findfile(f, p);
        if(!f) break;
    }
    
    free(pathcopy);
    return f;
}

/* Initialize VB9 filesystem with example form */
void
vb9_initfs(void)
{
    VB9File *forms, *calc, *button1, *text1, *text2;
    
    /* Create root directory */
    vb9_root = vb9_mkfile("/", "", 0x80000000 | 0755);
    
    /* Create /forms directory */
    forms = vb9_mkfile("forms", "", 0x80000000 | 0755);
    vb9_addchild(vb9_root, forms);
    
    /* Create /forms/Calculator directory */
    calc = vb9_mkfile("Calculator", "", 0x80000000 | 0755);
    vb9_addchild(forms, calc);
    
    /* Create Calculator controls */
    button1 = vb9_mkfile("Button1", "", 0x80000000 | 0755);
    vb9_addchild(calc, button1);
    vb9_addchild(button1, vb9_mkfile("text", "Double It!", 0644));
    vb9_addchild(button1, vb9_mkfile("geometry", "10 80 100 105", 0644));
    vb9_addchild(button1, vb9_mkfile("click", "#!/bin/sh\necho 'Button clicked!'", 0755));
    
    text1 = vb9_mkfile("Text1", "", 0x80000000 | 0755);
    vb9_addchild(calc, text1);
    vb9_addchild(text1, vb9_mkfile("text", "0", 0644));
    vb9_addchild(text1, vb9_mkfile("geometry", "10 40 150 65", 0644));
    
    text2 = vb9_mkfile("Text2", "", 0x80000000 | 0755);
    vb9_addchild(calc, text2);
    vb9_addchild(text2, vb9_mkfile("text", "0", 0644));
    vb9_addchild(text2, vb9_mkfile("geometry", "10 120 150 145", 0644));
    
    printf("VB9 9P filesystem initialized\n");
    printf("  /forms/Calculator/Button1/text\n");
    printf("  /forms/Calculator/Button1/click\n");
    printf("  /forms/Calculator/Text1/text\n");
    printf("  /forms/Calculator/Text2/text\n");
}

/* List directory contents */
void
vb9_ls(char *path)
{
    VB9File *dir = vb9_walkpath(path);
    VB9File *f;
    
    if(!dir) {
        printf("ls: %s not found\n", path);
        return;
    }
    
    if(!(dir->mode & 0x80000000)) {
        printf("ls: %s is not a directory\n", path);
        return;
    }
    
    printf("Contents of %s:\n", path);
    for(f = dir->children; f; f = f->sibling) {
        char mode = (f->mode & 0x80000000) ? 'd' : '-';
        printf("  %c%03o %8d %s\n", mode, f->mode & 0777, f->length, f->name);
    }
}

/* Read file contents */
void
vb9_cat(char *path)
{
    VB9File *f = vb9_walkpath(path);
    
    if(!f) {
        printf("cat: %s not found\n", path);
        return;
    }
    
    if(f->mode & 0x80000000) {
        printf("cat: %s is a directory\n", path);
        return;
    }
    
    printf("%s", f->content);
    if(f->length > 0 && f->content[f->length-1] != '\n')
        printf("\n");
}

/* Write to file */
void
vb9_echo(char *text, char *path)
{
    VB9File *f = vb9_walkpath(path);
    
    if(!f) {
        printf("echo: %s not found\n", path);
        return;
    }
    
    if(f->mode & 0x80000000) {
        printf("echo: %s is a directory\n", path);
        return;
    }
    
    free(f->content);
    f->content = strdup(text);
    f->length = strlen(f->content);
    f->qid.vers++;
    
    printf("Wrote '%s' to %s\n", text, path);
}

/* Execute file (for event handlers) */
void
vb9_exec(char *path)
{
    VB9File *f = vb9_walkpath(path);
    
    if(!f) {
        printf("exec: %s not found\n", path);
        return;
    }
    
    if(f->mode & 0x80000000) {
        printf("exec: %s is a directory\n", path);
        return;
    }
    
    if(!(f->mode & 0111)) {
        printf("exec: %s is not executable\n", path);
        return;
    }
    
    printf("Executing %s:\n", path);
    printf("--- Output ---\n");
    
    /* For demo, just show the script content */
    printf("%s\n", f->content);
    
    printf("--- End ---\n");
}

/* VB9 9P Server Demo */
int
main(void)
{
    char cmd[256], arg1[256], arg2[256];
    
    printf("VB9 9P Server - Forms as Plan 9 Services\n");
    printf("Drawing is Computing. Everything is a File.\n\n");
    
    vb9_initfs();
    
    printf("\nVB9 9P Server Commands:\n");
    printf("  ls <path>           - List directory\n");
    printf("  cat <path>          - Read file\n");
    printf("  echo <text> <path>  - Write to file\n");
    printf("  exec <path>         - Execute file\n");
    printf("  quit                - Exit server\n");
    printf("\nExample session:\n");
    printf("  ls /forms/Calculator\n");
    printf("  cat /forms/Calculator/Button1/click\n");
    printf("  echo '42' /forms/Calculator/Text1/text\n");
    printf("  exec /forms/Calculator/Button1/click\n");
    printf("\n> ");
    
    while(fgets(cmd, sizeof(cmd), stdin)) {
        cmd[strcspn(cmd, "\n")] = 0; /* remove newline */
        
        if(strcmp(cmd, "quit") == 0) {
            break;
        } else if(sscanf(cmd, "ls %255s", arg1) == 1) {
            vb9_ls(arg1);
        } else if(sscanf(cmd, "cat %255s", arg1) == 1) {
            vb9_cat(arg1);
        } else if(sscanf(cmd, "echo %255s %255s", arg1, arg2) == 2) {
            vb9_echo(arg1, arg2);
        } else if(sscanf(cmd, "exec %255s", arg1) == 1) {
            vb9_exec(arg1);
        } else if(strlen(cmd) > 0) {
            printf("Unknown command: %s\n", cmd);
        }
        
        printf("> ");
    }
    
    printf("\nVB9 9P Server shutdown\n");
    return 0;
}