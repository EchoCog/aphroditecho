/* VB9 - Visual Basic for Plan 9
 * Core type definitions and architecture
 * Drawing is Computing. Rendering is Execution.
 */

#pragma src "/home/runner/work/echo.kern/echo.kern/vb9"
#pragma lib "libvb9.a"

typedef struct Rectangle Rectangle;
typedef struct Point Point;
typedef struct Control Control;
typedef struct VB9Form VB9Form;
typedef struct VB9Event VB9Event;

struct Point {
    int x;
    int y;
};

struct Rectangle {
    Point min;
    Point max;
};

/* Control Types - The VB6 Essentials */
enum {
    VB9_BUTTON = 1,
    VB9_TEXTBOX,
    VB9_LABEL,
    VB9_LISTBOX,
    VB9_MAX_CONTROLS = 128  /* Like ttffs glyphs! */
};

/* Events map directly to file operations */
struct VB9Event {
    char *name;              /* "click", "change", "load" */
    char *handler;           /* path to handler file */
    int (*execute)(Control*); /* direct execution function */
};

/* Every control is a file in the namespace */
struct Control {
    int type;                /* VB9_BUTTON, VB9_TEXTBOX, etc */
    char name[64];           /* maps to /forms/{form}/{name} */
    Rectangle rect;          /* position IS memory address */
    char *text;              /* current display text */
    char *filepath;          /* /forms/{form}/{name} */
    VB9Event events[8];      /* max 8 events per control */
    
    /* Drawing IS execution */
    void (*draw)(Control*);   /* render to /dev/draw */
    void (*click)(Control*);  /* handle click event */
    void (*change)(Control*); /* handle change event */
};

/* A form is a Plan 9 service */
struct VB9Form {
    char name[64];           /* form name */
    char *basepath;          /* /forms/{name} */
    int drawfd;              /* /dev/draw file descriptor */
    int ncontrols;           /* number of controls */
    Control controls[VB9_MAX_CONTROLS];
    
    /* Form lifecycle */
    void (*load)(VB9Form*);
    void (*unload)(VB9Form*);
    void (*refresh)(VB9Form*);
};

/* The 1.4MB runtime */
struct VB9Runtime {
    VB9Form *forms;
    int nforms;
    int totalsize;           /* must be ≤ 1.4MB */
};

/* Core API - VB6 simplicity */
VB9Form* vb9_createform(char *name);
Control* vb9_addcontrol(VB9Form *form, int type, char *name, Rectangle rect);
void vb9_settext(Control *ctrl, char *text);
char* vb9_gettext(Control *ctrl);
void vb9_setevent(Control *ctrl, char *event, char *handler);
void vb9_show(VB9Form *form);
void vb9_compile(VB9Form *form, char *output);

/* Drawing = Computing */
void vb9_render(VB9Form *form);     /* render form to /dev/draw */
void vb9_execute(VB9Form *form);    /* execute form as service */

/* The magic: Everything maps to files */
void vb9_exportfs(VB9Form *form);   /* export form as 9P service */
void vb9_importfs(char *path);      /* import form from filesystem */

/* Drawing functions for controls */
void vb9_draw_button(Control *ctrl);
void vb9_draw_textbox(Control *ctrl);
void vb9_draw_label(Control *ctrl);
void vb9_draw_listbox(Control *ctrl);

/* Event handlers */
void vb9_click_button(Control *ctrl);
void vb9_change_textbox(Control *ctrl);
void vb9_click_listbox(Control *ctrl);

/* Utility functions */
char* readfile(char *path);
char* vb9_typename(int type);

/* Runtime limits - VB6 compatibility */
enum {
    VB9_MAX_FORMS = 16,
    VB9_MAX_FILESIZE = 1400000,  /* 1.4MB like VB6 runtime */
    VB9_MAX_PATH = 256
};