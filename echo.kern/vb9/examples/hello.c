/* Hello World - The VB6 Classic
 * One button, one message box, pure simplicity
 */

#include <u.h>
#include <libc.h>
#include "../include/vb9.h"

void
main(void)
{
    VB9Form *form;
    Control *button;
    Rectangle r;
    
    vb9_init();
    
    /* Create form */
    form = vb9_createform("HelloWorld");
    
    /* Add button */
    r = Rect(50, 50, 150, 80);
    button = vb9_addcontrol(form, VB9_BUTTON, "SayHello", r);
    vb9_settext(button, "Say Hello");
    
    /* The VB6 magic: MsgBox "Hello World!" */
    vb9_setevent(button, "click", "echo 'Hello World!' > /dev/cons");
    
    print("Hello World form created at %s\n", form->basepath);
    print("Click handler: echo 'Hello World!' > /dev/cons\n");
}