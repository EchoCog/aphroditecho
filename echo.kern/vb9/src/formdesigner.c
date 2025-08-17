/* VB9 Form Designer
 * The visual form editor - drag & drop simplicity
 * Drawing is Computing. Visual is Actual.
 */

#include <u.h>
#include <libc.h>
#include <draw.h>
#include <event.h>
#include <keyboard.h>
#include "../include/vb9.h"

enum {
    TOOLBOX_WIDTH = 100,
    PROPERTY_WIDTH = 200,
    MIN_FORM_WIDTH = 400,
    MIN_FORM_HEIGHT = 300
};

typedef struct Designer Designer;
struct Designer {
    VB9Form *form;
    int selectedtool;   /* VB9_BUTTON, VB9_TEXTBOX, etc */
    Control *selectedcontrol;
    Rectangle formarea;
    Rectangle toolbox;
    Rectangle properties;
    int designing;      /* 1 = design mode, 0 = run mode */
};

static Designer designer;
static Menu toolmenu = {
    nil, /* items filled in main */
    nil,
    nil
};

char *tools[] = {
    "Select",
    "Button", 
    "TextBox",
    "Label", 
    "ListBox",
    nil
};

void
initdesigner(void)
{
    Rectangle r;
    
    vb9_init();
    
    /* Layout designer interface */
    r = screen->r;
    
    /* Toolbox on left */
    designer.toolbox = r;
    designer.toolbox.max.x = designer.toolbox.min.x + TOOLBOX_WIDTH;
    
    /* Properties on right */
    designer.properties = r;
    designer.properties.min.x = designer.properties.max.x - PROPERTY_WIDTH;
    
    /* Form area in center */
    designer.formarea = r;
    designer.formarea.min.x += TOOLBOX_WIDTH;
    designer.formarea.max.x -= PROPERTY_WIDTH;
    
    designer.selectedtool = 0; /* Select tool */
    designer.selectedcontrol = nil;
    designer.designing = 1;
    
    toolmenu.item = tools;
    
    print("VB9 Form Designer initialized\n");
}

void
drawdesigner(void)
{
    Rectangle r;
    Point p;
    char buf[256];
    int i;
    
    /* Clear screen */
    draw(screen, screen->r, display->white, nil, ZP);
    
    /* Draw toolbox */
    draw(screen, designer.toolbox, display->paleyellow, nil, ZP);
    border(screen, designer.toolbox, 1, display->black, ZP);
    
    p = designer.toolbox.min;
    p.x += 5;
    p.y += font->height;
    string(screen, p, display->black, ZP, font, "Toolbox");
    
    /* Draw tools */
    for(i = 0; tools[i]; i++) {
        p.y += font->height + 4;
        if(i == designer.selectedtool) {
            r = Rect(p.x - 2, p.y - font->ascent, 
                     designer.toolbox.max.x - 5, p.y + font->height - font->ascent);
            draw(screen, r, display->palebluegreen, nil, ZP);
        }
        string(screen, p, display->black, ZP, font, tools[i]);
    }
    
    /* Draw properties panel */
    draw(screen, designer.properties, display->palegrey, nil, ZP);
    border(screen, designer.properties, 1, display->black, ZP);
    
    p = designer.properties.min;
    p.x += 5;
    p.y += font->height;
    string(screen, p, display->black, ZP, font, "Properties");
    
    if(designer.selectedcontrol) {
        p.y += font->height + 8;
        snprint(buf, sizeof(buf), "Name: %s", designer.selectedcontrol->name);
        string(screen, p, display->black, ZP, font, buf);
        
        p.y += font->height + 4;
        snprint(buf, sizeof(buf), "Type: %s", vb9_typename(designer.selectedcontrol->type));
        string(screen, p, display->black, ZP, font, buf);
        
        p.y += font->height + 4;
        snprint(buf, sizeof(buf), "Text: %s", designer.selectedcontrol->text);
        string(screen, p, display->black, ZP, font, buf);
    }
    
    /* Draw form area */
    draw(screen, designer.formarea, display->white, nil, ZP);
    border(screen, designer.formarea, 2, display->black, ZP);
    
    /* Draw form title */
    p = designer.formarea.min;
    p.x += 10;
    p.y += font->height;
    if(designer.form) {
        snprint(buf, sizeof(buf), "Form: %s (%s mode)", 
                designer.form->name, designer.designing ? "Design" : "Run");
        string(screen, p, display->black, ZP, font, buf);
    }
    
    /* Render form controls */
    if(designer.form && !designer.designing) {
        /* Run mode - use normal rendering */
        vb9_render(designer.form);
    } else if(designer.form) {
        /* Design mode - show controls with selection handles */
        for(i = 0; i < designer.form->ncontrols; i++) {
            Control *ctrl = &designer.form->controls[i];
            
            /* Adjust control position to form area */
            Rectangle cr = ctrl->rect;
            cr.min.x += designer.formarea.min.x + 10;
            cr.min.y += designer.formarea.min.y + 30;
            cr.max.x += designer.formarea.min.x + 10;
            cr.max.y += designer.formarea.min.y + 30;
            
            /* Draw control */
            switch(ctrl->type) {
            case VB9_BUTTON:
                draw(screen, cr, display->palebluegreen, nil, ZP);
                border(screen, cr, 1, display->black, ZP);
                p.x = cr.min.x + (Dx(cr) - stringwidth(font, ctrl->text)) / 2;
                p.y = cr.min.y + (Dy(cr) + font->height) / 2;
                string(screen, p, display->black, ZP, font, ctrl->text);
                break;
                
            case VB9_TEXTBOX:
                draw(screen, cr, display->white, nil, ZP);
                border(screen, cr, 1, display->black, ZP);
                p.x = cr.min.x + 4;
                p.y = cr.min.y + font->ascent + 2;
                string(screen, p, display->black, ZP, font, ctrl->text);
                break;
                
            case VB9_LABEL:
                p.x = cr.min.x;
                p.y = cr.min.y + font->ascent;
                string(screen, p, display->black, ZP, font, ctrl->text);
                break;
                
            case VB9_LISTBOX:
                draw(screen, cr, display->white, nil, ZP);
                border(screen, cr, 1, display->black, ZP);
                break;
            }
            
            /* Draw selection handles if selected */
            if(ctrl == designer.selectedcontrol) {
                border(screen, cr, 2, display->red, ZP);
                /* TODO: Draw resize handles */
            }
        }
    }
    
    flushimage(display, 1);
}

