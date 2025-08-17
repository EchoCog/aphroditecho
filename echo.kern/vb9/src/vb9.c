/* VB9 Runtime Implementation
 * The 1.4MB runtime that makes everything work
 */

#include <u.h>
#include <libc.h>
#include <draw.h>
#include <thread.h>
#include <9p.h>
#include "../include/vb9.h"

/* Global runtime - keep it under 1.4MB! */
static VB9Runtime runtime = {0};
static Image *screen;
static Display *display;

/* Initialize VB9 runtime */
void
vb9_init(void)
{
    display = initdraw(nil, nil, "VB9");
    if(display == nil)
        sysfatal("initdraw failed: %r");
    screen = display->image;
    
    runtime.nforms = 0;
    runtime.totalsize = sizeof(VB9Runtime);
    
    print("VB9 Runtime initialized (size: %d bytes)\n", runtime.totalsize);
}

/* Create a new form - maps to filesystem */
VB9Form*
vb9_createform(char *name)
{
    VB9Form *form;
    char path[VB9_MAX_PATH];
    
    if(runtime.nforms >= VB9_MAX_FORMS) {
        werrstr("too many forms");
        return nil;
    }
    
    form = &runtime.forms[runtime.nforms++];
    snprint(form->name, sizeof(form->name), "%s", name);
    snprint(path, sizeof(path), "/forms/%s", name);
    form->basepath = strdup(path);
    form->ncontrols = 0;
    form->drawfd = -1;
    
    /* Create filesystem structure */
    if(access(path, AEXIST) < 0) {
        if(create(path, OREAD, DMDIR|0755) < 0) {
            werrstr("cannot create form directory: %r");
            return nil;
        }
    }
    
    print("Created form '%s' at %s\n", name, path);
    return form;
}

/* Add control to form - every control is a file */
Control*
vb9_addcontrol(VB9Form *form, int type, char *name, Rectangle rect)
{
    Control *ctrl;
    char path[VB9_MAX_PATH];
    int fd;
    
    if(form->ncontrols >= VB9_MAX_CONTROLS) {
        werrstr("too many controls");
        return nil;
    }
    
    ctrl = &form->controls[form->ncontrols++];
    ctrl->type = type;
    snprint(ctrl->name, sizeof(ctrl->name), "%s", name);
    ctrl->rect = rect;
    ctrl->text = strdup("");
    
    /* Create control directory in filesystem */
    snprint(path, sizeof(path), "%s/%s", form->basepath, name);
    ctrl->filepath = strdup(path);
    
    if(create(path, OREAD, DMDIR|0755) < 0) {
        werrstr("cannot create control directory: %r");
        return nil;
    }
    
    /* Create control files */
    snprint(path, sizeof(path), "%s/%s/text", form->basepath, name);
    fd = create(path, OWRITE, 0644);
    if(fd >= 0) close(fd);
    
    snprint(path, sizeof(path), "%s/%s/geometry", form->basepath, name);
    fd = create(path, OWRITE, 0644);
    if(fd >= 0) {
        fprint(fd, "%d %d %d %d\n", rect.min.x, rect.min.y, rect.max.x, rect.max.y);
        close(fd);
    }
    
    /* Set up drawing and event functions */
    switch(type) {
    case VB9_BUTTON:
        ctrl->draw = vb9_draw_button;
        ctrl->click = vb9_click_button;
        break;
    case VB9_TEXTBOX:
        ctrl->draw = vb9_draw_textbox;
        ctrl->change = vb9_change_textbox;
        break;
    case VB9_LABEL:
        ctrl->draw = vb9_draw_label;
        break;
    case VB9_LISTBOX:
        ctrl->draw = vb9_draw_listbox;
        ctrl->click = vb9_click_listbox;
        break;
    }
    
    print("Added %s control '%s' to form '%s'\n", 
          vb9_typename(type), name, form->name);
    return ctrl;
}

/* Set control text - writes to file */
void
vb9_settext(Control *ctrl, char *text)
{
    char path[VB9_MAX_PATH];
    int fd;
    
    free(ctrl->text);
    ctrl->text = strdup(text);
    
    /* Write to filesystem */
    snprint(path, sizeof(path), "%s/text", ctrl->filepath);
    fd = create(path, OWRITE, 0644);
    if(fd >= 0) {
        write(fd, text, strlen(text));
        close(fd);
    }
}

