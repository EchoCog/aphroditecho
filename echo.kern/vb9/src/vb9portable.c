/* VB9 Portable - Visual Basic for Unix/Linux
 * A demonstration of VB9 concepts without Plan 9 dependencies
 * Still follows the "Drawing is Computing" philosophy
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>

/* Simplified VB9 types for demo */
typedef struct {
    int x, y;
} Point;

typedef struct {
    Point min, max;
} Rectangle;

typedef struct Control Control;
typedef struct VB9Form VB9Form;

enum {
    VB9_BUTTON = 1,
    VB9_TEXTBOX,
    VB9_LABEL,
    VB9_LISTBOX,
    VB9_MAX_CONTROLS = 128
};

struct Control {
    int type;
    char name[64];
    Rectangle rect;
    char *text;
    char *filepath;
    
    void (*draw)(Control*);
    void (*click)(Control*);
};

struct VB9Form {
    char name[64];
    char *basepath;
    int ncontrols;
    Control controls[VB9_MAX_CONTROLS];
};

/* Global runtime */
static VB9Form *current_form = NULL;
static int runtime_size = 0;

/* Create directory recursively */
int
mkdirp(const char *path)
{
    char tmp[256];
    char *p = NULL;
    size_t len;

    snprintf(tmp, sizeof(tmp), "%s", path);
    len = strlen(tmp);
    if(tmp[len - 1] == '/')
        tmp[len - 1] = 0;
    for(p = tmp + 1; *p; p++)
        if(*p == '/') {
            *p = 0;
            mkdir(tmp, 0755);
            *p = '/';
        }
    return mkdir(tmp, 0755);
}

/* VB9 API Implementation */
VB9Form*
vb9_createform(char *name)
{
    static VB9Form forms[16];
    static int nforms = 0;
    
    if(nforms >= 16) return NULL;
    
    VB9Form *form = &forms[nforms++];
    snprintf(form->name, sizeof(form->name), "%s", name);
    
    /* Create filesystem structure */
    char path[256];
    snprintf(path, sizeof(path), "./forms/%s", name);
    form->basepath = strdup(path);
    mkdirp(path);
    
    form->ncontrols = 0;
    current_form = form;
    
    printf("Created VB9 form: %s\n", name);
    return form;
}

Control*
vb9_addcontrol(VB9Form *form, int type, char *name, Rectangle rect)
{
    if(form->ncontrols >= VB9_MAX_CONTROLS) return NULL;
    
    Control *ctrl = &form->controls[form->ncontrols++];
    ctrl->type = type;
    snprintf(ctrl->name, sizeof(ctrl->name), "%s", name);
    ctrl->rect = rect;
    ctrl->text = strdup(name);
    
    /* Create control directory */
    char path[256];
    snprintf(path, sizeof(path), "%s/%s", form->basepath, name);
    ctrl->filepath = strdup(path);
    mkdirp(path);
    
    /* Create control files */
    char filepath[256];
    snprintf(filepath, sizeof(filepath), "%s/text", path);
    FILE *f = fopen(filepath, "w");
    if(f) {
        fprintf(f, "%s", name);
        fclose(f);
    }
    
    snprintf(filepath, sizeof(filepath), "%s/geometry", path);
    f = fopen(filepath, "w");
    if(f) {
        fprintf(f, "%d %d %d %d\n", rect.min.x, rect.min.y, rect.max.x, rect.max.y);
        fclose(f);
    }
    
    printf("Added %s control: %s\n", 
           (type == VB9_BUTTON) ? "Button" :
           (type == VB9_TEXTBOX) ? "TextBox" :
           (type == VB9_LABEL) ? "Label" : "Control", 
           name);
    
    return ctrl;
}

void
vb9_settext(Control *ctrl, char *text)
{
    free(ctrl->text);
    ctrl->text = strdup(text);
    
    /* Write to filesystem */
    char path[256];
    snprintf(path, sizeof(path), "%s/text", ctrl->filepath);
    FILE *f = fopen(path, "w");
    if(f) {
        fprintf(f, "%s", text);
        fclose(f);
    }
}