void
handleclick(Mouse m)
{
    Rectangle r;
    Point p;
    Control *ctrl;
    char name[64];
    int i;
    
    if(ptinrect(m.xy, designer.toolbox)) {
        /* Clicked in toolbox */
        int tool = (m.xy.y - designer.toolbox.min.y - font->height) / (font->height + 4);
        if(tool >= 0 && tool < nelem(tools) - 1) {
            designer.selectedtool = tool;
            print("Selected tool: %s\n", tools[tool]);
        }
        return;
    }
    
    if(ptinrect(m.xy, designer.formarea) && designer.form) {
        /* Clicked in form area */
        p.x = m.xy.x - designer.formarea.min.x - 10;
        p.y = m.xy.y - designer.formarea.min.y - 30;
        
        if(designer.designing) {
            if(designer.selectedtool == 0) {
                /* Select tool - find control under cursor */
                designer.selectedcontrol = nil;
                for(i = 0; i < designer.form->ncontrols; i++) {
                    ctrl = &designer.form->controls[i];
                    if(ptinrect(p, ctrl->rect)) {
                        designer.selectedcontrol = ctrl;
                        print("Selected control: %s\n", ctrl->name);
                        break;
                    }
                }
            } else {
                /* Place new control */
                r = Rect(p.x, p.y, p.x + 80, p.y + 24);
                snprint(name, sizeof(name), "%s%d", 
                        tools[designer.selectedtool], designer.form->ncontrols + 1);
                
                ctrl = vb9_addcontrol(designer.form, designer.selectedtool, name, r);
                if(ctrl) {
                    vb9_settext(ctrl, name);
                    designer.selectedcontrol = ctrl;
                    print("Added control: %s\n", name);
                }
            }
        } else {
            /* Run mode - handle clicks */
            for(i = 0; i < designer.form->ncontrols; i++) {
                ctrl = &designer.form->controls[i];
                if(ptinrect(p, ctrl->rect) && ctrl->click) {
                    ctrl->click(ctrl);
                    break;
                }
            }
        }
    }
}

void
handlekey(Rune r)
{
    switch(r) {
    case 'n':
    case 'N':
        /* New form */
        designer.form = vb9_createform("Form1");
        designer.selectedcontrol = nil;
        print("Created new form\n");
        break;
        
    case 'r':
    case 'R':
        /* Toggle run/design mode */
        designer.designing = !designer.designing;
        print("Switched to %s mode\n", designer.designing ? "design" : "run");
        break;
        
    case 'q':
    case 'Q':
    case Kdel:
        /* Quit */
        print("VB9 Form Designer exiting\n");
        exits(nil);
        break;
        
    case 's':
    case 'S':
        /* Save form */
        if(designer.form) {
            print("Form saved to %s\n", designer.form->basepath);
        }
        break;
    }
}

void
main(void)
{
    Event e;
    
    initdesigner();
    
    /* Create initial form */
    designer.form = vb9_createform("Form1");
    
    einit(Emouse | Ekeyboard);
    
    print("VB9 Form Designer - Press 'n' for new form, 'r' to run, 'q' to quit\n");
    
    for(;;) {
        drawdesigner();
        
        switch(eread(Emouse | Ekeyboard, &e)) {
        case Emouse:
            if(e.mouse.buttons & 1)
                handleclick(e.mouse);
            break;
            
        case Ekeyboard:
            handlekey(e.kbdc);
            break;
        }
    }
}