/* Get control text - reads from file */
char*
vb9_gettext(Control *ctrl)
{
    char path[VB9_MAX_PATH];
    char buf[1024];
    int fd, n;
    
    snprint(path, sizeof(path), "%s/text", ctrl->filepath);
    fd = open(path, OREAD);
    if(fd < 0) return strdup("");
    
    n = read(fd, buf, sizeof(buf)-1);
    close(fd);
    
    if(n > 0) {
        buf[n] = 0;
        free(ctrl->text);
        ctrl->text = strdup(buf);
    }
    
    return ctrl->text;
}

/* The magic: Drawing IS Computing */
void
vb9_render(VB9Form *form)
{
    int i;
    
    if(form->drawfd < 0) {
        form->drawfd = open("/dev/draw/new", ORDWR);
        if(form->drawfd < 0) {
            werrstr("cannot open /dev/draw: %r");
            return;
        }
    }
    
    /* Clear form */
    draw(screen, screen->r, display->white, nil, ZP);
    
    /* Render each control - drawing IS execution */
    for(i = 0; i < form->ncontrols; i++) {
        Control *ctrl = &form->controls[i];
        if(ctrl->draw)
            ctrl->draw(ctrl);
    }
    
    flushimage(display, 1);
    print("Rendered form '%s' with %d controls\n", form->name, form->ncontrols);
}

/* Convert type to string */
char*
vb9_typename(int type)
{
    switch(type) {
    case VB9_BUTTON: return "Button";
    case VB9_TEXTBOX: return "TextBox";
    case VB9_LABEL: return "Label";
    case VB9_LISTBOX: return "ListBox";
    default: return "Unknown";
    }
}

/* Drawing functions for each control type */
void
vb9_draw_button(Control *ctrl)
{
    Rectangle r = ctrl->rect;
    Point p;
    
    /* Draw button border */
    draw(screen, r, display->black, nil, ZP);
    r = insetrect(r, 1);
    draw(screen, r, display->white, nil, ZP);
    
    /* Draw button text */
    p.x = r.min.x + (Dx(r) - stringwidth(font, ctrl->text)) / 2;
    p.y = r.min.y + (Dy(r) - font->height) / 2 + font->ascent;
    string(screen, p, display->black, ZP, font, ctrl->text);
}

void
vb9_draw_textbox(Control *ctrl)
{
    Rectangle r = ctrl->rect;
    Point p;
    
    /* Draw textbox border */
    draw(screen, r, display->black, nil, ZP);
    r = insetrect(r, 1);
    draw(screen, r, display->white, nil, ZP);
    
    /* Draw text */
    p.x = r.min.x + 4;
    p.y = r.min.y + font->ascent + 2;
    string(screen, p, display->black, ZP, font, ctrl->text);
}

void
vb9_draw_label(Control *ctrl)
{
    Point p;
    
    p.x = ctrl->rect.min.x;
    p.y = ctrl->rect.min.y + font->ascent;
    string(screen, p, display->black, ZP, font, ctrl->text);
}

void
vb9_draw_listbox(Control *ctrl)
{
    Rectangle r = ctrl->rect;
    
    /* Draw listbox border */
    draw(screen, r, display->black, nil, ZP);
    r = insetrect(r, 1);
    draw(screen, r, display->white, nil, ZP);
    
    /* TODO: Draw list items */
}

/* Event handlers */
void
vb9_click_button(Control *ctrl)
{
    char path[VB9_MAX_PATH];
    char *cmd;
    
    snprint(path, sizeof(path), "%s/click", ctrl->filepath);
    cmd = readfile(path);
    if(cmd) {
        system(cmd);
        free(cmd);
    }
}

void
vb9_change_textbox(Control *ctrl)
{
    char path[VB9_MAX_PATH];
    char *cmd;
    
    snprint(path, sizeof(path), "%s/change", ctrl->filepath);
    cmd = readfile(path);
    if(cmd) {
        system(cmd);
        free(cmd);
    }
}

void
vb9_click_listbox(Control *ctrl)
{
    /* TODO: Handle listbox selection */
}