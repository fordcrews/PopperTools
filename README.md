# PopperTools
A few tools for pinup Popper managment.

To use PopperPlayListSqlCreationTool put files on your computer, install python3 in not installed, run pip install flask, then phython lists.py.
Now you should be able to open your browser to  http://localhost:5000/ to access the web interface, build your query, and use "Copy Query to Clipboard" 
button below the query box, to copy the query to paste into popup list creation tool.  Press ctrl-c to end mini server when finished


# OperatorKeyboard

    Button 1 (Keyboard 'End'): GPIO 22
    Button 2 (Keyboard '7'): GPIO 21
    Button 3 (Keyboard '8'): GPIO 17
    Button 4 (Keyboard '9'): GPIO 16
    Button 5 (Keyboard '0'): GPIO 32
    Button 6 (Keyboard '-'): GPIO 25
    Button 7 (Keyboard '='): GPIO 27
    Button 8 (Keyboard 'N'): GPIO 26

# puplookupcsv.py  UPDATES PupLookup.cxv
 
    Requirements:
        Chrome browser installed.
        selenium and beautifulsoup4 libraries installed. Install them using:

    pip install selenium beautifulsoup4

Functionality:

    Backs up the existing puplookup.csv to puplookup.bak, overwriting any existing backup.
    Downloads the CSV from the specified webpage and saves it as puplookup.csv.
