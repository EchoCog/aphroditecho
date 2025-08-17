#!/bin/bash
# VB9 Form Export to Plan 9 Service Demo
# This demonstrates how VB9 forms become Plan 9 services

FORM_NAME="Calculator"
FORM_PATH="./forms/$FORM_NAME"

echo "=== VB9 to Plan 9 Service Export ==="
echo "Form: $FORM_NAME"
echo "Path: $FORM_PATH"
echo ""

echo "1. Form Structure (Everything is a File):"
find $FORM_PATH -type f | sort

echo ""
echo "2. Control Text Files:"
for control in Label1 Text1 Button1 Text2; do
    echo "  $control/text: $(cat $FORM_PATH/$control/text)"
done

echo ""
echo "3. Event Handlers (Executable Files):"
find $FORM_PATH -name "click" -o -name "change" -o -name "load" | while read handler; do
    echo "  $handler:"
    echo "    $(head -1 $handler)"
done

echo ""
echo "4. Simulated 9P Service Operations:"
echo "  Read control text:  cat /forms/$FORM_NAME/Text1/text"
echo "  Write control text: echo '123' > /forms/$FORM_NAME/Text1/text"
echo "  Execute event:      /forms/$FORM_NAME/Button1/click"
echo ""

echo "5. Plan 9 Namespace Integration:"
echo "  mount -t 9p /forms/$FORM_NAME /mnt/calculator"
echo "  ls /mnt/calculator/Text1/"
echo "  cat /mnt/calculator/Button1/click"
echo ""

echo "6. Distributed Computing (via drawterm):"
echo "  Each form control becomes a distributed service"
echo "  Button clicks execute on remote CPU servers"
echo "  Text boxes sync across the network namespace"
echo "  Drawing the form IS computing across the cluster"
echo ""

echo "VB9 Principles Demonstrated:"
echo "✓ Drawing = Computing"
echo "✓ Visual = Actual" 
echo "✓ Everything is a File"
echo "✓ Events are Executables"
echo "✓ Forms are Services"
echo "✓ 1.4MB Runtime Target"