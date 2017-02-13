`tix` is a personal task ant notes manager. `tix` is a Shell tool on Linux for storing notes, personal tasks. It has a GUI and a text-based environment.
## installation
```
git clone git://github.com/sinas/tix.git
cd tix/
sudo ./install

# for gui version, run:
tix -g
# OR text mode:
tix
```

optional step:
#edit the file  ~/tix/tix.cfg to change the default editor

some useful keys in tix editor environment:
*  <q> to quit
*  <a> to add a note
*  <ENTER> to edit a note
*  </> to start searching
*  <TAB> list of #hash-tags

The environment shows a list of items, which are tasks or notes.

It is not a text editor! when you select a file, it opens that file in an editor (e.g. Vim)

The words starting with "#" are #tags, beginning of the line.
pressing <tab> will show all #tags.
Special tags:
The notes containing the word "TODO" are group on top of the list to look like unread emails.

The content is saved in folder: `~/tix/`