void
vb9_setevent(Control *ctrl, char *event, char *handler)
{
    char path[256];
    snprintf(path, sizeof(path), "%s/%s", ctrl->filepath, event);
    FILE *f = fopen(path, "w");
    if(f) {
        fprintf(f, "#!/bin/bash\n%s\n", handler);
        fclose(f);
        chmod(path, 0755);
    }
    
    printf("Set %s event for %s: %s\n", event, ctrl->name, handler);
}

void
vb9_render(VB9Form *form)
{
    printf("\n=== VB9 Form: %s ===\n", form->name);
    printf("┌─────────────────────────────────────┐\n");
    
    for(int i = 0; i < form->ncontrols; i++) {
        Control *ctrl = &form->controls[i];
        char *type = (ctrl->type == VB9_BUTTON) ? "Button" :
                     (ctrl->type == VB9_TEXTBOX) ? "TextBox" :
                     (ctrl->type == VB9_LABEL) ? "Label" : "Control";
        
        printf("│ [%s] %-20s %6s │\n", type, ctrl->name, ctrl->text);
    }
    
    printf("└─────────────────────────────────────┘\n");
    printf("Form rendered with %d controls\n", form->ncontrols);
}

void
vb9_show_filesystem(VB9Form *form)
{
    printf("\n=== VB9 Filesystem Structure ===\n");
    char cmd[256];
    snprintf(cmd, sizeof(cmd), "find %s -type f | head -20", form->basepath);
    system(cmd);
}

void
vb9_execute_event(Control *ctrl, char *event)
{
    char path[256];
    snprintf(path, sizeof(path), "%s/%s", ctrl->filepath, event);
    
    if(access(path, X_OK) == 0) {
        printf("Executing %s event for %s...\n", event, ctrl->name);
        system(path);
    } else {
        printf("No %s handler for %s\n", event, ctrl->name);
    }
}

void
vb9_runtime_info(void)
{
    printf("\n=== VB9 Runtime Information ===\n");
    printf("Target runtime size: 1.4MB (like VB6)\n");
    printf("Current estimated size: %d bytes\n", runtime_size);
    printf("Forms directory: ./forms/\n");
    printf("Drawing is Computing: ✓\n");
    printf("Everything is a File: ✓\n");
    printf("Visual = Actual: ✓\n");
}

/* Demo program */
int
main(void)
{
    printf("VB9 - Visual Basic for Plan 9 (Portable Demo)\n");
    printf("Drawing is Computing. Rendering is Execution.\n\n");
    
    /* Create the classic VB6 calculator */
    VB9Form *form = vb9_createform("Calculator");
    
    Rectangle r;
    Control *label1, *text1, *button1, *text2;
    
    /* Add label */
    r = (Rectangle){{10, 10}, {120, 30}};
    label1 = vb9_addcontrol(form, VB9_LABEL, "Label1", r);
    vb9_settext(label1, "Enter number:");
    
    /* Add input textbox */
    r = (Rectangle){{10, 40}, {150, 65}};
    text1 = vb9_addcontrol(form, VB9_TEXTBOX, "Text1", r);
    vb9_settext(text1, "0");
    
    /* Add button - the VB6 magic! */
    r = (Rectangle){{10, 80}, {100, 105}};
    button1 = vb9_addcontrol(form, VB9_BUTTON, "Button1", r);
    vb9_settext(button1, "Double It!");
    
    /* Add result textbox */
    r = (Rectangle){{10, 120}, {150, 145}};
    text2 = vb9_addcontrol(form, VB9_TEXTBOX, "Text2", r);
    vb9_settext(text2, "0");
    
    /* The VB6 equivalent: Text2.Text = Val(Text1.Text) * 2 */
    char handler[256];
    snprintf(handler, sizeof(handler), 
             "input=$(cat %s/text)\n"
             "result=$(echo \"$input * 2\" | bc 2>/dev/null || echo 0)\n"
             "echo \"$result\" > %s/text\n"
             "echo \"Calculated: $input * 2 = $result\"",
             text1->filepath, text2->filepath);
    
    vb9_setevent(button1, "click", handler);
    
    /* Show the form */
    vb9_render(form);
    
    /* Show filesystem structure */
    vb9_show_filesystem(form);
    
    /* Test the button click */
    printf("\n=== Testing Button Click ===\n");
    vb9_execute_event(button1, "click");
    
    /* Show runtime info */
    vb9_runtime_info();
    
    printf("\nVB9 Demo complete! The future is simpler than the past.\n");
    return 0;
}