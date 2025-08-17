/* VB9 Utility Functions
 * Helper functions for VB9 runtime
 */

#include <u.h>
#include <libc.h>
#include "../include/vb9.h"

/* Read entire file into string */
char*
readfile(char *path)
{
    int fd, n;
    char *buf;
    Dir *d;
    
    fd = open(path, OREAD);
    if(fd < 0)
        return nil;
        
    d = dirfstat(fd);
    if(d == nil) {
        close(fd);
        return nil;
    }
    
    buf = malloc(d->length + 1);
    if(buf == nil) {
        free(d);
        close(fd);
        return nil;
    }
    
    n = read(fd, buf, d->length);
    buf[n] = 0;
    
    free(d);
    close(fd);
    
    return buf;
}

/* Set event handler for control */
void
vb9_setevent(Control *ctrl, char *event, char *handler)
{
    char path[VB9_MAX_PATH];
    int fd;
    
    snprint(path, sizeof(path), "%s/%s", ctrl->filepath, event);
    fd = create(path, OWRITE, 0755);
    if(fd >= 0) {
        if(strncmp(handler, "#!/", 3) != 0) {
            write(fd, "#!/bin/rc\n", 10);
        }
        write(fd, handler, strlen(handler));
        if(handler[strlen(handler)-1] != '\n') {
            write(fd, "\n", 1);
        }
        close(fd);
    }
    
    print("Set %s event for %s: %s\n", event, ctrl->name, handler);
}

/* Show form (stub for now) */
void
vb9_show(VB9Form *form)
{
    print("Showing form: %s\n", form->name);
    vb9_render(form);
}

/* Compile form to executable */
void
vb9_compile(VB9Form *form, char *output)
{
    char cmd[1024];
    
    /* For now, just copy the form structure */
    snprint(cmd, sizeof(cmd), 
            "echo 'VB9 compiled form: %s' > %s && chmod +x %s", 
            form->name, output, output);
    
    if(system(cmd) == 0) {
        print("Compiled form %s to %s\n", form->name, output);
    } else {
        print("Failed to compile form %s\n", form->name);
    }
}

/* Export form as 9P service */
void
vb9_exportfs(VB9Form *form)
{
    /* TODO: Implement 9P server for form */
    print("Exporting form %s as 9P service\n", form->name);
}

/* Import form from filesystem */
void
vb9_importfs(char *path)
{
    /* TODO: Import form from 9P namespace */
    print("Importing form from %s\n", path);
}