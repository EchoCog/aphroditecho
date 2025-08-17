/* VB9 Demo - Hello World the VB6 way
 * Recreating the legendary 30-second calculator
 */

#include <u.h>
#include <libc.h>
#include <draw.h>
#include <event.h>
#include "../include/vb9.h"

VB9Form *form;
Control *text1, *text2, *button1, *label1;

void
setup_form(void)
{
    Rectangle r;
    
    /* Create the form */
    form = vb9_createform("Calculator");
    if(!form) sysfatal("cannot create form: %r");
    
    /* Add Label1 */
    r = Rect(10, 10, 100, 30);
    label1 = vb9_addcontrol(form, VB9_LABEL, "Label1", r);
    vb9_settext(label1, "Enter number:");
    
    /* Add Text1 - input */
    r = Rect(10, 40, 150, 65);
    text1 = vb9_addcontrol(form, VB9_TEXTBOX, "Text1", r);
    vb9_settext(text1, "0");
    
    /* Add Button1 - the magic happens here */
    r = Rect(10, 80, 100, 105);
    button1 = vb9_addcontrol(form, VB9_BUTTON, "Button1", r);
    vb9_settext(button1, "Double It!");
    
    /* Add Text2 - result */
    r = Rect(10, 120, 150, 145);
    text2 = vb9_addcontrol(form, VB9_TEXTBOX, "Text2", r);
    vb9_settext(text2, "0");
    
    print("VB9 Calculator form created!\n");
}

/* The VB6 magic: Private Sub Command1_Click() */
void
button1_click(void)
{
    char *input, result[64];
    double val;
    
    /* VB6: Val(Text1.Text) * 2 */
    input = vb9_gettext(text1);
    val = strtod(input, nil) * 2;
    snprint(result, sizeof(result), "%.0f", val);
    
    /* VB6: Text2.Text = result */
    vb9_settext(text2, result);
    
    print("Calculated: %s * 2 = %s\n", input, result);
}

void
setup_events(void)
{
    char path[256], *handler;
    int fd;
    
    /* Create click handler file - this IS the VB6 code! */
    snprint(path, sizeof(path), "%s/click", button1->filepath);
    fd = create(path, OWRITE, 0755);
    if(fd >= 0) {
        handler = "#!/bin/rc\n"
                  "# VB6 equivalent: Text2.Text = Val(Text1.Text) * 2\n"
                  "input=`{cat /forms/Calculator/Text1/text}\n"
                  "result=`{echo $input '*' 2 | bc}\n"
                  "echo $result > /forms/Calculator/Text2/text\n";
        write(fd, handler, strlen(handler));
        close(fd);
    }
    
    /* Override with direct function for demo */
    button1->click = button1_click;
    
    print("Event handlers configured\n");
}

void
run_form(void)
{
    Event e;
    Mouse m;
    
    einit(Emouse | Ekeyboard);
    
    print("VB9 Calculator running - Click 'Double It!' button\n");
    print("Press 'q' to quit\n");
    
    for(;;) {
        vb9_render(form);
        
        switch(eread(Emouse | Ekeyboard, &e)) {
        case Emouse:
            m = e.mouse;
            if(m.buttons & 1) {
                /* Check if clicked on button */
                Point p = m.xy;
                if(ptinrect(p, button1->rect)) {
                    button1_click();
                }
            }
            break;
            
        case Ekeyboard:
            if(e.kbdc == 'q' || e.kbdc == 'Q')
                exits(nil);
            break;
        }
    }
}

void
main(void)
{
    print("VB9 Demo - The 30 Second Calculator\n");
    print("Recreating VB6 magic on Plan 9\n\n");
    
    /* Initialize VB9 runtime */
    vb9_init();
    
    /* Create the form - just like VB6 */
    setup_form();
    
    /* Set up events - the VB6 way */
    setup_events();
    
    /* Show the form and run */
    run_form();
}